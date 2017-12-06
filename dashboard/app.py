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
from flask_talisman import Talisman, ALLOW_FROM

import auth
import config
import person
import vanity

from csp import DASHBOARD_CSP
from models.user import User
from models.user import FakeUser
from op.yaml_loader import Application
from models.alert import Rules
from models.tile import S3Transfer

logging.basicConfig(level=logging.INFO)

with open('logging.yml', 'r') as log_config:
    config_yml = log_config.read()
    config_dict = yaml.load(config_yml)
    logging.config.dictConfig(config_dict)

logger = logging.getLogger('sso-dashboard')

app = Flask(__name__)

talisman = Talisman(
    app, content_security_policy=DASHBOARD_CSP,
)

app.config.from_object(config.Config(app).settings)
app_list = S3Transfer(config.Config(app).settings)
app_list.sync_config()

assets = Environment(app)
js = Bundle('js/base.js', filters='jsmin', output='js/gen/packed.js')
assets.register('js_all', js)

sass = Bundle('css/base.scss', filters='scss')
css = Bundle(sass, filters='cssmin', output='css/gen/all.css')
assets.register('css_all', css)

# Hack to support serving .svg
mimetypes.add_type('image/svg+xml', '.svg')

oidc_config = config.OIDCConfig()
authentication = auth.OpenIDConnect(
    oidc_config
)
oidc = authentication.auth(app)
person_api = person.API()

vanity_router = vanity.Router(app, app_list).setup()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'), 'favicon.ico')


@app.route('/')
def home():
    return redirect('/dashboard', code=302)


@app.route('/csp_report', methods=['POST'])
def csp_report():
    return '200'


# XXX This needs to load the schema from a better location
# See also https://github.com/mozilla/iam-project-backlog/issues/161
@app.route('/claim')
def claim():
    """Show the user schema - this path is refered to by
    our OIDC Claim namespace, i.e.: https://sso.mozilla.com/claim/*"""
    return redirect(
        'https://github.com/mozilla-iam/cis/blob/master/cis/schema.json',
        code=302
    )


@app.errorhandler(404)
def page_not_found(error):
    if request.url is not None:
        logger.error(
            "A 404 has been generated for {route}".format(route=request.url)
        )
    return render_template('404.html'), 404


@app.route('/forbidden')
def forbidden():
    """Route to render error page."""

    if 'error' not in request.args:
        return render_template('forbidden.html')
    else:
        jws = request.args['error']

    token_verifier = auth.tokenVerification(jws=jws, public_key=app.config['FORBIDDEN_PAGE_PUBLIC_KEY'])
    token_verifier.verify

    return render_template(
        'forbidden.html', token_verifier=token_verifier
    )


@app.route('/logout')
@oidc.oidc_logout
def logout():

    """Route decorator destroys flask session and redirects to auth0 to destroy
    auth0 session.  Ending page is mozilla signout.html."""
    logger.info("User called logout route.")
    if os.environ.get('ENVIRONMENT') == 'Production':
        proto = "https"
    else:
        proto = "http"

    return_url = "{proto}://{server_name}/signout.html".format(
        proto=proto, server_name=app.config['SERVER_NAME']
    )

    logout_url = "https://{auth0_domain}/v2/logout?returnTo={return_url}".format(
        auth0_domain=oidc_config.OIDC_DOMAIN, return_url=return_url
    )

    return redirect(logout_url, code=302)


@app.route('/signout.html')
def signout():
    logger.info("Signout messaging displayed.")
    return render_template('signout.html')


@app.route('/dashboard')
@oidc.oidc_auth
def dashboard():
    """Primary dashboard the users will interact with."""
    logger.info("User: {} authenticated proceeding to dashboard.".format(session.get('id_token')['sub']))

    if "Mozilla-LDAP" in session.get('userinfo')['sub']:
        logger.info("Mozilla IAM user detected. Attempt enriching with ID-Vault data.")
        try:
            session['idvault_userinfo'] = person_api.get_userinfo(session.get('id_token')['sub'])
        except Exception as e:
            logger.error("Could not enrich profile due to: {}.  Perhaps it doesn't exist?".format(e))

    # Transfer any updates in to the app_tiles.
    S3Transfer(config.Config(app).settings).sync_config()

    # Send the user session and browser headers to the alert rules engine.
    Rules(userinfo=session['userinfo'], request=request).run()

    user = User(session, config.Config(app).settings)
    apps = user.apps(Application(app_list.apps_yml).apps)

    return render_template(
        'dashboard.html',
        config=app.config,
        user=user,
        apps=apps,
        alerts=None
    )


@app.route('/styleguide')
def styleguide():
    user = FakeUser(config.Config(app).settings)
    apps = user.apps(Application(app_list.apps_yml).apps)

    return render_template(
        'dashboard.html',
        config=app.config,
        user=user,
        apps=apps,
        alerts=None
    )


@app.route('/notifications')
@oidc.oidc_auth
def notifications():
    user = User(session, config.Config(app).settings)
    return render_template(
        'notifications.html',
        config=app.config,
        user=user,
    )


@oidc.oidc_auth
@app.route('/alert/<alert_id>', methods=['POST'])
def alert_operation(alert_id):
    if request.method == 'POST':
        user = User(session, config.Config(app).settings)

        if request.data is not None:
            data = json.loads(data)
            alert_action = data.get('alert_action')
        else:
            alert_action = 'acknowledge' # (escalate|acknowledge|false-positive)

        result = user.acknowledge_alert(alert_id, alert_action)

        if result['ResponseMetadata']['HTTPStatusCode'] == 200:
            return '200'
        else:
            return '500'


@app.route('/info')
@oidc.oidc_auth
def info():
    """Return the JSONified user session for debugging."""
    return jsonify(
        id_token=session.get('id_token'),
        access_token=session.get('access_token'),
        userinfo=session.get('userinfo')
    )


@app.route('/about')
def about():
    return render_template(
        'about.html'
    )


@app.route('/contribute.json')
def contribute_lower():
    data = {
        "name": "sso-dashboard by Mozilla",
        "description": "A single signon dashboard for auth0.",
        "repository": {
            "url": "https://github.com/mozilla-iam/sso-dashboard",
            "license": "MPL2"
        },
        "participate": {
            "home": "https://github.com/mozilla-iam/sso-dashboard",
            "irc": "irc://irc.mozilla.org/#infosec",
            "irc-contacts": [
                "Andrew"
            ]
        },
        "bugs": {
            "list": "https://github.com/mozilla-iam/sso-dashboard/issues",
            "report": "https://github.com/mozilla-iam/sso-dashboard/issues/new",
            "mentored": "https://github.com/mozilla-iam/sso-dashboard/issues?q=is%3Aissue+is%3Aclosed"  # noqa
        },
        "urls": {
            "prod": "https://sso.mozilla.com/",
            "stage": "https://sso.allizom.org/"
        },
        "keywords": [
            "python",
            "html5",
            "jquery",
            "mui-css",
            "sso",
            "auth0"
        ]
    }

    return jsonify(data)


if __name__ == '__main__':
    app.run()
