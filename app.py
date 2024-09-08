from flask import Flask, redirect, url_for, render_template, session, request
from flask_sqlalchemy import SQLAlchemy
import datetime, pytz, re

# Flask and sqlalchemy config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config["SECRET_KEY"] = 'sessionsecretkey'

# Declare variables
malaysiaTZ = pytz.timezone("Asia/Kuala_Lumpur")
search = None

# Declare functions

def user_input_new_delete_old_schedule_decoder(schedule_input):
    global schedule_input_success_bool
    schedule_input_success_bool = False
    schedule_input = schedule_input.replace("\n", " ")

    dates = r"(January\s*\d{1,2},\s*\d{4})|(February\s*\d{1,2},\s*\d{4})|(March\s*\d{1,2},\s*\d{4})|(April\s*\d{1,2},\s*\d{4})|(May\s*\d{1,2},\s*\d{4})|(June\s*\d{1,2},\s*\d{4})|(July\s*\d{1,2},\s*\d{4})|(August\s*\d{1,2},\s*\d{4})|(September\s*\d{1,2},\s*\d{4})|(October\s*\d{1,2},\s*\d{4})|(November\s*\d{1,2},\s*\d{4})|(December\s*\d{1,2},\s*\d{4})"
    times = r"(\d{1,2}:\d{2}[AaPp][Mm])\s*-\s*(\d{1,2}:\d{2}[AaPp][Mm])\s*([A-Za-z]{4}\d{4})\s*:\s*([A-Za-z]*\d*)\s*-\s*\w*\s*\((\w*)\)"
    # regex string to find in the input. 

    # months = string to match the dates
    # group(1) = ([month] [day], [year])

    # times = string to match the dates
    # group(1) = ([start time][am/pm])
    # group(2) = ([end time][am/pm])
    # group(3) = ([room name])
    # group(4) = ([subject code])
    # group(5) = ([class section])


    pattern_date = re.compile(dates)
    pattern_time = re.compile(times)
    try:
        first_occurence_room_name = pattern_time.search(schedule_input).group(3)
    except:
        first_occurence_room_name = None
    with app.app_context():
        search_results = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_id = first_occurence_room_name)).all()
        for i in range(len(search_results)):
            for ii in range(len(search_results[i])):
                db.session.delete(search_results[i][ii])
                db.session.commit()

    dates_list = []
    for i in pattern_date.finditer(schedule_input):# puts match objects into a list, so i can count and call through index
        dates_list.append(i)

    for date_iter in range(len(dates_list)): # iterates through dates
        if date_iter < len(dates_list) - 1: # selects text from current date till the next date, so we know which time belongs to which date
            schedule_day = schedule_input[dates_list[date_iter].end():dates_list[date_iter+1].start()]
        elif date_iter == len(dates_list) - 1: # to fix list out of bounds
            schedule_day = schedule_input[dates_list[date_iter].end():]
        
        for time_iter in pattern_time.finditer(schedule_day):
            if time_iter.group(3) == first_occurence_room_name: # Verifies that all the room names match the first occurence, otherwise something is wrong with the input and it is discarded
                class_start = f"{dates_list[date_iter].group(0)} {time_iter.group(1)}"
                class_end = f"{dates_list[date_iter].group(0)} {time_iter.group(2)}"

                epoch_class_start = malaysiaTZ.localize(datetime.datetime.strptime(class_start, "%B %d, %Y %I:%M%p")).timestamp() # taking the sections from the strings and sorting into their values
                epoch_class_end = malaysiaTZ.localize(datetime.datetime.strptime(class_end, "%B %d, %Y %I:%M%p")).timestamp()
                fci_room_id = time_iter.group(3)
                class_subject_code = time_iter.group(4)
                class_section = time_iter.group(5)
                incoming_to_DB = room_availability_schedule(fci_room_id = fci_room_id, epoch_class_start = epoch_class_start, epoch_class_end = epoch_class_end, class_subject_code = class_subject_code, class_section = class_section)
                schedule_input_success_bool = True

                with app.app_context():
                    db.session.add(incoming_to_DB)
                    db.session.commit()

def room_status_func(room_status):
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
    return room_status, room_status_modifier

