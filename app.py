from flask import Flask, redirect, url_for, render_template, session, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime, pytz, re
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Flask and sqlalchemy config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app, session_options={"autoflush": False})
app.config["SECRET_KEY"] = 'sessionsecretkey'

# Declare variables
malaysiaTZ = pytz.timezone("Asia/Kuala_Lumpur")

def current_time():
    return datetime.datetime.now(tz=malaysiaTZ)

# Declare functions

def user_input_new_delete_old_schedule_decoder(schedule_input):
    global schedule_input_success_bool
    schedule_input_success_bool = False
    schedule_input = schedule_input.replace("\n", " ")

    dates = r"(January\s*\d{1,2},\s*\d{4})|(February\s*\d{1,2},\s*\d{4})|(March\s*\d{1,2},\s*\d{4})|(April\s*\d{1,2},\s*\d{4})|(May\s*\d{1,2},\s*\d{4})|(June\s*\d{1,2},\s*\d{4})|(July\s*\d{1,2},\s*\d{4})|(August\s*\d{1,2},\s*\d{4})|(September\s*\d{1,2},\s*\d{4})|(October\s*\d{1,2},\s*\d{4})|(November\s*\d{1,2},\s*\d{4})|(December\s*\d{1,2},\s*\d{4})"
    times = r"(\d{1,2}:\d{2}[AaPp][Mm])\s*-\s*(\d{1,2}:\d{2}[AaPp][Mm])\s*([A-Z]{4}\d{4})\s*:\s*([A-Z]*\d*)\s*-\s*(\w*)\s*\((\w*)\)"
    # regex string to find in the input. 

    # months = string to match the dates
    # group(1) = ([month] [day], [year])

    # times = string to match the dates
    # group(1) = ([start time][am/pm])
    # group(2) = ([end time][am/pm])
    # group(3) = ([room name])
    # group(4) = ([subject code])
    # group(5) = ([description])
    # group(6) = ([class section])

    pattern_date = re.compile(dates)
    pattern_time = re.compile(times)
    try:
        first_occurence_room_name = pattern_time.search(schedule_input).group(3) # gets room name, to weed out old outdated schedules to be deleted
    except:
        first_occurence_room_name = None
    with app.app_context():
        search_results = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_name = first_occurence_room_name, input_from_scheduleORcustomORbutton = "schedule")).scalars()
        for i in search_results:
            db.session.delete(i)
            db.session.commit()

    dates_list = [] # first we find the dates, eg. September 6, 2024
    for i in pattern_date.finditer(schedule_input):# puts match objects into a list, so i can count and call through index
        dates_list.append(i)

    for date_iter in range(len(dates_list)): # iterates through dates
        if date_iter < len(dates_list) - 1: # selects text from current date till the next date, so we know which time belongs to which date
            schedule_day = schedule_input[dates_list[date_iter].end():dates_list[date_iter+1].start()]
        elif date_iter == len(dates_list) - 1: # to fix list out of bounds
            schedule_day = schedule_input[dates_list[date_iter].end():]
        
        for time_iter in pattern_time.finditer(schedule_day): # finds the time values of class in between the dates
            if time_iter.group(3) == first_occurence_room_name: # Verifies that all the room names match the first occurence, otherwise something is wrong with the input and it is discarded
                class_start = f"{dates_list[date_iter].group(0)} {time_iter.group(1)}"
                class_end = f"{dates_list[date_iter].group(0)} {time_iter.group(2)}"

                epoch_start = float(malaysiaTZ.localize(datetime.datetime.strptime(class_start, "%B %d, %Y %I:%M%p")).timestamp()) # taking the sections from the strings and sorting into their values
                epoch_end = float(malaysiaTZ.localize(datetime.datetime.strptime(class_end, "%B %d, %Y %I:%M%p")).timestamp())
                fci_room_name = time_iter.group(3)
                class_subject_code = time_iter.group(4)# all these are assigning values to variables, to be later placed in a class and commited to the database
                class_section = time_iter.group(6)
                schedule_description = time_iter.group(5)
                persistence_weeks = 6
                input_from_scheduleORcustomORbutton = "schedule"
                availability_weightage_value = 10
                incoming_to_DB = room_availability_schedule(fci_room_name = fci_room_name, epoch_start = epoch_start, epoch_end = epoch_end, class_subject_code = class_subject_code, class_section = class_section, schedule_description = schedule_description, persistence_weeks = persistence_weeks, input_from_scheduleORcustomORbutton = input_from_scheduleORcustomORbutton, availability_weightage_value = availability_weightage_value)
                schedule_input_success_bool = True # used to check if schedule input is successful, for rewards or score etc.

                with app.app_context():
                    db.session.add(incoming_to_DB)
                    db.session.commit()

