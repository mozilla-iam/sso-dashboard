"""SSO Dashboard App File."""

import json
import logging
import logging.config
import mimetypes
import os
import redis
import traceback
import yaml

from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import session
from flask import url_for
from flask.sessions import SessionInterface

from flask_assets import Bundle  # type: ignore
from flask_assets import Environment  # type: ignore
from flask_session.redis import RedisSessionInterface  # type: ignore
from flask_talisman import Talisman  # type: ignore

from dashboard import oidc_auth
from dashboard import config
from dashboard import vanity

from dashboard.csp import DASHBOARD_CSP
from dashboard.models.user import User
from dashboard.models.user import FakeUser
from dashboard.op.yaml_loader import Application
from dashboard.models.tile import CDNTransfer


logging.config.fileConfig("dashboard/logging.ini")

app_config = config.Default()

if app_config.DEBUG:
    # Set the log level to DEBUG for all defined loggers
    for logger_name in logging.root.manager.loggerDict.keys():
        logging.getLogger(logger_name).setLevel("DEBUG")

app = Flask(__name__)
app.config.from_object(app_config)

talisman = Talisman(app, content_security_policy=DASHBOARD_CSP, force_https=False)

app_list = CDNTransfer(app_config)


def session_configure(app: Flask) -> SessionInterface:
    """
    We should try doing what our dependencies prefer, falling back to what we
    want to do only as a last resort. That is to say, try using a connection
    string _first_, then do our logic.

    This function will either return a _verified_ connection or raise an
    exception (failing fast).

    Considerations for the future:
    * Auth
    """
    try:
        client = redis.Redis.from_url(app.config["REDIS_CONNECTOR"])
    except ValueError:
        host, _, port = app.config["REDIS_CONNECTOR"].partition(":")
        client = redis.Redis(host=host, port=int(port))
    # [redis.Redis.ping] will raise an exception if it can't connect anyways,
    # but at least this way we make use of it's return value. Feels weird to
    # not?
    #
    # redis.Redis.ping: https://github.com/redis/redis-py/blob/00f5be420b397adfa1b9aa9c2761f7d8a27c0a9a/redis/commands/core.py#L1206
    assert client.ping(), "Could not ping Redis"
    return RedisSessionInterface(app, client=client)


app.session_interface = session_configure(app)

assets = Environment(app)
js = Bundle("js/base.js", filters="jsmin", output="js/gen/packed.js")
assets.register("js_all", js)

sass = Bundle("css/base.scss", filters="scss")
css = Bundle(sass, filters="cssmin", output="css/gen/all.css")
assets.register("css_all", css)

# Hack to support serving .svg
mimetypes.add_type("image/svg+xml", ".svg")

oidc_config = config.OIDC()
authentication = oidc_auth.OpenIDConnect(oidc_config)
oidc = authentication.get_oidc(app)

vanity_router = vanity.Router(app, app_list).setup()


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static/img"), "favicon.ico")


@app.route("/")
def home():
    if app.config["ENVIRONMENT"] == "local":
        return redirect("dashboard", code=302)

    url = request.url.replace("http://", "https://", 1)
    return redirect(url + "dashboard", code=302)


@app.route("/csp_report", methods=["POST"])
def csp_report():
    return "200"


@app.route("/version", methods=["GET"])
def get_version():
    with open("/version.json", "r") as version:
        v = version.read().replace("\n", "")
    return jsonify(build_version=v)


# XXX This needs to load the schema from a better location
# See also https://github.com/mozilla/iam-project-backlog/issues/161
@app.route("/claim")
def claim():
    """Show the user schema - this path is refered to by
    our OIDC Claim namespace, i.e.: https://sso.mozilla.com/claim/*"""
    return redirect("https://github.com/mozilla-iam/cis/blob/master/cis/schema.json", code=302)


# Flask Error Handlers
@app.errorhandler(404)
def page_not_found(error):
    if request.url is not None:
        app.logger.error("A 404 has been generated for {route}".format(route=request.url))
    return render_template("404.html"), 404


@app.errorhandler(Exception)
def handle_exception(e):

    # Capture the traceback
    tb_str = traceback.format_exc()

    # Log the error with traceback
    app.logger.error("An error occurred: %s\n%s", str(e), tb_str)

    response = {"error": "An internal error occurred", "message": str(e)}
    return jsonify(response), 500


@app.route("/forbidden")
def forbidden():
    """Route to render error page."""
    if "error" not in request.args:
        return render_template("forbidden.html"), 500
    try:
        tv = oidc_auth.TokenVerification(
            jws=request.args.get("error").encode(),
            public_key=app.config["FORBIDDEN_PAGE_PUBLIC_KEY"],
        )
    except oidc_auth.TokenError:
        app.logger.exception("Could not validate JWS from IdP")
        return render_template("forbidden.html"), 500
    app.logger.warning(
        f"{tv.error_code} for {tv.client} (connection: {tv.connection}, preferred connection: {tv.preferred_connection_name})"
    )
    return render_template("forbidden.html", message=tv.error_message()), 400


