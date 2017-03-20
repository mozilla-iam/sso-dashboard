from flask import Flask, render_template, jsonify, session, request, redirect, send_from_directory
from flask_assets import Environment, Bundle

from flask_secure_headers.core import Secure_Headers
from os.path import join, dirname
from werkzeug.exceptions import BadRequest

import os
import hashlib
import datetime

import config
import auth
from user import User
from alert import Alert
from s3 import AppFetcher
from op.yaml_loader import Application

from flask_sse import sse

app = Flask(__name__)

if os.environ.get('ENVIRONMENT') == 'Production':
    app.config.from_object(config.ProductionConfig())
elif os.environ.get('ENVIRONMENT') == 'Development':
    print("Getting development config")
    app.config.from_object(config.DevelopmentConfig())

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


if __name__ == '__main__':
    app.run()