def in_session_weightage_total(room_name):
    current_time_single = current_time()
    query = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_name = room_name)).all()
    weightage_total = 0
    for i in range(len(query)):
        for ii in range(len(query[i])):
            if (query[i][ii].input_from_scheduleORcustomORbutton == "schedule") and (int(query[i][ii].datetime_start(strftime="%H%M%S%f")) < int(current_time_single.strftime("%H%M%S%f")) <= int(query[i][ii].datetime_end(strftime="%H%M%S%f"))):
                weightage_total += int(query[i][ii].availability_weightage_value)
            elif float(query[i][ii].epoch_start) < float(current_time_single.timestamp()) <= float(query[i][ii].epoch_end):
                weightage_total += int(query[i][ii].availability_weightage_value)
    return weightage_total

# def room_status_func(room_status): # TODO: delete this feature
#     if abs(room_status) == 0:
#         room_status_modifier = ""
#     if 1 <= abs(room_status) <= 2:
#         room_status_modifier = "Likely"
#     elif 3 <= abs(room_status) <= 4:
#         room_status_modifier = "Probably"
#     elif abs(room_status) == 5:
#         room_status_modifier = "Definitely"
    
#     if room_status == 0:
#         room_status = "Unknown"
#     elif room_status < 0:
#         room_status = "Empty"
#     elif room_status > 0:
#         room_status = "Occupied"
#     return room_status, room_status_modifier

