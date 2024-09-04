from flask import Flask, redirect, url_for, render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config["SECRET_KEY"] = 'sessionsecretkey'
search = None

# Database for block, floor, and number of rooms.
class fci_room(db.Model):
    __tablename__ = "fci_room"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    room_code = db.Column(db.String(50), nullable=False)
    room_block = db.Column(db.String(1), nullable=False)
    room_floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    def __repr__(self, id, room_code, room_block, room_floor, room_number):
        self.id = id
        self.room_code = room_code
        self.room_block = room_block
        self.room_floor = room_floor
        self.room_number = room_number

# Database for user info
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# -------------------------------------------------------

@app.route("/")
def redirect_home():
    return redirect("/map/0")

@app.route("/map/<floor>/", methods=["GET", "POST"])
def home(floor):
    search = None
    if request.method == "POST":
        search = request.form["search"]
        if search:
            return redirect(f"/search/{search}")
    return render_template("index.html", ActivePage="index", ActiveFloor=floor)

@app.route("/roompage/<room_code>", methods=["GET", "POST"])
def room_page(room_code):
    room = db.session.execute(db.select(fci_room).filter_by(room_code=room_code)).scalar()
    search = None
    if request.method == "POST":
        search = request.form["search"]
        if search:
            return redirect(f"/search/{search}")
    return render_template("roompage.html", room_code=room.room_code, room_block=room.room_block, room_floor=room.room_floor, room_number=room.room_number)

@app.route("/account/", methods=["GET", "POST"])
def account():
    return redirect("/signup")
    # return render_template("account.html", ActivePage="account")

@app.route("/search/<search>", methods=["GET", "POST"])
def search(search):
    session["search"] = search
    search_results = db.session.execute(db.select(fci_room).filter_by(room_code=search)).all()

    results_list = []
    for i in range(len(search_results)):
        for ii in range(len(search_results[i])):
            results_list.append(search_results[i][ii].room_code)

    if request.method == "POST":
        search = request.form["search"]
        if search:
            return redirect(f"/search/{search}")
    return render_template("search.html", ActivePage="search", search=session["search"], results_list=results_list)

# -------------------------------------------------------

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

        # Hash the password using pbkdf2:sha256
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('signup_success'))

    return render_template('signup.html')

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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
