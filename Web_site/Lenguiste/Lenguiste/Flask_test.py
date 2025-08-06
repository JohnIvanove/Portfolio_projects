from flask import Flask, render_template, request, url_for, flash, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config['SECRET_KEY'] = 'your_secret_key'
ceruvanya = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
migrate = Migrate(app, ceruvanya)

class User(ceruvanya.Model, UserMixin):
    id = ceruvanya.Column(ceruvanya.Integer, primary_key=True)
    username = ceruvanya.Column(ceruvanya.String(20), nullable=False)
    email = ceruvanya.Column(ceruvanya.String(120), unique=True, nullable=False)
    password = ceruvanya.Column(ceruvanya.String(128), nullable=False)
#    date = ceruvanya.Column (ceruvanya.DateTime, default = datetime.utcnow)
    def __repr__(self):
        return f"<User {self.email}>"


class Deck (ceruvanya.Model):
    id = ceruvanya.Column(ceruvanya.Integer, primary_key=True)
    name = ceruvanya.Column(ceruvanya.String(20), nullable=False)
    id_user = ceruvanya.Column(ceruvanya.Integer, nullable=False)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@app.route("/home")
def hello_world():
    if current_user.is_authenticated:
        flash(f"Hello {current_user.username}", "success")
    else:
        flash("You are not logged in - please log in", "danger")
    return render_template("index.html", user=current_user)

@app.route("/login", methods=["GET", "POST"])
def login():
    data = User.query.order_by().all()
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        for python in data:
            if python.email == email and python.password == password:
                flash("You are registered", "danger")
                return render_template ("home.html")
            else:
                flash("You are not registered", "danger")
                return render_template ("home.html")
    return render_template("login.html")

@app.route("/singing", methods=["GET", "POST"])
def user_singing():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        # Перевірка, чи email вже існує
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email address already exists. Please use a different email.", "danger")
            return redirect("/singing")

        user = User(username=username, email=email, password=hashed_password)
        try:
            ceruvanya.session.add(user)
            ceruvanya.session.commit()
            # Автоматичний вхід після реєстрації
            login_user(user)
            flash("Your account has been created and you are now logged in!", "success")
            return redirect("/home")
        except Exception as e:
            flash("Your account hasn't been created! Error: " + str(e), "danger")
            ceruvanya.session.rollback()
            return redirect("/singing")
    return render_template("singing.html", user=current_user)


@app.route("/deck", methods=["GET", "POST"])
def create_deck():
    user = User.query.get(id)
    if user is None:
        flash("User not found!", "danger")
        return redirect("/home")
    
    if request.method == "POST":
        name = request.form["name_deck"]
        deck = Deck(name=name, user_id=user.id)
        try:
            ceruvanya.session.add(deck)
            ceruvanya.session.commit()
            flash("Deck has been created successfully!", "success")
            return redirect("/home")
        except Exception as e:
            ceruvanya.session.rollback()
            flash("Your deck hasn't been created! Error: " + str(e), "danger")
            return redirect("/home")
    
    return render_template("deck.html", user=user)

@app.route('/acount')
def user_account():
    user = current_user  # або інша логіка отримання користувача
    return render_template('user.html', user=user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        ceruvanya.create_all()
    app.run(debug=True, port=8080)