# Database for block, floor and number of rooms.
class fci_room(db.Model):
    __tablename__ = "fci_room"
    # id = db.Column(db.Integer,nullable=False) TODO Delete
    room_name = db.Column(db.String(50), primary_key=True,  nullable=False )
    room_block = db.Column(db.String(1), nullable=False)
    room_floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    room_classes_schedule = db.relationship("room_availability_schedule", backref="fci_room", lazy=True)
    room_name_aliases = db.relationship("room_aliases", backref="fci_room", lazy=True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    popup = db.Column(db.String(50)) # nullable=False
    def __repr__(self, room_name, room_block, room_floor, room_number):
        # self.id = id TODO Delete
        self.room_name = room_name
        self.room_block = room_block
        self.room_floor = room_floor
        self.room_number = room_number

# Database table for room availability, from CLiC schedule
class room_availability_schedule(db.Model):
    __tablename__ = "room_availability_schedule"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    fci_room_name = db.Column(db.String(50), db.ForeignKey("fci_room.room_name"), nullable=False)
    epoch_start = db.Column(db.Float, nullable=False)
    epoch_end = db.Column(db.Float, nullable=False)
    class_subject_code = db.Column(db.String(50))
    class_section = db.Column(db.String(50))
    schedule_description = db.Column(db.String(200))
    persistence_weeks = db.Column(db.Integer, nullable=False) # must set automatically, allow user choice from input
    input_from_scheduleORcustomORbutton = db.Column(db.String(50), nullable=False) # must set automatically
    availability_weightage_value = db.Column(db.Integer, nullable=False)

    def datetime_start(self, strftime=None):
        if strftime:
            return datetime.datetime.fromtimestamp(float(self.epoch_start)).astimezone(malaysiaTZ).strftime(strftime)
        else:
            return datetime.datetime.fromtimestamp(float(self.epoch_start)).astimezone(malaysiaTZ)
    
    def datetime_end(self, strftime=None):
        if strftime:
            return datetime.datetime.fromtimestamp(float(self.epoch_end)).astimezone(malaysiaTZ).strftime(strftime)
        else:
            return datetime.datetime.fromtimestamp(float(self.epoch_end)).astimezone(malaysiaTZ)

    def __repr__(self, id, fci_room_name, epoch_start, epoch_end, class_subject_code, class_section, schedule_description, persistence_weeks, input_from_scheduleORcustomORbutton, availability_weightage_value):
        self.id = id
        self.fci_room_name = fci_room_name
        self.epoch_start = epoch_start
        self.epoch_end = epoch_end
        self.class_subject_code = class_subject_code
        self.class_section = class_section
        self.schedule_description = schedule_description
        self.persistence_weeks = persistence_weeks
        self.input_from_scheduleORcustomORbutton = input_from_scheduleORcustomORbutton
        self.availability_weightage_value = availability_weightage_value

class room_aliases(db.Model):
    __tablename__ = "room_aliases"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    room_name_aliases = db.Column(db.String(50), nullable=False)
    fci_room_name = db.Column(db.String(50), db.ForeignKey("fci_room.room_name"), nullable=False)

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

@app.route("/get_markers/<floor>/<room_name>")
def get_markers(floor, room_name="None"):
    if room_name!="None":
        query = db.session.execute(db.select(fci_room).filter_by(room_name = room_name)).scalars()
    else: query = db.session.execute(db.select(fci_room).filter_by(room_floor = floor)).scalars()
    markers = []
    for i in query:
            if i.lat and i.lng:
                markers.append({"lat":float(i.lat), "lng":float(i.lng), "popup":f"<a href=\"/roompage/{i.room_name}\">{i.room_name}</a></br>{i.popup}"})
    return jsonify(markers)

@app.route("/map/<floor>/", methods=["GET", "POST"])
def home(floor):
    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
    search_suggestion = []
    for i in db.session.execute(db.select(fci_room)).scalars():
        search_suggestion.append(i.room_name)
    for i in db.session.execute(db.select(room_aliases)).scalars():
        search_suggestion.append(i.room_name_aliases)
    session["search_suggestion"] = search_suggestion
    return render_template("index.html", ActivePage="index", search_suggestion = session["search_suggestion"], ActiveFloor = floor)

@app.route("/roompage/<room_name>", methods=["GET", "POST"])
def room_page(room_name):
    room = db.session.execute(db.select(fci_room).filter_by(room_name = room_name)).scalar()
    if room:
        pass
    else:
        return render_template("search.html")
    current_time_single = current_time()

    # Identify which form is input
    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass

        try:
            room_status = request.form["room_status"]
            fci_room_name = room_name
            epoch_start = current_time_single.timestamp()
            epoch_end = (current_time_single + datetime.timedelta(hours=1)).timestamp()
            persistence_weeks = 1
            input_from_scheduleORcustomORbutton = "button"
            availability_weightage_value = int(room_status)
            incoming_to_DB = room_availability_schedule(fci_room_name = fci_room_name, epoch_start = epoch_start, epoch_end = epoch_end, persistence_weeks = persistence_weeks, input_from_scheduleORcustomORbutton = input_from_scheduleORcustomORbutton, availability_weightage_value = availability_weightage_value)
            with app.app_context():
                db.session.add(incoming_to_DB)
                db.session.commit()
        except:
            pass

    # --------------------------------------------------------clic schedule
    # room availability schedule
    room_obj = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_name = room.room_name, input_from_scheduleORcustomORbutton = "schedule").order_by(room_availability_schedule.epoch_start)).scalars()
    class_schedule_list = []
    for i in room_obj:
        check_class_start = i.datetime_start()
        timeDelta = current_time_single - check_class_start
        if timeDelta.days >= (i.persistence_weeks)*7: # Deletes old inputs that are more than the persistence time/exceeds the limit
            db.session.delete(i)
            db.session.commit()
        else:
            class_schedule_list.append(i)
    
    # current class checker, checks if class in in session
    class_in_session_list = []
    for schedule_single in class_schedule_list:
        if schedule_single.datetime_start().weekday() == current_time_single.weekday():
            if int(schedule_single.datetime_start(strftime="%H%M%S%f")) < int(current_time_single.strftime("%H%M%S%f")) <= int(schedule_single.datetime_end(strftime="%H%M%S%f")):
                class_in_session_list.append(schedule_single)

    #-----------------------------------------------------custom schedule
    room_obj = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_name = room.room_name, input_from_scheduleORcustomORbutton = "custom").order_by(room_availability_schedule.epoch_start)).scalars()
    custom_schedule_list = []
    for i in room_obj:
        check_class_start = i.datetime_start()
        timeDelta = current_time_single - check_class_start
        if timeDelta.days >= (i.persistence_weeks)*7: # Deletes old inputs that are more than the persistence time/exceeds the limit
            db.session.delete(i)
            db.session.commit()
        else:
            custom_schedule_list.append(i)
    
    custom_in_session_list = []
    for custom_single in custom_schedule_list:
        if custom_single.datetime_start().weekday() == current_time_single.weekday():
            if float(custom_single.epoch_start) < float(current_time_single.timestamp()) <= float(custom_single.epoch_end):
                custom_in_session_list.append(custom_single)

    # class_schedule_list = list of row objects of CLiC MMUclass
    # class_in_session = single row object of CLiC MMUclass which is currently going on in this room. Returns None if no class ongoing
    # TODO room_status and room_status_modifier = to be deleted/remade
    return render_template("roompage.html", search_suggestion = session["search_suggestion"], room = room, class_schedule_list = class_schedule_list, class_in_session_list = class_in_session_list, current_time_single = current_time_single, custom_schedule_list = custom_schedule_list, custom_in_session_list = custom_in_session_list)

