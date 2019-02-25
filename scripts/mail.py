import os
from flask_mail import Mail, Message
from flask import render_template

URL = os.environ.get('HEROKU_URL', 'http://127.0.0.1:5000/')

mail = Mail()

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'matt.w.taylor1989@gmail.com',
    "MAIL_PASSWORD": 'fishdoctor'
}


def verify_user(r, uuid):
    msg = Message(subject="Please verify your email",
                  sender="Calsta 3W Manager",
                  recipients=[r],
                  body="follow the following link to verify your email - {}verify/{}".format(URL, uuid),
                  html=render_template('emails/verifyemail.html', URL=URL, uuid=uuid))
    mail.send(msg)


def reset_password(email, token):
    msg = Message(subject="Your password reset code",
                  sender="Calsta 3W Manager",
                  recipients=[email],
                  body="follow the following link to reset your email - {}reset/{}".format(URL, token)
                  )
    mail.send(msg)
