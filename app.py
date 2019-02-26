import os

from flask import (
                   Flask,
                   flash,
                   redirect,
                   render_template,
                   request,
                   session)
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer


from scripts.login import UserModel, login_required
from scripts.item import ItemModel
from scripts.mail import verify_user, reset_password, mail_settings, mail


app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
                                                        'DATABASE_URL',
                                                        'sqlite:///data.db'
                                                        )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY')

app.config.update(mail_settings)
ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

URL = os.environ.get('HEROKU_URL', 'http://127.0.0.1:5000/')


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/')
@login_required
def index():

    return render_template('index.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    # clear any user id
    session.clear()
    if request.method == "POST":
        name = request.form.get("username")
        password = request.form.get("password")
        # Ensure username was submitted
        if not name:
            flash("Username is not entered", 'error')
            return render_template("/login.html")
        elif not password:
            flash("Password is not entered", 'error')
            return render_template("/account/login.html")

        user = UserModel.find_by_username(name)

        if not user or not check_password_hash(user.password, password):
            flash("username or password not correct", 'error')
            return render_template("/account/login.html")

        # Remember which user has logged in
        session["user_id"] = user.id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/account/login.html")


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    # forget user_id
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    users = UserModel.listUsers()

    if request.method == 'POST':

        # forget any user.id
        session.clear()
        # import username and save as name
        username = request.form.get("username")
        password = request.form.get("password")
        name = request.form.get("name")
        supervisor = request.form.get("supervisor")
        # ensure username is not blank
        if not username:
            flash("Please enter an email address as your username", 'error')
            return render_template("register.html", users=users)
        # ensure password is not blank
        elif not password:
            flash("Please provide a valid password", 'error')
            return render_template("register.html", users=users)
        elif not name:
            flash("Please provide a valid name", 'error')
            return render_template("register.html", users=users)
        elif not supervisor:
            flash("Please provide a valid supervisor", 'error')
            return render_template("register.html", users=users)

        password = generate_password_hash(password)

        user = UserModel(username, name, password, supervisor)

        if user.find_by_username(username):
            flash("Username already exists, please log in with your email",
                  'error')

            return render_template("account/register.html", users=users)

        # remembers the user id in sessions to allow access to other pages.


        uuid = ts.dumps(user.username, salt='email-confirm-key')

        verify_user(user.username, uuid)

        # adds user to the database
        try:
            user.save_to_db()
        except:
            flash("something went wrong, pleae try again")
            return redirect('/')

        session["user_id"] = user.id

        return redirect('/')
    else:
        return render_template('/account/register.html', users=users)


@app.route("/manager", methods=["GET", "POST"])
@login_required
def manager():
    user = UserModel.find_by_id(session["user_id"])
    items = ItemModel.listItems(user.id)
    item_list = [item.manage() for item in items]

    return render_template("/manager.html", who=user, items=item_list)


@app.route("/item/<int:item>")
@login_required
def item(item):
    user = UserModel.find_by_id(session["user_id"])
    items = ItemModel.listItem(item)
    item_list = [item.manage() for item in items]

    return render_template("/item.html", who=user, items=item_list)


@app.route("/completeditems")
@login_required
def completedItems():
    user = UserModel.find_by_id(session["user_id"])
    completedItems = ItemModel.listCompletedItems()
    item_list = [item.manage() for item in completedItems]

    return render_template("/completeditems.html", who=user, items=item_list)


@app.route("/update/<int:item_id>", methods=["POST"])
@login_required
def update(item_id):
    user = UserModel.find_by_id(session["user_id"])
    first_name = user.name.split(" ")
    detail = request.form.get("detail")

    item = ItemModel.find_by_id(item_id)
    tmp = item.detail
    time = datetime.now()
    time = time.strftime('%d/%m/%Y')
    item.detail = tmp + " - " + time + " ({}): ".format(first_name[0]) + detail

    item.save_to_db()

    return redirect('/item/{}'.format(item_id))


@app.route("/newitem", methods=["GET", "POST"])
@login_required
def newitem():
    user = UserModel.find_by_id(session["user_id"])

    if request.method == "POST":

        what = request.form.get("what")
        when = request.form.get("when")
        detail = request.form.get("detail")
        who = UserModel.find_by_name(request.form.get("who"))
        time = datetime.now()

        detail = time.strftime('%d/%m/%Y') + ": " + detail
        item = ItemModel(what, when, who.id, detail, user.id, False)

        item.save_to_db()

        return redirect("/manager")
    else:
        users = UserModel.listUsers()
        return render_template("/newitem.html", who=user, users=users)


@app.route("/verify/<string:token>", methods=["GET", "POST"])
def verify(token):

    email = ts.loads(token, salt="email-confirm-key", max_age=86400)

    user = UserModel.find_by_username(email)

    if user:
        user.verified = True
        user.save_to_db()

        flash("Thank you for registering your email", 'message')
        return redirect('/')
    else:
        flash("The link has expired, please try again", 'message')
        return redirect('/')


@app.route("/reset", methods=["GET", "POST"])
def password_reset_request():
    if request.method == "POST":
        email = request.form.get("email")
        token = ts.dumps(email, salt='recovery-key')

        reset_password(email, token)
        return "Please check your email for reset url"
    else:
        return render_template("/account/reset.html")


@app.route("/reset/<string:token>")
def password_reset(token):
    email = ts.loads(token, salt="recovery-key", max_age=86400)

    user = UserModel.find_by_username(email)

    if not user:
        return "your email does not exist"

    if not user.verified:
        return "your email must be verified"

    return render_template('/account/passwordreset.html', username=email)


@app.route("/passwordconfirmed", methods=["GET", "POST"])
def password_confirmed():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        hpassword = generate_password_hash(password)

        user = UserModel.find_by_username(email)

        if not user.verified:
            flash('Sorry your email was not verified.')
            return redirect('/')

        user.password = hpassword
        user.save_to_db()

        session["user_id"] = user.id

        flash("Password successfully changed", 'message')
        return redirect('/')

    return redirect('/')


if __name__ == '__main__':
    from db import db

    @app.before_first_request
    def create_tables():
        db.create_all()

    db.init_app(app)
    mail.init_app(app)
    app.run(port=5000, debug=True)
