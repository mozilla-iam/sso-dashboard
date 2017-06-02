import auth
import config
import logging
import mimetypes
import os
import watchtower

from flask import (Flask, render_template, jsonify, session, request, redirect,
                   send_from_directory)
from flask_assets import Environment, Bundle
from flask_secure_headers.core import Secure_Headers

from vanity import Router
from user import User
from s3 import AppFetcher
from op.yaml_loader import Application

app = Flask(__name__)
AppFetcher().sync_config_and_images()

logger = logging.getLogger(__name__)

if os.environ.get('ENVIRONMENT') == 'Production':
    # Only cloudwatch log when app is in production mode.
    handler = watchtower.CloudWatchLogHandler()
    logger.info("Getting production config")
    app.logger.addHandler(handler)
    app.config.from_object(config.ProductionConfig())
elif os.environ.get('ENVIRONMENT') == 'Development':
    # Only log flask debug in development mode.
    handler = logging.StreamHandler()
    logging.getLogger("werkzeug").addHandler(handler)
    app.config.from_object(config.DevelopmentConfig())

if os.environ.get('LOGGING') == 'True':
    logging.basicConfig(level=logging.INFO)

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

# Load proxy router for redirect urls like gmail
vanity = Router(app_load=Application(), flask_app=app)
vanity.setup()

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
                'https://*.google-analytics.com'
            ],
            'style-src': [
                'self',
                'ajax.googleapis.com',
                'fonts.googleapis.com',
            ],
            'img-src': [
                'self',
                'https://mozillians.org',
                'https://*.google-analytics.com'
            ],
            'font-src': [
                'self',
                'fonts.googleapis.com',
                'fonts.gstatic.com',
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


@app.route('/favicon.ico')
@sh.wrapper()
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'),
                               'favicon.ico')


@app.route('/')
@sh.wrapper()
def home():
    return redirect('/dashboard', code=302)


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

    AppFetcher().sync_config_and_images()

    user = User(session)

    all_apps = Application().apps

    apps = user.apps(all_apps)['apps']

    return render_template(
        'dashboard.html',
        user=user,
        apps=apps
    )


@app.route('/info')
@sh.wrapper()
@oidc.oidc_auth
def info():
    """Return the JSONified user session for debugging."""
    return jsonify(
        id_token=session['id_token'],
        access_token=session['access_token'],
        userinfo=session['userinfo']
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