# Database for block, floor and number of rooms.
class fci_room(db.Model):
    __tablename__ = "fci_room"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    room_name = db.Column(db.String(50), nullable=False )
    room_block = db.Column(db.String(1), nullable=False)
    room_floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    room_status = db.Column(db.Integer, nullable=False)
    room_classes_schedule = db.relationship("room_availability_schedule", backref="fci_room")
    room_name_aliases = db.relationship("room_aliases", backref="fci_room")
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
    fci_room_id = db.Column(db.Integer, db.ForeignKey("fci_room.id"), nullable=False)
    epoch_class_start = db.Column(db.Float, nullable=False)
    epoch_class_end = db.Column(db.Float, nullable=False)
    class_subject_code = db.Column(db.String(50))
    class_section = db.Column(db.String(50))
    persistence_weeks = db.Column(db.Integer, nullable=False)
    input_from_scheduleORcustomORbutton = db.Column(db.String(50), nullable=False)
    def __repr__(self, id, fci_room_id, epoch_class_start, epoch_class_end, class_subject_code, class_section, persistence_weeks, input_from_scheduleORcustomORbutton):
        self.id = id
        self.fci_room_id = fci_room_id
        self.epoch_class_start = epoch_class_start
        self.epoch_class_end = epoch_class_end
        self.class_subject_code = class_subject_code
        self.class_section = class_section
        persistence_weeks = persistence_weeks
        input_from_scheduleORcustomORbutton = input_from_scheduleORcustomORbutton
    
    

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

    # Identify which form is input
    if request.method == "POST":
        try:
            request.form["search"]
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
        try:
            request.form["room_status"]
            room_status = int(request.form["room_status"])
            if (int(room.room_status) < 5) and (room_status > 0):
                room.room_status = int(room.room_status) + int(room_status)
            elif (int(room.room_status) > -5) and (room_status < 0):
                room.room_status = int(room.room_status) + int(room_status)
            db.session.commit()
        except:
            pass

    # TODO: change this to advanced system. this is the upvote/downvote room availability system
    room_status, room_status_modifier = room_status_func(room_status=room.room_status)

    current_time = datetime.datetime.now(tz=malaysiaTZ) #find current time

    # room availability schedule
    room_obj = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_id = room.room_name)).all()
    schedule_list = []
    for i in range(len(room_obj)):
        for ii in range(len(room_obj[i])):
            check_class_start = datetime.datetime.fromtimestamp(room_obj[i][ii].epoch_class_start).astimezone(malaysiaTZ)
            timeDelta = current_time - check_class_start
            if timeDelta.days > (room_obj[i][ii].persistence_weeks)*7:
                db.session.delete(room_obj[i][ii])
                db.session.commit()
            else:
                schedule_list.append(room_obj[i][ii])
    
    # current class checker
    class_in_session = None
    for schedule_single in schedule_list:
        check_class_start = datetime.datetime.fromtimestamp(schedule_single.epoch_class_start).astimezone(malaysiaTZ)
        check_class_end = datetime.datetime.fromtimestamp(schedule_single.epoch_class_end).astimezone(malaysiaTZ)
        if check_class_start.weekday() == current_time.weekday():
            if check_class_start.hour <= current_time.hour < check_class_end.hour:
                class_in_session = schedule_single
                current_class_start = check_class_start
                current_class_end = check_class_end
                break
    if class_in_session:
        return render_template("roompage.html", room_name = room.room_name, room_block = room.room_block, room_floor = room.room_floor, room_number = room.room_number, room_status = room_status, room_status_modifier = room_status_modifier, schedule_list = schedule_list, class_in_session = class_in_session, current_class_start = current_class_start, current_class_end = current_class_end)
    else: 
        return render_template("roompage.html", room_name = room.room_name, room_block = room.room_block, room_floor = room.room_floor, room_number = room.room_number, room_status = room_status, room_status_modifier = room_status_modifier, schedule_list = schedule_list)

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

@app.route("/schedule_input", methods=["GET", "POST"])
def schedule_input():
    if request.method == "POST":
        try:
            request.form["search"]
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
            
        
        try:
            request.form["schedule_input"]
            schedule_input = str(request.form["schedule_input"])
            user_input_new_delete_old_schedule_decoder(schedule_input)
            if schedule_input_success_bool:
                pass # Show popup that "Input has entered the database" or give user a reward, etc.
            return redirect("/schedule_input")
        except:
            pass

    return render_template("schedule_input.html")

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