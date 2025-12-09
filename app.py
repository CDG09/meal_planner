from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import Config

#Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

#Initialize SQLAlchemy
db = SQLAlchemy(app)

#Model Imports
from models import User

#Create tables (if they don't exist)
with app.app_context():
    db.create_all()

#Routes
@app.route('/')
def home():
    return render_template('home.html', active_page='home')


if __name__ == '__main__':
    app.run()
