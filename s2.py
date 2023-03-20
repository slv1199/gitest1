from flask import Flask, render_template, request, url_for, jsonify, current_app, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user


from flask_socketio import SocketIO
from flask_socketio import send
from collections import OrderedDict
import smtplib

import csv

# app = Flask(__name__)
app = Flask(__name__,
            static_url_path='',
            static_folder='static')

app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['JSON_SORT_KEYS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

#1
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

# @app.route('/')
# def home():
#     # only by sending this page first will the client be connected to the socketio instance
#     return current_app.send_static_file('index1.html')

@app.route('/sendTable', methods=['POST'])
def hello():
    if request.method == 'POST':

        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            json = request.json

            with open('state-data.csv', 'w', newline='') as csvfile:
                fields = ['id', 'city', 'country', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8']
                writer = csv.DictWriter(csvfile, fields, restval='Unknown', extrasaction='ignore')
                writer.writeheader()
                writer.writerows(json)
            print(json)

            socketio.send(json, broadcast=True)

            return current_app.send_static_file('index1.html')
        else:
            return 'Content-Type not supported!'


@app.route('/table', methods=['GET'])
def getTable():  # listening the message
    print('/table')
    data = []

    with open('state-data.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print('row: ', row)
            data.append(row)

    return jsonify(data)

@socketio.on('connect')
def test_connect(auth):
    print('Client CONNECTED!!!!')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


##CREATE TABLE
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


# db.create_all()


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html", title = "О сайте")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if User.query.filter_by(email=request.form.get('email')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()

        # Log in and authenticate user after adding details to database.
        login_user(new_user)

        return redirect(url_for("secrets"))

    return render_template("register.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        # Find user by email entered.
        user = User.query.filter_by(email=email).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Check stored password hash against entered password hashed.
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('secrets'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/secrets')
@login_required
def secrets():
    # only by sending this page first will the client be connected to the socketio instance
    return current_app.send_static_file('index1.html')

# @app.route('/secrets')
# @login_required
# def secrets():
#     print(current_user.name)
#     return render_template("secrets.html", name=current_user.name)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/download')
@login_required
def download():
    return send_from_directory('static', filename="files/cheat_sheet.pdf")

# send email
@app.route("/contact")

def contact():
    return render_template("contact.html")


@app.route("/form-entry.html", methods=['POST'])
def receive_data():
    if request.method == 'POST':
        f_name = request.form['name']
        f_email = request.form['email']
        f_phone = request.form['phone']
        f_message = request.form['message']
        print(f_name)
        print(f_email)
        print(f_phone)
        print(f_message)
        send_email(f_name, f_email, f_phone, f_message)
        return "<h1>Successfully sent your message</h1>"





def send_email(name, email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"

    my_email = 'mail'
    password = 'mail'

    connection = smtplib.SMTP_SSL('smtp.mail.ru', 465)
    # connection.starttls() # шифрование письма
    connection.login(user=my_email, password=password)
    connection.sendmail(from_addr=my_email, to_addrs=email, msg=message)
    connection.close()
    print(email_message)




if __name__ == "__main__":
    app.run(debug=True)