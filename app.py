from flask import Flask, redirect, url_for, render_template, session, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime, pytz, re
from werkzeug.security import generate_password_hash, check_password_hash

# Flask and SQLAlchemy configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app, session_options={"autoflush": False})
app.config["SECRET_KEY"] = 'sessionsecretkey'

# Timezone setup
malaysiaTZ = pytz.timezone("Asia/Kuala_Lumpur")

def current_time():
    return datetime.datetime.now(tz=malaysiaTZ)

# Database models

class fci_room(db.Model):
    __tablename__ = "fci_room"
    room_name = db.Column(db.String(50), primary_key=True,  nullable=False)
    room_block = db.Column(db.String(1), nullable=False)
    room_floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    room_classes_schedule = db.relationship("room_availability_schedule", backref="fci_room", lazy=True)
    room_name_aliases = db.relationship("room_aliases", backref="fci_room", lazy=True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    popup = db.Column(db.String(50))

    def __repr__(self):
        return f'<Room {self.room_name}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Routes and application logic

@app.route("/")
def redirect_home():
    return redirect("/map/0")

# Account routes (Login, Signup, Change Password, Delete Account)

@app.route("/account/", methods=["GET", "POST"])
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("account.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        # Check if the user exists and verify the password
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect("/")
        else:
            return render_template('login.html', error="Invalid email or password.")

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Password validation
        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'[0-9]', password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return render_template('signup.html', error="Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.")

        # Check if the username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                return render_template('signup.html', error="Username already registered.", login_link=True)
            elif existing_user.email == email:
                return render_template('signup.html', error="Email address already registered.", login_link=True)

        # Hash the password using pbkdf2:sha256
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('signup_success'))

    return render_template('signup.html')

@app.route('/signup_success')
def signup_success():
    return render_template('signup_success.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = User.query.get(session['user_id'])

        if not check_password_hash(user.password, current_password):
            return render_template('change_password.html', error="Current password is incorrect.")

        if len(new_password) < 8 or not re.search(r'[A-Z]', new_password) or not re.search(r'[a-z]', new_password) or not re.search(r'[0-9]', new_password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            return render_template('change_password.html', error="New password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.")

        # Check if new password and confirmation match
        if new_password != confirm_password:
            return render_template('change_password.html', error="New password and confirmation password do not match.")

        # Hash the new password before storing it in the database
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        user.password = hashed_password
        db.session.commit()

        # Redirect to the login page after a successful password change
        return redirect(url_for('login'))

    return render_template('change_password.html')

@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Find the user in the database using their session ID
        user = User.query.get(session['user_id'])

        # Delete the user from the database
        db.session.delete(user)
        db.session.commit()

        # Clear the session to log the user out
        session.pop('user_id', None)

        # Redirect to the signup page after account deletion
        return redirect(url_for('signup'))

    # Render the delete account confirmation page
    return render_template('delete_account.html')

# Additional routes (e.g., /map, /roompage, /search) ...

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
