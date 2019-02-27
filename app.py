from flask import (
                   Flask,
                   flash,
                   redirect,
                   render_template,
                   request,
                   session)
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired


from scripts.config import app_settings, mail_settings
from scripts.login import UserModel, login_required, verify_user
from scripts.item import ItemModel
from scripts.mail import reset_password, mail
from scripts.schedule import tasks_overdue

app = Flask(__name__)

app.config.update(app_settings)
app.config.update(mail_settings)

ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

Session(app) # noqa


@app.route('/')
@login_required
def index():

    return render_template('index.html')


@app.route('/account', methods=["GET", "POST"])
@login_required
def account():
    user = UserModel.find_by_id(session["user_id"])

    return render_template('/account/account.html', user=user.json())


@app.route("/account/login", methods=["GET", "POST"])
def login():
    # clear any user id
    session.clear()
    if request.method == "POST":
        name = request.form.get("username")
        password = request.form.get("password")
        # Ensure username was submitted
        if not name:
            flash("Username is not entered", 'danger')
            return redirect("/account/login")
        elif not password:
            flash("Password is not entered", 'danger')
            return redirect("/account/login")

        user = UserModel.find_by_username(name)

        if not user or not check_password_hash(user.password, password):
            flash("username or password not correct", 'danger')
            return redirect("/account/login")

        # Remember which user has logged in
        session["user_id"] = user.id
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("/account/login.html")


@app.route("/account/logout", methods=["GET", "POST"])
@login_required
def logout():
    # forget user_id
    session.clear()
    return redirect("/")


@app.route("/account/register", methods=["GET", "POST"])
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
            flash("Please enter an email address as your username", 'danger')
            return redirect('/account/register')
        # ensure password is not blank
        elif not password:
            flash("Please provide a valid password", 'danger')
            return redirect('/account/register')
        elif not name:
            flash("Please provide a valid name", 'danger')
            return redirect('/account/register')
        elif not supervisor:
            flash("Please provide a valid supervisor", 'danger')
            return redirect('/account/register')

        password = generate_password_hash(password)

        user = UserModel(username, name, password, supervisor)

        if user.find_by_username(username):
            flash("Username already exists, please log in with your email",
                  'danger')
            return redirect('/account/register')

        # adds user to the database
        try:
            user.save_to_db()
        except Exception:
            flash("something went wrong, please try again", 'danger')
            return redirect('/register')

        verify_user(user.username, ts)

        # remembers the user id in sessions to allow access to other pages.
        session["user_id"] = user.id

        return redirect('/')
    else:
        return render_template('/account/register.html', users=users)


@app.route("/account/verify/<string:token>", methods=["GET", "POST"])
def verify(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
    except SignatureExpired:
        email = ts.loads(token, salt="email-confirm-key")
        user = UserModel.find_by_username(email)

        verify_user(user.username, ts)

        flash("The link has expired \
               a new email will be sent to your email address", 'danger')
        return redirect('/')
    except Exception:
        flash("Something went wrong \
               please contact support for assistance", 'danger')
        return redirect('/')

    user = UserModel.find_by_username(email)

    if user:
        user.verified = True
        user.save_to_db()

    flash("Thank you for registering your email", 'success')
    return redirect('/')


@app.route("/account/reset", methods=["GET", "POST"])
def password_reset_request():
    if request.method == "POST":
        email = request.form.get("email")
        token = ts.dumps(email, salt='recovery-key')

        reset_password(email, token)
        return "Please check your email for reset url"
    else:
        return render_template("/account/reset.html")


@app.route("/account/reset/<string:token>")
def password_reset(token):
    session.clear()
    try:
        email = ts.loads(token, salt="recovery-key", max_age=86400)
    except Exception:
        flash("The token has expired, please try reset your password again",
              'danger')
        return redirect('/account/login')

    user = UserModel.find_by_username(email)

    if not user.verified:
        flash('Your account must be verified', 'danger')
        redirect('/')

    return render_template('/account/passwordconfirmed.html', username=email)


@app.route("/account/passwordconfirmed", methods=["GET", "POST"])
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

        flash("Password successfully changed", 'success')
        return redirect('/')

    return redirect('/')


@app.route("/account/delete", methods=["GET", "POST"])
@login_required
def account_delete():
    if request.method == "POST":

        # import username and save as name
        email = request.form.get("email")
        password = request.form.get("password")

        if not email:
            flash("Please enter an email address as your username", 'danger')
            return redirect('/account/register')
        # ensure password is not blank
        elif not password:
            flash("Please provide a valid password", 'danger')
            return redirect('/account/register')

        user = UserModel.find_by_username(email)

        if not user or not check_password_hash(user.password, password):
            flash("username or password do not match", 'danger')
            return redirect("/account")

        # delete user to the database
        try:
            user.delete_from_db()
        except Exception:
            flash("something went wrong, please try again", 'danger')
            return redirect('/account')

        session.clear()
        return redirect('/')


@app.route("/manager")
@login_required
def manager():
    user = UserModel.find_by_id(session["user_id"])
    items = ItemModel.listWhoItems(user.id)
    item_list = [item.manage() for item in items]

    return render_template("/manager.html", who=user, items=item_list)


@app.route('/manager/overdue')
def overdue_manager():
    user = "All Users"
    items = ItemModel.listOverdueItems()
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

@app.route('/test')
def test():

    tasks_overdue(app)
    return "<a href='/test'>test again</a>"

if __name__ == '__main__':
    from db import db

    @app.before_first_request
    def create_tables():
        db.create_all()

    db.init_app(app)
    mail.init_app(app)
    app.run(port=5000, debug=True)

