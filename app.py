from flask import Flask
import os

from application.database import db

app=None
def create_app():
    app=Flask(__name__)
    app.debug=True
    app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///placement.db'
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
                       mail=os.getenv('ADMIN_EMAIL'),
                       password=os.getenv('ADMIN_PWD'),
                       role="admin")
            db.session.add(Admin)
            db.session.commit()
    app.run(debug=True)
                       