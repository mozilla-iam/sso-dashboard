from flask import Flask, render_template, jsonify, session, request, redirect, send_from_directory
from flask_assets import Environment, Bundle

from flask_secure_headers.core import Secure_Headers
from werkzeug.exceptions import BadRequest

import os
import hashlib
import datetime

import watchtower
import logging

import config
import auth


from user import User
from alert import Alert
from s3 import AppFetcher
from op.yaml_loader import Application

from flask_sse import sse

app = Flask(__name__)
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

js = Bundle('js/base.js',
            filters='jsmin', output='js/gen/packed.js')
assets.register('js_all', js)


sass = Bundle('*.sass', filters='sass', output='css/gen/sass.css')
css = Bundle(
            'css/base.css', sass,
            filters='cssmin', output="css/gen/all.css"
        )
assets.register('css_all', css)

oidc_config = config.OIDCConfig()

authentication = auth.OpenIDConnect(
    oidc_config
)

oidc = authentication.auth(app)

# Add secure Headers to satify observatory checks

sh = Secure_Headers()
sh.update(
    {
        'CSP': {
            'script-src':
                [
                    'self',
                    'ajax.googleapis.com',
                    'cdn.muicss.com',
                    'netdna.bootstrapcdn.com',
                    's.gravatar.com',
                    'fonts.googleapis.com'
                ],
            'style-src':
                [
                    'self',
                    'ajax.googleapis.com',
                    'cdn.muicss.com',
                    'netdna.bootstrapcdn.com',
                    's.gravatar.com',
                    'fonts.googleapis.com'
                ],
            'img-src':
                [
                    'self',
                    's.gravatar.com',
                    'i0.wp.com'
                ],
            'font-src':
                [
                    'self',
                    'netdna.bootstrapcdn.com',
                    'fonts.googleapis.com',
                    'cdn.muicss.com'
                ]
        }
    }
)

sh.update(
    {
        'HSTS':
            {
                'max-age': 1,
                'includeSubDomains': True,
                'preload': False
            }
    }
)

# Register the flask blueprint for SSE.
app.register_blueprint(sse, url_prefix='/stream')

@sse.before_request
def check_access():
    """Users can only view their own security alerts."""
    user = User(session)
    if request.args.get("channel") == Userhash():
        pass
    else:
        abort(403)

@app.route('/favicon.ico')
@sh.wrapper()
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'),
                               'favicon.ico')

@app.route('/')
@sh.wrapper()
def home():
    return redirect('/dashboard', code=302)

@app.route('/dashboard')
@sh.wrapper()
@oidc.oidc_auth
def dashboard():
    """Primary dashboard the users will interact with."""
    logger.info("User authenticated proceeding to dashboard.")
    AppFetcher().sync_config_and_images()
    user = User(session)
    alerts = Alert(user, app).get()
    all_apps = Application().apps
    apps = user.apps(all_apps)['apps']

    return render_template(
        'dashboard.html',
        user=user,
        apps=apps,
        alerts=alerts
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


@app.route('/alert', methods = ['POST'])
@sh.wrapper()
def publish_alert():
    """
    Takes JSON post with user e-mail to alert.
    Minimum fields are email and message in the form
    of a dict.

    Example:
        {
          "user": {"email": "andrewkrug@gmail.com"},
            "message": "this is a security alert"
        }
    """
    try:
        content = request.json
        #Send a real time event to the user
        m = hashlib.md5()
        m.update(content['user']['email'])
        channel = m.hexdigest()

        sse.publish(
            {"message": content['message']},
            type="alert",
            channel=channel
        )

        permanent_message = "Security Alert Logged at {date} : {message}".format(
            date=datetime.datetime.now(),
            message=content['message']
        )
        # Store the event in redis keyed to the users hashed e-mail

        Alert().set(channel, permanent_message)

        return jsonify({'status': 'success'})
    except:
        raise BadRequest('POST does not contain e-mail and message')
        return jsonify({'status': 'fail'})


vanity = Application().vanity_urls()
logger.info("Vanity URLs loaded for {num} apps.".format(num=len(vanity)))
logger.info(
    "Count of apps by OP is {stats}".format(stats=Application().stats())
)

def redirect_url():
    vanity_url = '/' + request.url.split('/')[3]

    logger.info("Attempting to match {url}".format(url=vanity_url))

    for match in vanity:
        if match.keys()[0] == vanity_url:
            logger.info(
                "Vanity URL found for {app}".format(app=match[vanity_url])
            )
            return redirect(match[vanity_url], code=301)
        else:
            pass

    logger.info(
        "Vanity URL could not be matched for {app}".format(app=vanity_url)
    )

for url in vanity:
    try:
        app.add_url_rule(url.keys()[0], url.keys()[0], redirect_url)
    except Exception as e:
        logger.error(e)
        logger.info("Could not create vanity URL for {app}".format(app=url))

if __name__ == '__main__':
    app.run()
