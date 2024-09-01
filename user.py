import re
from flask import Flask, request, redirect, url_for, render_template, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required to use sessions

# Configuring the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initializing the database
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

@app.route('/signup_success')
def signup_success():
    return render_template('signup_success.html')

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

        new_user = User(username=username, email=email, password=password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('signup_success'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['user_id'] = user.id
            return "Logged in successfully!"
        else:
            return render_template('login.html', error="Invalid email or password.")

    return render_template('login.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create the database and the tables
    app.run(debug=True, port=5001)

