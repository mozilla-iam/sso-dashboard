from flask import Flask, render_template, jsonify, session
from flask_assets import Environment, Bundle
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname
import os
import hashlib

import config
import auth

load_dotenv(find_dotenv())

app = Flask(__name__)

if os.environ.get('ENVIRONMENT') == 'Production':
    app.config.from_object(config.ProductionConfig())
elif os.environ.get('ENVIRONMENT') == 'Development':
    print("Development Mode Running")
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


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    user = "akrug@mozilla.com"
    m = hashlib.md5()
    m.update(user)
    robohash = m.hexdigest()

    return render_template('dashboard.html', user=user, robohash=robohash)


#@app.route('/redirect_uri')
#def handle_oidc_redirect():
#    code = request.args.get('code')
#    print code
#    pass

@app.route('/info')
@oidc.oidc_auth
def info():
    return jsonify(id_token=session['id_token'], access_token=session['access_token'],
userinfo=session['userinfo'])


if __name__ == '__main__':
    app.run()
