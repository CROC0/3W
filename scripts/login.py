from functools import wraps

from flask import redirect, session

from db import db


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    name = db.Column(db.String(80))
    password = db.Column(db.String(80))
    supervisor = db.Column(db.String(80))

    def __init__(self, username, name, password, supervisor):
        self.username = username
        self.name = name
        self.password = password
        self.supervisor = supervisor

    def __repr__(self):
        return self.name

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_subordinate_list(cls, _id):
        name = cls.find_by_id(_id)
        subordinate = cls.query.filter_by(supervisor=name.name).all()
        return ([sub.id for sub in subordinate])

    @classmethod
    def listUsers(cls):
        return cls.query.all()
