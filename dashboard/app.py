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

from flask_assets import Bundle  # type: ignore
from flask_assets import Environment  # type: ignore
from flask_kvsession import KVSessionExtension  # type: ignore
from flask_talisman import Talisman  # type: ignore

from simplekv.memory.redisstore import RedisStore  # type: ignore
from simplekv.decorator import PrefixDecorator  # type: ignore

from dashboard import oidc_auth
from dashboard import config
from dashboard import get_config
from dashboard import vanity

from dashboard.api import idp
from dashboard.api import exceptions
from dashboard.csp import DASHBOARD_CSP
from dashboard.models.user import User
from dashboard.models.user import FakeUser
from dashboard.op.yaml_loader import Application
from dashboard.models.tile import CDNTransfer


logging.config.fileConfig("dashboard/logging.ini")

if config.Config(None).settings.DEBUG:
    # Set the log level to DEBUG for all defined loggers
    for logger_name in logging.root.manager.loggerDict.keys():
        logging.getLogger(logger_name).setLevel("DEBUG")

app = Flask(__name__)

talisman = Talisman(app, content_security_policy=DASHBOARD_CSP, force_https=False)

app.config.from_object(config.Config(app).settings)

app_list = CDNTransfer(config.Config(app).settings)

# Activate server-side redis sesssion KV
redis_host, redis_port = app.config["REDIS_CONNECTOR"].split(":")
store = RedisStore(redis.StrictRedis(host=redis_host, port=redis_port))
prefixed_store = PrefixDecorator(app.config["SERVER_NAME"] + "_", store)
KVSessionExtension(store, app)

assets = Environment(app)
js = Bundle("js/base.js", filters="jsmin", output="js/gen/packed.js")
assets.register("js_all", js)

sass = Bundle("css/base.scss", filters="scss")
css = Bundle(sass, filters="cssmin", output="css/gen/all.css")
assets.register("css_all", css)

# Hack to support serving .svg
mimetypes.add_type("image/svg+xml", ".svg")

oidc_config = config.OIDCConfig()
authentication = oidc_auth.OpenIDConnect(oidc_config)
oidc = authentication.get_oidc(app)

vanity_router = vanity.Router(app, app_list).setup()

api = idp.AuthorizeAPI(app, oidc_config)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static/img"), "favicon.ico")


@app.route("/")
def home():
    if config.Config(app).environment == "local":
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
    Redirect to new feature in NLX that destroys autologin preferences.
    Aka Logout is REALLY logout.
    """
    logout_url = "https://{}/login?client={}&action=logout".format(oidc_config.OIDC_DOMAIN, oidc_config.OIDC_CLIENT_ID)
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

    user = User(session, config.Config(app).settings)
    apps = user.apps(Application(app_list.apps_yml).apps)

    return render_template("dashboard.html", config=app.config, user=user, apps=apps)


@app.route("/styleguide/dashboard")
def styleguide_dashboard():
    user = FakeUser(config.Config(app).settings)
    apps = user.apps(Application(app_list.apps_yml).apps)

    return render_template("dashboard.html", config=app.config, user=user, apps=apps)


@app.route("/styleguide/notifications")
@oidc.oidc_auth("default")
def styleguide_notifications():
    user = FakeUser(config.Config(app).settings)
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