@app.route("/account/", methods=["GET", "POST"])
def account():
    return redirect("/signup")

@app.route("/search/<search>", methods=["GET", "POST"])
def search(search):
    search = str(search)
    session["search"] = search
    room_name_results = db.session.execute(db.select(fci_room).filter(fci_room.room_name.icontains(search))).scalars()
    room_name_results_list = []
    for i in room_name_results:
        room_name_results_list.append(i)
    aliases_results = db.session.execute(db.select(room_aliases).filter(room_aliases.room_name_aliases.icontains(search))).scalars()
    aliases_results_list = []
    for i in aliases_results:
        aliases_results_list.append(i)

    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
    return render_template("search.html", ActivePage = "search", search_suggestion = session["search_suggestion"], search = session["search"], room_name_results_list = room_name_results_list, aliases_results_list = aliases_results_list )

@app.route("/schedule_input/", methods=["GET", "POST"])
def schedule_input():
    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
            
        try:
            schedule_input = str(request.form["schedule_input"])
            user_input_new_delete_old_schedule_decoder(schedule_input)
            if schedule_input_success_bool:
                pass # Show popup that "Input has entered the database" or give user a reward, etc.
            return redirect("/schedule_input")
        except:
            pass

        try:
            custom_schedule_search_room = request.form["custom_schedule_search_room"]
            custom_schedule_datetime = request.form["custom_schedule_datetime"]
            custom_schedule_hours = request.form["custom_schedule_hours"]
            custom_schedule_textarea = request.form["custom_schedule_textarea"]
            custom_room_status = request.form["custom_room_status"]
            custom_schedule_datetime_start = malaysiaTZ.localize(datetime.datetime.strptime(custom_schedule_datetime, "%Y-%m-%dT%H:%M"))
            custom_schedule_datetime_end = custom_schedule_datetime_start + datetime.timedelta(hours=int(custom_schedule_hours))

            room_name_re_check = r"(^[A-Z]{4}\d{4}$)"
            room_name_pattern = re.compile(room_name_re_check)
            if room_name_pattern.search(custom_schedule_search_room):
                fci_room_name = custom_schedule_search_room
                epoch_start = float(custom_schedule_datetime_start.timestamp())
                epoch_end = float(custom_schedule_datetime_end.timestamp())
                schedule_description = custom_schedule_textarea
                persistence_weeks = 1
                input_from_scheduleORcustomORbutton = "custom"
                availability_weightage_value = int(custom_room_status)
                
                incoming_to_DB = room_availability_schedule(fci_room_name = fci_room_name, epoch_start = epoch_start, epoch_end = epoch_end, class_subject_code = None, class_section = None, schedule_description = schedule_description, persistence_weeks = persistence_weeks, input_from_scheduleORcustomORbutton = input_from_scheduleORcustomORbutton, availability_weightage_value = availability_weightage_value)
                with app.app_context():
                    db.session.add(incoming_to_DB)
                    db.session.commit()
        except:
            pass

    return render_template("schedule_input.html", ActivePage="schedule_input", search_suggestion = session["search_suggestion"], current_time=current_time())

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

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Change password route
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

        # Redirect to the login page after successful password change
        return redirect(url_for('login'))

    return render_template('change_password.html')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)