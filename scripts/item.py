from db import db
from datetime import datetime
from scripts.login import UserModel


class ItemModel(db.Model):

    __tablename__ = 'manager'

    id = db.Column(db.Integer, primary_key=True)
    what = db.Column(db.String(180))
    when = db.Column(db.String())
    requester = db.Column(db.String(180))
    detail = db.Column(db.String(5000))
    who_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    complete = db.Column(db.Boolean())

    def __init__(self, what, when, who_id, detail, requester, complete):
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
                'requester': UserModel.find_by_id(self.requester),
                'complete': self.complete
                }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_what(cls, what):
        return cls.query.filter_by(what=what).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def listItems(cls):
        return cls.query.all()

    @classmethod
    def listWhoItems(cls, _id):
        items = cls.query.filter_by(who_id=_id).all()
        subordinates = UserModel.find_subordinate_list(_id)

        for person in subordinates:
            if person:
                items = items + cls.listWhoItems(person)
        return items

    @classmethod
    def listCompletedItems(cls):
        return cls.query.filter_by(complete=True).all()

    @classmethod
    def listItem(cls, item):
        return cls.query.filter_by(id=item).all()

    @classmethod
    def listOverdueItems(cls):
        items = cls.query.all()
        overdue_items = []
        for item in items:
            if datetime.strptime(item.when, '%Y-%m-%d') <= datetime.now():
                overdue_items.append(item)
        return overdue_items

    def check_status(self):
        if self.complete:
            return "Complete"
        else:
            if datetime.strptime(self.when, '%Y-%m-%d') < datetime.now():
                return "Overdue"
            return "WIP"
