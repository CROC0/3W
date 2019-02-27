import os

app_settings = {
    'SECRET_KEY': os.environ.get('SECRET_KEY'),
    "TEMPLATES_AUTO_RELOAD": True,
    'SQLALCHEMY_DATABASE_URI': os.environ.get(
                                            'DATABASE_URL',
                                            'sqlite:///data.db'
                                            ),
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SESSION_TYPE': 'filesystem',
    'PERMANENT_SESSION_LIFETIME': (1 * 60 * 60),
    'SESSION_PERMANENT': False
}

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": os.environ.get('EMAIL_USER'),
    "MAIL_PASSWORD": os.environ.get('EMAIL_PASSWORD')
}

URL = os.environ.get('HEROKU_URL', 'http://127.0.0.1:5000/')
