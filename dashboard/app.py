from flask import Flask, render_template
from flask_assets import Environment, Bundle
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname
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
css = Bundle('css/base.css', sass,
                 filters='cssmin', output="css/gen/all.css")
assets.register('css_all', css)


@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run()
