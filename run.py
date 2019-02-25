from app import app
from db import db
from app import mail

db.init_app(app)
mail.init_app(app)


@app.before_first_request
def create_tables():
    db.create_all()
