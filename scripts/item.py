from db import db
from flask import session
from datetime import datetime
from scripts.login import UserModel

class ItemModel(db.Model):
    __tablename__ = 'manager'

    id = db.Column(db.Integer, primary_key=True)
    what = db.Column(db.String(180))
    when = db.Column(db.String())
    requester = db.Column(db.String(180))
    detail = db.Column(db.String(5000))
    who_id = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)
    complete = db.Column(db.Boolean())

    def __init__(self,what,when,who_id,detail,requester,complete):
        self.what = what
        self.when = when
        self.who_id = who_id
        self.detail = detail
        self.requester = requester
        self.complete = complete

    def manage(self):
        return {
                'id': self.id,
                'what': self.what,
                'when': self.when,
                'who': UserModel.find_by_id(self.who_id),
                'stat': self.check_status(),
                'detail': self.detail,
                'requester': UserModel.find_by_id(self.requester)
                }


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_what(cls,what):
        return cls.query.filter_by(what=what).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def listItems(cls):
        return cls.query.filter_by(who_id=session['user_id']).all()

    @classmethod
    def listItem(cls,item):
        return cls.query.filter_by(id=item).all()

    @classmethod
    def subordinateListItems(cls,ids):
        subordinate_list = []
        for _id in ids:
            tmp_object = cls.query.filter_by(who_id=_id).all()
            subordinate_list = subordinate_list + [item.manage() for item in tmp_object]
        return subordinate_list

    def check_status(self):
        if datetime.strptime(self.when,'%Y-%m-%d') < datetime.now():
            return "Overdue"
        return "WIP"