@app.route("/logout")
@oidc.oidc_logout
def logout():
    """
    Uses the RP-Initiated Logout End Session Endpoint [0] if the app was
    started up with knowledge of it. Flask-pyoidc will make use of this
    endpoint if it's in the provider metadata [1].

    If the app was _not_ started with the End Session Endpoint, then we'll
    fallback to using the `v2/logout` [2] endpoint.

    These two methods cover all cases where:

    * the tenant does not have the End Session Endpoint turned on/off;
    * the Universal Login page has/has not been customized.

    Note: As the Auth0 docs state [3], this _does not_ log users out of all
    applications. This simply ends their session with Auth0 and clears their
    SSO Dashboard session. Refer to the docs on what we'd need to do to achieve
    a global logout.

    [0]: https://auth0.com/docs/authenticate/login/logout/log-users-out-of-auth0#example
    [1]: https://github.com/zamzterz/Flask-pyoidc/blob/26b123572cba0b3fa84482c6c0270900042a73c9/src/flask_pyoidc/flask_pyoidc.py#L263
    [2]: https://auth0.com/docs/api/authentication#auth0-logout
    [3]: https://manage.mozilla-dev.auth0.com/docs/authenticate/login/logout/log-users-out-of-applications
    """
    try:
        has_provider_endpoint = oidc.clients["default"].provider_end_session_endpoint is not None
    except (AttributeError, KeyError):
        has_provider_endpoint = False
    if has_provider_endpoint:
        app.logger.info("Used provider_end_session_endpoint for logout")
        return render_template("signout.html")
    # Old-school redirect. If we get here this means we haven't enabled the
    # RP-initiated logout end session endpoint on Auth0, and so we need to do
    # manual logout (in a non-breaking way).
    app.logger.info("Redirecting to v2/logout")
    # Build up the logout and signout URLs
    signout_url = f"{app.config["PREFERRED_URL_SCHEME"]}://{app.config["SERVER_NAME"]}{url_for("signout")}"
    logout_url = (
        f"https://{oidc_config.OIDC_DOMAIN}/v2/logout?client_id={oidc_config.OIDC_CLIENT_ID}&returnTo={signout_url}"
    )
    return redirect(logout_url, code=302)


@app.route("/autologin-settings")
def showautologinsettings():
    """
    Redirect to NLX Auto-login Settings page
    """
    autologin_settings_url = "https://{}/login?client={}&action=autologin_settings".format(
        oidc_config.OIDC_DOMAIN, oidc_config.OIDC_CLIENT_ID
    )
    return redirect(autologin_settings_url, code=302)


@app.route("/signout.html")
def signout():
    app.logger.info("Signout messaging displayed.")
    return render_template("signout.html")


@app.route("/dashboard")
@oidc.oidc_auth("default")
def dashboard():
    """Primary dashboard the users will interact with."""
    app.logger.info("User: {} authenticated proceeding to dashboard.".format(session.get("id_token")["sub"]))

    # TODO: Refactor rules later to support full id_conformant session
    session["userinfo"]["user_id"] = session.get("id_token")["sub"]

    # This checks the CDN for any updates to apps.yml
    # If an update is found, all gunicorn workers will be reloaded
    app_list.sync_config()

    user = User(session, app.config)
    apps = user.apps(Application(app_list.apps_yml).apps)

    return render_template("dashboard.html", config=app.config, user=user, apps=apps)


@app.route("/styleguide/dashboard")
def styleguide_dashboard():
    user = FakeUser(app.config)
    apps = user.apps(Application(app_list.apps_yml).apps)

    return render_template("dashboard.html", config=app.config, user=user, apps=apps)


@app.route("/styleguide/notifications")
@oidc.oidc_auth("default")
def styleguide_notifications():
    user = FakeUser(app.config)
    return render_template("notifications.html", config=app.config, user=user)


"""useful endpoint for debugging"""


@app.route("/info")
@oidc.oidc_auth("default")
def info():
    """Return the JSONified user session for debugging."""
    return jsonify(
        id_token=session.get("id_token"),
        userinfo=session.get("userinfo"),
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contribute.json")
def contribute_lower():
    data = {
        "name": "sso-dashboard by Mozilla",
        "description": "A single signon dashboard for auth0.",
        "repository": {
            "url": "https://github.com/mozilla-iam/sso-dashboard",
            "license": "MPL2",
        },
        "participate": {
            "home": "https://github.com/mozilla-iam/sso-dashboard",
            "irc": "irc://irc.mozilla.org/#infosec",
            "irc-contacts": ["Andrew"],
        },
        "bugs": {
            "list": "https://github.com/mozilla-iam/sso-dashboard/issues",
            "report": "https://github.com/mozilla-iam/sso-dashboard/issues/new",
            "mentored": "https://github.com/mozilla-iam/sso-dashboard/issues?q=is%3Aissue+is%3Aclosed",  # noqa
        },
        "urls": {
            "prod": "https://sso.mozilla.com/",
            "stage": "https://sso.allizom.org/",
        },
        "keywords": ["python", "html5", "jquery", "mui-css", "sso", "auth0"],
    }

    return jsonify(data)


if __name__ == "__main__":
    app.run()
