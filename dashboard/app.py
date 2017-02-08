from flask import Flask, render_template, jsonify
from flask_assets import Environment, Bundle
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
import os

import config

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

client_info=dict(
    client_id=oidc_config.client_id(),
    client_secret=oidc_config.client_id()
)

provider_info=dict(
    issuer=oidc_config.OIDC_DOMAIN,
    authorization_endpoint=oidc_config.auth_endpoint(),
    token_endpoint=oidc_config.token_endpoint()
)

auth = OIDCAuthentication(
    app,
    provider_configuration_info=provider_info,
    client_registration_info=client_info
)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/info')
@auth.oidc_auth
def info():
    return jsonify(
        id_token=flask.session['id_token'],
        access_token=flask.session['access_token'],
        userinfo=flask.session['userinfo']
    )


if __name__ == '__main__':
    app.run()
