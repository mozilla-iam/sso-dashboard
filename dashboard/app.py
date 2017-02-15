from flask import Flask, render_template, jsonify, session
from flask_assets import Environment, Bundle
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname
import os
import hashlib

import config
import auth

from op import authzero

from flask_sse import sse

load_dotenv(find_dotenv())

app = Flask(__name__)





if os.environ.get('ENVIRONMENT') == 'Production':
    app.config.from_object(config.ProductionConfig())
elif os.environ.get('ENVIRONMENT') == 'Development':
    print("Development Mode Running")
    app.config.from_object(config.DevelopmentConfig())

print app.config

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
#app.config["REDIS_URL"] = "redis://localhost"
app.register_blueprint(sse, url_prefix='/stream')


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
#@oidc.oidc_auth
def dashboard():
    """Primary dashboard the users will interact with."""
    user = {
        "session": {
            "userinfo": {
                "email": "andrewkrug@gmail.com"
            }
        }
    }
    #user = session['userinfo']
    m = hashlib.md5()
    m.update("andrewkrug@gmail.com")
    #m.update(user['email'])
    robohash = m.hexdigest()
    return render_template('dashboard.html', user=user, robohash=robohash)

@app.route('/info')
#@oidc.oidc_auth
def info():
    """Return the JSONified user session for debugging."""
    return jsonify(
            id_token=session['id_token'],
            access_token=session['access_token'],
            userinfo=session['userinfo']
        )


@app.route('/hello')
def publish_hello():
    sse.publish({"message": "Hello!"}, type='greeting')
    print "published"
    return "Message sent!"


if __name__ == '__main__':

    app.run()
