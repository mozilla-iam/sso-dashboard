"""SSO Dashboard App File."""
import json
import logging.config
import mimetypes
import os
import yaml

from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import session

from flask_assets import Bundle
from flask_assets import Environment
from flask_talisman import Talisman

from dashboard import oidc_auth
from dashboard import config
from dashboard import get_config
from dashboard import person
from dashboard import vanity

from dashboard.api import idp
from dashboard.api import exceptions
from dashboard.csp import DASHBOARD_CSP
from dashboard.models.user import User
from dashboard.models.user import FakeUser
from dashboard.op.yaml_loader import Application
from dashboard.models.alert import Alert
from dashboard.models.alert import FakeAlert
from dashboard.models.alert import Rules
from dashboard.models.tile import S3Transfer


logging.basicConfig(level=logging.DEBUG)

with open("dashboard/logging.yml", "r") as log_config:
    config_yml = log_config.read()
    config_dict = yaml.safe_load(config_yml)
    logging.config.dictConfig(config_dict)

logger = logging.getLogger("sso-dashboard")

app = Flask(__name__)
everett_config = get_config()

talisman = Talisman(app, content_security_policy=DASHBOARD_CSP, force_https=False)

app.config.from_object(config.Config(app).settings)
app_list = S3Transfer(config.Config(app).settings)
app_list.sync_config()

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
person_api = person.API()

vanity_router = vanity.Router(app, app_list).setup()

api = idp.AuthorizeAPI(app, oidc_config)

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static/img"), "favicon.ico")

@app.route("/")
def home():
    if app.env == "development":
        return redirect("dashboard", code=302)

    url = request.url.replace("http://", "https://", 1)
    return redirect(url + "dashboard", code=302)

@app.route("/csp_report", methods=["POST"])
def csp_report():
    return "200"


# XXX This needs to load the schema from a better location
# See also https://github.com/mozilla/iam-project-backlog/issues/161
@app.route("/claim")
def claim():
    """Show the user schema - this path is refered to by
    our OIDC Claim namespace, i.e.: https://sso.mozilla.com/claim/*"""
    return redirect(
        "https://github.com/mozilla-iam/cis/blob/master/cis/schema.json", code=302
    )


@app.errorhandler(404)
def page_not_found(error):
    if request.url is not None:
        logger.error("A 404 has been generated for {route}".format(route=request.url))
    return render_template("404.html"), 404


@app.route("/forbidden")
def forbidden():
    """Route to render error page."""

    if "error" not in request.args:
        return render_template("forbidden.html")
    else:
        jws = request.args.get("error").encode()

    token_verifier = oidc_auth.tokenVerification(
        jws=jws, public_key=app.config["FORBIDDEN_PAGE_PUBLIC_KEY"]
    )
    token_verifier.verify

    return render_template("forbidden.html", token_verifier=token_verifier)


@app.route("/logout")
@oidc.oidc_logout
def logout():
    """
    Redirect to new feature in NLX that destroys autologin preferences.
    Aka Logout is REALLY logout.
    """
    logout_url = "https://{}/login?client={}&action=logout".format(
        oidc_config.OIDC_DOMAIN, oidc_config.OIDC_CLIENT_ID
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
    logger.info("Signout messaging displayed.")
    return render_template("signout.html")


@app.route("/dashboard")
@oidc.oidc_auth('default')
def dashboard():
    """Primary dashboard the users will interact with."""
    logger.info(
        "User: {} authenticated proceeding to dashboard.".format(
            session.get("id_token")["sub"]
        )
    )

    if "Mozilla-LDAP" in session.get("userinfo")["sub"]:
        logger.info("Mozilla IAM user detected. Attempt enriching with ID-Vault data.")
        try:
            session["idvault_userinfo"] = person_api.get_userinfo(
                session.get("id_token")["sub"]
            )
        except Exception as e:
            logger.error(
                "Could not enrich profile due to: {}.  Perhaps it doesn't exist?".format(
                    e
                )
            )

    # Hotfix to set user id for firefox alert
    # XXXTBD Refactor rules later to support full id_conformant session
    session["userinfo"]["user_id"] = session.get("id_token")["sub"]

    # Transfer any updates in to the app_tiles.
    S3Transfer(config.Config(app).settings).sync_config()

    # Send the user session and browser headers to the alert rules engine.
    Rules(userinfo=session["userinfo"], request=request).run()

    user = User(session, config.Config(app).settings)
    apps = user.apps(Application(app_list.apps_yml).apps)

    return render_template(
        "dashboard.html", config=app.config, user=user, apps=apps, alerts=None
    )


@app.route("/styleguide/dashboard")
def styleguide_dashboard():
    user = FakeUser(config.Config(app).settings)
    apps = user.apps(Application(app_list.apps_yml).apps)

    return render_template(
        "dashboard.html", config=app.config, user=user, apps=apps, alerts=None
    )


@app.route("/styleguide/notifications")
@oidc.oidc_auth('default')
def styleguide_notifications():
    user = FakeUser(config.Config(app).settings)
    return render_template("notifications.html", config=app.config, user=user)


@app.route("/notifications")
@oidc.oidc_auth('default')
def notifications():
    user = User(session, config.Config(app).settings)
    return render_template("notifications.html", config=app.config, user=user)


@oidc.oidc_auth('default')
@app.route("/alert/<alert_id>", methods=["POST"])
def alert_operation(alert_id):
    if request.method == "POST":
        user = User(session, config.Config(app).settings)
        if request.data is not None:
            data = json.loads(request.data.decode())
            helpfulness = data.get("helpfulness")
            alert_action = data.get("alert_action")

        result = user.take_alert_action(alert_id, alert_action, helpfulness)

        if result["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return "200"
        else:
            return "500"


@oidc.oidc_auth('default')
@app.route("/alert/fake", methods=["GET"])
def alert_faking():
    if request.method == "GET":
        if app.config.get("SERVER_NAME") != "sso.mozilla.com":
            """Only allow alert faking in non production environment."""
            user = User(session, config.Config(app).settings)
            fake_alerts = FakeAlert(user_id=user.userinfo.get("sub"))
            fake_alerts.create_fake_alerts()

    return redirect("/dashboard", code=302)


@app.route("/api/v1/alert", methods=["GET"])
@api.requires_api_auth
def alert_api():
    if request.method == "GET" and api.requires_scope("read:alert"):
        user_id = request.args.get("user_id")
        alerts = Alert().find(user_id)
        result = Alert().to_summary(alerts)
        return jsonify(result)
    raise exceptions.AuthError(
        {"code": "Unauthorized", "description": "Scope not matched.  Access Denied."},
        403,
    )


@app.route("/info")
@oidc.oidc_auth('default')
def info():
    """Return the JSONified user session for debugging."""
    return jsonify(
        id_token=session.get("id_token"),
        userinfo=session.get("userinfo"),
        person_api_v1=session.get("idvault_userinfo"),
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
