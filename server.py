import config
from models import User, Page, Change

from flask import Flask, render_template

app = Flask(__name__)
app.config.from_object(config.FlaskConfig)


# def get_user_


@app.route('/')
def index():
    return render_template('index.html',
                           User=User,
                           Page=Page,
                           Change=Change)

if __name__ == '__main__':
    app.run()
