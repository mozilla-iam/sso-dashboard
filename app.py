from flask import Flask, render_template
from flask_assets import Environment, Bundle


app = Flask(__name__)

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
