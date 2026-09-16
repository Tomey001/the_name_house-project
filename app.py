# app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'warning'

os.makedirs(
    os.path.join(app.root_path, 'instance'),
    exist_ok=True
)

@login_manager.user_loader
def load_user(user_id):
    with app.app_context():
        from models import Admin
        return db.session.get(Admin, int(user_id))

# Import routes LAST — after everything is set up
from routes import *

if __name__ == '__main__':
    app.run(debug=True)