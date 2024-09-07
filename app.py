from flask import Flask, redirect, url_for, render_template, session, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config["SECRET_KEY"] = 'sessionsecretkey'
search = None

# Database for block, floor and number of rooms.
class fci_room(db.Model):
    __tablename__ = "fci_room"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    room_name = db.Column(db.String(50), nullable=False )
    room_block = db.Column(db.String(1), nullable=False)
    room_floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    room_status = db.Column(db.Integer, nullable=False)
    def __repr__(self, id, room_name, room_block, room_floor, room_number, room_status):
        self.id = id
        self.room_name = room_name
        self.room_block = room_block
        self.room_floor = room_floor
        self.room_number = room_number
        self.room_status = room_status

# Database table for room availability, from CLiC schedule
class room_availability_schedule(db.Model):
    __tablename__ = "room_availability_schedule"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    room_name = db.Column(db.String(50), nullable=False)
    date_M_D_Y = db.Column(db.String(50), nullable=False)
    weekday_iso = room_floor = db.Column(db.Integer, nullable=False)
    time_class_start = db.Column(db.String(50), nullable=False)
    time_class_end = db.Column(db.String(50), nullable=False)
    class_subject_code = db.Column(db.String(50), nullable=False)
    class_section = db.Column(db.String(50), nullable=False)
    def __repr__(self, id, room_name, date_M_D_Y, time_class_start, time_class_end, class_subject_code, class_section):
        self.id = id
        self.room_name = room_name
        self.date_M_D_Y = date_M_D_Y
        self.time_class_start = time_class_start
        self.time_class_end = time_class_end
        self.class_subject_code = class_subject_code
        self.class_section = class_section
    
    

class room_aliases(db.Model):
    __tablename__ = "room_aliases"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    fci_room_id = db.Column(db.Integer, db.ForeignKey("fci_room.id"), nullable=False)
    room_name_aliases = db.Column(db.String(50), nullable=False)

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
    return render_template("index.html", ActivePage="index", ActiveFloor = floor)

@app.route("/roompage/<room_name>", methods=["GET", "POST"])
def room_page(room_name):
    room = db.session.execute(db.select(fci_room).filter_by(room_name = room_name)).scalar()
    search = None
    if request.method == "POST":
        try:
            request.form["search"]
        except:
            pass
        else:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        try:
            request.form["room_status"]
        except:
            pass
        else:
            room_status = int(request.form["room_status"])
            if (int(room.room_status) < 5) and (room_status > 0):
                room.room_status = int(room.room_status) + int(room_status)
            elif (int(room.room_status) > -5) and (room_status < 0):
                room.room_status = int(room.room_status) + int(room_status)
            db.session.commit()

    room_status = room.room_status
    if abs(room_status) == 0:
        room_status_modifier = ""
    if 1 <= abs(room_status) <= 2:
        room_status_modifier = "Likely"
    elif 3 <= abs(room_status) <= 4:
        room_status_modifier = "Probably"
    elif abs(room_status) == 5:
        room_status_modifier = "Definitely"
    
    if room_status == 0:
        room_status = "Unknown"
    elif room_status > 0:
        room_status = "Empty"
    elif room_status < 0:
        room_status = "Occupied"
    
    return render_template("roompage.html", room_name = room.room_name, room_block = room.room_block, room_floor = room.room_floor, room_number = room.room_number, room_status = room_status, room_status_modifier = room_status_modifier)
    

@app.route("/account/", methods=["GET", "POST"])
def account():
    search = None
    if request.method == "POST":
        search = request.form["search"]
        if search:
            return redirect(f"/search/{search}")
    return render_template("account.html", ActivePage = "account")

@app.route("/search/<search>", methods=["GET", "POST"])
def search(search):
    session["search"] = search
    search_results = db.session.execute(db.select(fci_room).filter_by(room_name = search)).all()

    results_list = []
    for i in range(len(search_results)):
        for ii in range(len(search_results[i])):
            results_list.append(search_results[i][ii].room_name)
    
    if request.method == "POST":
        search = request.form["search"]
        if search:
            return redirect(f"/search/{search}")
    return render_template("search.html", ActivePage = "search", search = session["search"], results_list = results_list)

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






if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)