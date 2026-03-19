from flask import Flask,session
import os
from dotenv import load_dotenv
from application.database import db

load_dotenv()

app=None
def create_app():
    app=Flask(__name__)
    app.debug=True
    app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///placement.sqlite3'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    db.init_app(app)
    app.app_context().push()
    return app

app=create_app()
from application.controllers import *

if __name__=="__main__":
    with app.app_context():
        db.create_all()
        Admin=User.query.filter_by(role="admin").first()
        if Admin is None:
            Admin=User(username=os.getenv('ADMIN_USERNAME'),
                       email=os.getenv('ADMIN_EMAIL'),
                       password=os.getenv('ADMIN_PWD'),
                       role="admin")
            db.session.add(Admin)
            db.session.commit()
    app.run(debug=True)
                       