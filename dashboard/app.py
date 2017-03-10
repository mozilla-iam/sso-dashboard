from flask import Flask, render_template, jsonify, session, request, redirect
from flask_assets import Environment, Bundle
from flask_redis import FlaskRedis
from os.path import join, dirname
from werkzeug.exceptions import BadRequest
import os
import hashlib
import datetime

import config
import auth
from user import User
from op.yaml_loader import Application

from op import authzero

from flask_sse import sse

app = Flask(__name__)



if os.environ.get('ENVIRONMENT') == 'Production':
    app.config.from_object(config.ProductionConfig())
elif os.environ.get('ENVIRONMENT') == 'Development':
    print("Getting development config")
    app.config.from_object(config.DevelopmentConfig())

redis_store = FlaskRedis(app)
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

#Register the flask blueprint for SSE.
app.register_blueprint(sse, url_prefix='/stream')




@sse.before_request
def check_access():
    """Users can only view their own security alerts."""
    user = User(session)
    if request.args.get("channel") == Userhash():
        pass
    else:
        abort(403)

@app.route('/')
def home():
    return redirect('/dashboard', code=302)

@app.route('/dashboard')
@oidc.oidc_auth
def dashboard():
    """Primary dashboard the users will interact with."""
    user = User(session)
    alerts = redis_store.lrange(user.userhash(), 0, -1)
    all_apps = Application().apps
    apps = user.apps(all_apps)['apps']

    return render_template(
        'dashboard.html',
        user=user,
        apps=apps,
        alerts=alerts
    )

@app.route('/info')
@oidc.oidc_auth
def info():
    """Return the JSONified user session for debugging."""
    return jsonify(
            id_token=session['id_token'],
            access_token=session['access_token'],
            userinfo=session['userinfo']
        )


@app.route('/alert', methods = ['POST'])
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
    #try:
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
    #Store the event in redis keyed to the users hashed e-mail
    redis_store.lpush(channel, permanent_message)

    return jsonify({'status': 'success'})
    #except:
    #    raise BadRequest('POST does not contain e-mail and message')
    #    return jsonify({'status': 'fail'})


if __name__ == '__main__':
    app.run()
