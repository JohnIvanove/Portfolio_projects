from flask import Flask, render_template, request, url_for, flash, redirect, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from random import shuffle
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sendgrid.helpers.mail import Mail
import sendgrid
import sqlite3
import random
import smtplib
import os
#https://computer-help-2.jimdosite.com/detalnishe/
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "your_secret_key"
ceruvanya = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(ceruvanya.Model, UserMixin):
    id = ceruvanya.Column(ceruvanya.Integer, primary_key=True)
    username = ceruvanya.Column(ceruvanya.String(150), nullable=False, unique=True)
    email = ceruvanya.Column(ceruvanya.String(150), nullable=False, unique=True)
    password = ceruvanya.Column(ceruvanya.String(150), nullable=False)
    theme = ceruvanya.Column(ceruvanya.String(100), default='light')
    font = ceruvanya.Column(ceruvanya.String(100), default='Arial')  # Додаємо поле для збереження вибору шрифту
    decks = ceruvanya.relationship('Deck', backref='owner', lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"

class Deck(ceruvanya.Model):
    id_deck = ceruvanya.Column(ceruvanya.Integer, primary_key=True)
    name_deck = ceruvanya.Column(ceruvanya.String(20), nullable=False)
    card_type = ceruvanya.Column(ceruvanya.String(20), nullable=False)
    color = ceruvanya.Column(ceruvanya.String(7), nullable=False)
    user_id = ceruvanya.Column(ceruvanya.Integer, ceruvanya.ForeignKey('user.id'), nullable=False)
    card_count = ceruvanya.Column(ceruvanya.Integer, nullable=False, default=0)
    text_ukr = ceruvanya.Column(ceruvanya.String(18), nullable=False)
    text_usa = ceruvanya.Column(ceruvanya.String(18), nullable=False)
    translation_direction = ceruvanya.Column(ceruvanya.String(20), nullable=False, default="usa_to_ukr")

@app.route("/get_theme", methods=["GET"])
@login_required
def get_theme():
    theme = current_user.theme
    return jsonify({"theme": theme})

@app.route("/set_user_theme", methods=["POST"])
@login_required
def set_user_theme():
    theme = request.form.get("theme")
    current_user.theme = theme
    ceruvanya.session.commit()
    print(theme)
    return jsonify({"status": "success", "theme": theme})

@app.route ("/set_font", methods = ["POST"])
@login_required
def set_font():
    font = request.form.get ("font")
    current_user.font = font
    ceruvanya.session.commit()
    #?print (font)
    return jsonify ({"status": "success", "font": font})

@app.route("/delete/<int:deck_id>", methods=["POST"])
def delete_deck(deck_id):
    deck = Deck.query.get(deck_id)
    if deck:
        ceruvanya.session.delete(deck)
        ceruvanya.session.commit()
        flash('Deck deleted successfully', 'success')
    else:
        flash('Deck not found', 'danger')
    return redirect(url_for('decks'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Використовуємо об'єкт `ceruvanya` для запиту
# Підключення до бази даних
def connect_db():
    db_path = os.path.join(app.instance_path, 'blog.db')
    conn = sqlite3.connect(db_path)
    print("Connected to SQLite database", conn)
    return conn

# Створення таблиці user_data в базі даних blog.db
def create_user_data_table():
    conn = connect_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_data
                 (id INTEGER PRIMARY KEY, user_id INTEGER, ip_address TEXT, browser_info TEXT,
                 FOREIGN KEY(user_id) REFERENCES user(id))''')
    print("Table user_data created successfully", c)
    conn.commit()
    conn.close()

create_user_data_table()

@app.route('/')
@app.route('/home')
def hello_world():
    user = current_user

    # Збір IP-адреси та інформації про браузер
    ip_address = request.remote_addr
    browser_info = request.headers.get('User-Agent')
    
    # Підключення до бази даних
    conn = connect_db()
    c = conn.cursor()
    
    # Перевірка, чи користувач аутентифікований
    if user.is_authenticated:
        user_id = user.id
        theme = user.theme
        font = user.font
    else:
        user_id = None  # або можна призначити значення для анонімного користувача, наприклад, 0 або 'anonymous'
        theme = 'light'  # або будь-яка тема за замовчуванням
        font = 'Arial'
    
    # Вставка даних у базу даних
    c.execute("INSERT INTO user_data (user_id, ip_address, browser_info) VALUES (?, ?, ?)",
              (user_id, ip_address, browser_info))
    #?print(f"-User ID: {user_id};\n-IP address: ({ip_address});\n-Browser info: ({browser_info}).")
    conn.commit()
    conn.close()

    return render_template('index.html', user=user, theme=theme, font=font)

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    if logout_user():
        flash("You have been logged out!", "success")
    logout_user()
    return render_template('index.html', user=current_user, theme='light')  # Тема за замовчуванням

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        remember = "remember" in request.form  # Перевіряємо, чи обрано "Remember Me"
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)  # Передаємо значення прапорця remember
            flash("You are now logged in!", "success")
            return redirect(url_for('hello_world'))  # Перенаправляємо на головну сторінку
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")
    return render_template("login.html", user=current_user, theme='light')  # Тема за замовчуванням

@app.route("/singing", methods=["GET", "POST"])
def user_singing():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email address already exists. Please use a different email.", "danger")
            return redirect("/singing")

        user = User(username=username, email=email, password=hashed_password)
        try:
            ceruvanya.session.add(user)
            ceruvanya.session.commit()
            login_user(user)
            flash("Your account has been created and you are now logged in!", "success")
            return redirect("/home")
        except Exception as e:
            flash(f"Your account hasn't been created! Error: {str(e)}", "danger")
            ceruvanya.session.rollback()
            return redirect("/singing")
    return render_template("singing.html", user=current_user, theme='light')  # Тема за замовчуванням

@app.route("/deck")
@login_required
def create_deck():
    return render_template("create_deck.html", user=current_user, theme = current_user.theme, font=current_user.font)

@app.route("/decks")
@login_required
def decks():
    all_decks = Deck.query.filter_by(user_id=current_user.id).all()  # Отримуємо всі колоди користувача
    return render_template("decks.html", user=current_user, decks=all_decks, theme = current_user.theme, font=current_user.font)  # Передаємо користувача та список колод у шаблон

@app.route("/learning")
@login_required
def learning():
    all_decks = Deck.query.filter_by(user_id=current_user.id).all()  # Отримуємо всі колоди користувача
    return render_template("learning.html", user=current_user, decks=all_decks, theme = current_user.theme, font=current_user.font)  # Передаємо користувача та список колод у шаблон
@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        user = current_user
        user.username = request.form["username"]
        user.email = request.form["email"]
        ceruvanya.session.commit()  # Save changes to the database
        return redirect(url_for("account"))
    else:
        return render_template("account.html", user=current_user, theme = current_user.theme, font = current_user.font)

@app.route("/function1", methods=["POST"])
@login_required
def function1():
    if 'name_deck' in request.form:
        name_deck = request.form.get ("name_deck")
        card_type = request.form.get ("card_type")
        card_color = request.form.get ("card_color")
        cards_len = request.form.get ("counter")
        direction = request.form.get ("direction")

        text_ukr = []
        text_usa = []

        for i in range(int(cards_len)):
            text_ukr.append(request.form.get(f"text_ukr_{i}"))
            text_usa.append(request.form.get(f"text_usa_{i}"))

        new_deck = Deck(name_deck=name_deck, card_type=card_type, color=card_color, user_id=current_user.id, card_count=cards_len, text_ukr=";".join(text_ukr), text_usa=";".join(text_usa), translation_direction=direction)
        
        ceruvanya.session.add(new_deck)
        ceruvanya.session.commit()

        return redirect(url_for('decks'))
    else:
        return redirect(url_for('create_deck'))

q = Flask(__name__)
# Налаштування Flask-Mail
q.config['MAIL_SERVER'] = 'smtp.gmail.com'
q.config['MAIL_PORT'] = 587
q.config['MAIL_USE_TLS'] = True
q.config['MAIL_USERNAME'] = 'Nazzych - Senior Developer'
q.config['MAIL_PASSWORD'] = '{[Nazzych|2020]}'
q.config['MAIL_DEFAULT_SENDER'] = 'nazzych666@gmail.com'
mail = Mail(q)

@app.route("/function2", methods=["POST"])
@login_required
def function2():
    # Get form data
    name = request.form.get('name')
    sender_email = request.form.get('email')
    message = request.form.get('message')
    q.logger.info("Form data received: Name=%s, Email=%s, Message=%s", name, sender_email, message)

    # Email details
    receiver_email = "LinchEgorovuch@outlook.com"

    # Create the email message
    msg = Message("Contact Form Submission",
                  sender='nazzych666@gmail.com',
                  recipients=[receiver_email])
    msg.body = f"Name: {name}\nEmail: {sender_email}\nMessage: {message}"

    try:
        # Send the email
        with q.app_context():
            mail.send(msg)
        q.logger.info("Email sent successfully")

        flash("Email sent successfully!", "success")
    except Exception as e:
        q.logger.error("Failed to send email. Error: %s", e)
        flash(f"Failed to send email. Error: {e}", "danger")

    return redirect('home')

@app.route("/edit/<int:deck_id>", methods=["GET", "POST"])
@login_required
def edit(deck_id):
    deck = Deck.query.get_or_404(deck_id)  # Get deck by its ID or return 404 if not found
    if request.method == "POST":
        deck.name_deck = request.form["name_deck"]
        deck.card_type = request.form["card_type"]
        deck.color = request.form["card_color"]
        deck.card_count = request.form["counter"]
        deck.translation_direction = request.form["translation_direction"]  # Додаємо збереження напрямку перекладу
        # Update text for each card
        text_ukr = []
        text_usa = []
        for i in range(int(deck.card_count)):
            text_ukr_value = request.form.get(f"text_ukr_{i}")
            text_usa_value = request.form.get(f"text_usa_{i}")

            text_ukr.append(text_ukr_value if text_ukr_value is not None else "")
            text_usa.append(text_usa_value if text_usa_value is not None else "")
        
        deck.text_ukr = ";".join(text_ukr)
        deck.text_usa = ";".join(text_usa)
        
        ceruvanya.session.commit()  # Save changes to the database
        return redirect(url_for("decks"))

    # Split the text values to pass them to the template
    text_ukr_list = deck.text_ukr.split(";")
    text_usa_list = deck.text_usa.split(";")
    
    return render_template("edit.html", user=current_user, deck=deck, card_count=int(deck.card_count), text_ukr_list=text_ukr_list, text_usa_list=text_usa_list, theme = current_user.theme, font=current_user.font)

@app.route("/start/<int:deck_id>", methods=['GET', 'POST'])
@login_required
def start(deck_id):
    deck = Deck.query.get_or_404(deck_id)

    # Визначте дані для питань і варіантів відповіді
    if deck.translation_direction == 'usa_to_ukr':
        questions = deck.text_usa.split(";")
        correct_answers = deck.text_ukr.split(";")
    else:
        questions = deck.text_ukr.split(";")
        correct_answers = deck.text_usa.split(";")
    
    # Генеруйте випадкові варіанти відповідей для quizzes
    random_words_ukr = [
    "яблуко", "комп'ютер", "банан", "клавіатура", "вишня", "монітор", "фінік", "принтер",
    "чорниця", "сканер", "інжир", "планшет", "виноград", "телефон", "диня", "камера",
    "ківі", "навушники", "лимон", "зарядний", "манго", "батарея", "нектарин", "програмне забезпечення",
    "апельсин", "апаратне забезпечення", "папая", "мережа", "айва", "інтернет", "малина", "вебсайт"
    ]
    random_words_usa = [
    "apple", "laptop", "banana", "keyboard", "cherry", "monitor", "date", "printer",
    "elderberry", "scanner", "fig", "tablet", "grape", "phone", "honeydew", "camera",
    "kiwi", "headphones", "lemon", "charger", "mango", "battery", "nectarine", "software",
    "orange", "hardware", "papaya", "network", "quince", "internet", "raspberry", "website"
    ]
    options = []

    for i in range(deck.card_count):
        incorrect_answers = random_words_ukr if deck.translation_direction == 'usa_to_ukr' else random_words_usa
        shuffle(incorrect_answers)
        answer_options = [correct_answers[i]] + incorrect_answers[:3]  # 3 випадкових неправильних відповіді + 1 правильна відповідь
        shuffle(answer_options)  # перемішати варіанти відповідей
        options.append(answer_options)

    if deck.card_type == 'quizzes':
        return render_template("quizz.html", user=current_user, questions=questions, options=options, correct_answers=correct_answers, card_count=deck.card_count, theme = current_user.theme, font=current_user.font)
    elif deck.card_type == 'true_false':
        answers = random.choices(correct_answers + (random_words_ukr if deck.translation_direction == 'usa_to_ukr' else random_words_usa), k=deck.card_count)
        return render_template("true_false.html", user=current_user, questions=questions, correct_answers=correct_answers, answers=answers, card_count=deck.card_count, theme = current_user.theme, font=current_user.font)
    elif deck.card_type == 'input_answer':
        return render_template("input_answer.html", user=current_user, questions=questions, correct_answers=correct_answers, card_count=deck.card_count, theme = current_user.theme, font=current_user.font)
    else:
        flash("Unknown deck type!", "danger")
        return redirect(url_for("learning"))

@app.route("/contact")
@login_required
def contact():
    return render_template("contacts.html", user=current_user, theme = current_user.theme, font=current_user.font)

@app.route("/privat_policy")
@login_required
def privat_policy():
    return render_template ("privatpolicy.html", user=current_user, theme = current_user.theme, font=current_user.font)

@app.route("/logika")
@login_required
def logika():
    return render_template ("logikaschool.html", user=current_user, theme = current_user.theme, font=current_user.font)

@app.route("/tutorial")
@login_required
def tutorial():
    return render_template ("tutorial.html", user=current_user, theme = current_user.theme, font=current_user.font)

@app.route("/whoweare")
@login_required
def whoweare():
    return render_template ("whoweare.html", user=current_user, theme = current_user.theme, font=current_user.font)

@app.route("/whywe")
@login_required
def whywe():
    return render_template ("whywe.html", user=current_user, theme = current_user.theme, font=current_user.font)

if __name__ == "__main__":
    with app.app_context():
        ceruvanya.create_all()  # Створення нових таблиць з правильною структурою
    app.run(debug=True, port=8080)
#?.
"""
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("You are now logged in!", "success")
            return redirect(url_for('decks'))  # Перенаправляємо на сторінку колод після входу
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")
    return render_template("login.html", user=current_user)
"""