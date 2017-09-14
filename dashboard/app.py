import logging
import mimetypes
import os

from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import session
from flask_assets import Bundle
from flask_assets import Environment
from flask_secure_headers.core import Secure_Headers

import auth
import config
import vanity
from models.user import User
from op.yaml_loader import Application
from models.alert import Rules
from models.tile import S3Transfer

logger = logging.getLogger(__name__)
logging.getLogger(__name__).addHandler(logging.StreamHandler())
logging.basicConfig(level=logging.CRITICAL)

app = Flask(__name__)
app.config.from_object(config.Config(app).settings)

S3Transfer(config.Config(app).settings).sync_config()

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

vanity_router = vanity.Router(app=app).setup()
# Add secure Headers to satify observatory checks

sh = Secure_Headers()
sh.update(
    {
        'CSP': {
            'default-src': [
                'self',
            ],
            'script-src': [
                'self',
                'data:',
                'ajax.googleapis.com',
                'fonts.googleapis.com',
                'https://*.googletagmanager.com',
                'https://tagmanager.google.com',
                'https://*.google-analytics.com',
                'https://cdn.sso.mozilla.com',
                'https://cdn.sso.allizom.org',
                'https://dhjrqi6qcwjfu.cloudfront.net'
            ],
            'style-src': [
                'self',
                'ajax.googleapis.com',
                'fonts.googleapis.com',
                'https://cdn.sso.mozilla.com',
                'https://cdn.sso.allizom.org',
                'https://dhjrqi6qcwjfu.cloudfront.net'
            ],
            'img-src': [
                'self',
                'https://mozillians.org',
                'https://media.mozillians.org',
                'https://cdn.mozillians.org',
                'https://cdn.sso.mozilla.com',
                'https://cdn.sso.allizom.org',
                'https://*.google-analytics.com',
                'https://*.gravatar.com',
                'https://cdn.sso.mozilla.com',
                'https://cdn.sso.allizom.org',
                'https://dhjrqi6qcwjfu.cloudfront.net'
            ],
            'font-src': [
                'self',
                'fonts.googleapis.com',
                'fonts.gstatic.com',
                'https://cdn.sso.mozilla.com',
                'https://cdn.sso.allizom.org',
                'https://dhjrqi6qcwjfu.cloudfront.net'
            ]
        }
    }
)

sh.update(
    {
        'HSTS':
            {
                'max-age': 15768000,
                'includeSubDomains': True,
                'preload': False
            }
    }
)

sh.update(
    {
        'HPKP': {}
    }
)


@app.route('/favicon.ico')
@sh.wrapper()
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'),
                               'favicon.ico')


@app.route('/')
@sh.wrapper()
def home():
    return redirect('/dashboard', code=302)


# XXX This needs to load the schema from a better location
# See also https://github.com/mozilla/iam-project-backlog/issues/161
@app.route('/claim')
@sh.wrapper()
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
@sh.wrapper()
@oidc.oidc_auth
def dashboard():
    """Primary dashboard the users will interact with."""
    logger.info("User authenticated proceeding to dashboard.")

    # Transfer any updates in to the app_tiles.
    S3Transfer(config.Config(app).settings).sync_config()

    # Send the user session and browser headers to the alert rules engine.
    Rules(userinfo=session['userinfo'], request=request).run()

    user = User(session, config.Config(app).settings)
    apps = user.apps(Application().apps)

    return render_template(
        'dashboard.html',
        config=app.config,
        user=user,
        apps=apps,
        alerts=None
    )


@sh.wrapper
@oidc.oidc_auth
@app.route('/alert/<alert_id>', methods=['POST'])
def alert_operation(alert_id):
    if request.method == 'POST':
        user = User(session, config.Config(app).settings)
        result = user.acknowledge_alert(alert_id)

        if result['ResponseMetadata']['HTTPStatusCode'] == 200:
            return '200'
        else:
            return '500'


@app.route('/info')
@sh.wrapper()
@oidc.oidc_auth
def info():
    """Return the JSONified user session for debugging."""
    return jsonify(
        id_token=session.get('id_token'),
        access_token=session.get('access_token'),
        userinfo=session.get('userinfo')
    )


@app.route('/about')
@sh.wrapper()
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
