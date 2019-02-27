from flask_mail import Mail, Message
from flask import render_template

from scripts.config import URL


mail = Mail()


def verify_user_email(r, uuid):
    msg = Message(subject="Please verify your email",
                  sender="Calsta 3W Manager",
                  recipients=[r],
                  body="follow the following link to verify your email -\
                       {}account/verify/{}".format(URL, uuid),
                  html=render_template('emails/verifyemail.html',
                                       URL=URL, uuid=uuid))
    mail.send(msg)


def reset_password(email, token):
    msg = Message(subject="Your password reset code",
                  sender="Calsta 3W Manager",
                  recipients=[email],
                  body="follow the following link to reset your email -\
                       {}account/reset/{}".format(URL, token)
                  )
    mail.send(msg)


def overdue_item_email(email, message, timeframe):
    msg = Message(subject="Your 3W item is due {}".format(timeframe),
                  sender="Calsta 3W Manager",
                  recipients=[email],
                  body=message
                  )
    print(msg)
   # mail.send(msg)
