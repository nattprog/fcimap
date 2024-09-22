from flask import Flask, redirect, url_for, render_template, session, request, jsonify, flash
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
    schedule_input = schedule_input.replace("\n", " ")

    dates = r"(January\s*\d{1,2},\s*\d{4})|(February\s*\d{1,2},\s*\d{4})|(March\s*\d{1,2},\s*\d{4})|(April\s*\d{1,2},\s*\d{4})|(May\s*\d{1,2},\s*\d{4})|(June\s*\d{1,2},\s*\d{4})|(July\s*\d{1,2},\s*\d{4})|(August\s*\d{1,2},\s*\d{4})|(September\s*\d{1,2},\s*\d{4})|(October\s*\d{1,2},\s*\d{4})|(November\s*\d{1,2},\s*\d{4})|(December\s*\d{1,2},\s*\d{4})"
    times_schedule = r"(\d{1,2}:\d{2}[AaPp][Mm])\s*-\s*(\d{1,2}:\d{2}[AaPp][Mm])\s*([A-Z]{4}\d{4})\s*:\s*([A-Z]*\d*)\s*-\s*(\w*)\s*\((\w*)\)"
    times_custom = r"(\d{1,2}:\d{2}[AaPp][Mm])\s*-\s*(\d{1,2}:\d{2}[AaPp][Mm])\s*([A-Z]{4}\d{4})\s*:\s*(Class/Tutorial|Club\sActivity/Event|Examination|Final\sExam|External\sEvent|Meeting/Discussion|Others|Presentation|Training/Conference)"
    # regex string to find in the input. 

    # months = string to match the dates
    # group(1) = ([month] [day], [year])

    # times_schedule OR times_custom = string to match the dates
    # group(1) = ([start time][am/pm])
    # group(2) = ([end time][am/pm])
    # group(3) = ([room name]) 
    # group(4) = ([subject code]) OR ([description])
    # group(5) = ([description])
    # group(6) = ([class section]) OR None

    pattern_date = re.compile(dates)
    pattern_time_schedule = re.compile(times_schedule)
    pattern_times_custom = re.compile(times_custom)
    if (pattern_date.search(schedule_input) and pattern_time_schedule.search(schedule_input)) or (pattern_date.search(schedule_input) and pattern_times_custom.search(schedule_input)):# OR checks validity incase there is only schedule booking
        first_occurence_room_name = pattern_time_schedule.search(schedule_input).group(3) # gets room name, to weed out old outdated schedules to be deleted
        if pattern_time_schedule.search(schedule_input):
            first_occurence_datetime_start = malaysiaTZ.localize(datetime.datetime.strptime(f"{pattern_date.search(schedule_input).group(0)} {pattern_time_schedule.search(schedule_input).group(1)}", "%B %d, %Y %I:%M%p"))
        elif pattern_times_custom.search(schedule_input):
            first_occurence_datetime_start = malaysiaTZ.localize(datetime.datetime.strptime(f"{pattern_date.search(schedule_input).group(0)} {pattern_times_custom.search(schedule_input).group(1)}", "%B %d, %Y %I:%M%p"))
        if (((first_occurence_datetime_start - current_time()).days)//7) <= 12: # checks and fails if mass add is more than 12 weeks in the future
            with app.app_context():
                search_results = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_name = first_occurence_room_name, input_from_scheduleORcustomORbutton = "schedule")).scalars()
                for i in search_results:
                    local_obj = db.session.merge(i)
                    db.session.delete(local_obj)
                    db.session.commit() # deletes outdated schedule data
        else:
            first_occurence_datetime_start = None
    else:
        first_occurence_room_name = None
    
# I pity every poor soul who has to set eyes on this peak logik shit
    if first_occurence_room_name and first_occurence_datetime_start: # checks if room name is valid, and first occurence start date is valid (exists and not exceeding 12 weeks in future)
        if cooldown_checker_return_True_if_accept(first_occurence_room_name, input_type="schedule",seconds=10):
            success_bool = False
            dates_list = [] # first we find the dates, eg. September 6, 2024
            for i in pattern_date.finditer(schedule_input):# puts match objects into a list, so i can count and call through index
                dates_list.append(i)
            for date_iter in range(len(dates_list)): # iterates through dates
                if date_iter < len(dates_list) - 1: # selects text from current date till the next date, so we know which time belongs to which date
                    schedule_day = schedule_input[dates_list[date_iter].end():dates_list[date_iter+1].start()]
                elif date_iter == len(dates_list) - 1: # to fix list out of bounds
                    schedule_day = schedule_input[dates_list[date_iter].end():]
                
                for time_iter in pattern_time_schedule.finditer(schedule_day): # finds the time values of class in between the dates
                    if time_iter.group(3) == first_occurence_room_name: # Verifies that all the room names match the first occurence, otherwise something is wrong with the input and it is discarded
                        class_start = f"{dates_list[date_iter].group(0)} {time_iter.group(1)}"
                        class_end = f"{dates_list[date_iter].group(0)} {time_iter.group(2)}"

                        epoch_start = float(malaysiaTZ.localize(datetime.datetime.strptime(class_start, "%B %d, %Y %I:%M%p")).timestamp()) # taking the sections from the strings and sorting into their values
                        epoch_end = float(malaysiaTZ.localize(datetime.datetime.strptime(class_end, "%B %d, %Y %I:%M%p")).timestamp())
                        fci_room_name = time_iter.group(3)
                        class_subject_code = time_iter.group(4)# all these are assigning values to variables, to be later placed in a class and commited to the database
                        class_section = time_iter.group(6)
                        schedule_description = time_iter.group(5)
                        persistence_weeks = 12
                        input_from_scheduleORcustomORbutton = "schedule"
                        availability_weightage_value = 10
                        incoming_to_DB = room_availability_schedule(fci_room_name = fci_room_name, epoch_start = epoch_start, epoch_end = epoch_end, class_subject_code = class_subject_code, class_section = class_section, schedule_description = schedule_description, persistence_weeks = persistence_weeks, input_from_scheduleORcustomORbutton = input_from_scheduleORcustomORbutton, availability_weightage_value = availability_weightage_value)
                        with app.app_context():
                            db.session.add(incoming_to_DB)
                            db.session.commit()
                            success_bool = True
                for time_iter in pattern_times_custom.finditer(schedule_day): # finds the time values of custom booking in between the dates
                    if time_iter.group(3) == first_occurence_room_name: # Verifies that all the room names match the first occurence, otherwise something is wrong with the input and it is discarded
                        class_start = f"{dates_list[date_iter].group(0)} {time_iter.group(1)}"
                        class_end = f"{dates_list[date_iter].group(0)} {time_iter.group(2)}"

                        epoch_start = float(malaysiaTZ.localize(datetime.datetime.strptime(class_start, "%B %d, %Y %I:%M%p")).timestamp()) # taking the sections from the strings and sorting into their values
                        epoch_end = float(malaysiaTZ.localize(datetime.datetime.strptime(class_end, "%B %d, %Y %I:%M%p")).timestamp())
                        fci_room_name = time_iter.group(3)
                        schedule_description = time_iter.group(4)
                        persistence_weeks = 0
                        input_from_scheduleORcustomORbutton = "CLiC Reservation" # TODO be replaced with user email
                        availability_weightage_value = 10
                        incoming_to_DB = room_availability_schedule(fci_room_name = fci_room_name, epoch_start = epoch_start, epoch_end = epoch_end, schedule_description = schedule_description, persistence_weeks = persistence_weeks, input_from_scheduleORcustomORbutton = input_from_scheduleORcustomORbutton, availability_weightage_value = availability_weightage_value)

                        with app.app_context():
                            db.session.add(incoming_to_DB)
                            db.session.commit()
                            success_bool = True
            success_fail_flash(success_bool)
    else:
        success_fail_flash(False)

def user_input_new_custom(): # the only reason this is up here is to clear up the website routes area
    custom_schedule_search_room = request.form["custom_schedule_search_room"] # gets data from form
    custom_schedule_datetime = request.form["custom_schedule_datetime"]
    custom_schedule_hours = request.form["custom_schedule_hours"]
    custom_schedule_textarea = request.form["custom_schedule_textarea"]
    custom_room_status = request.form["custom_room_status"]
    custom_schedule_datetime_start = malaysiaTZ.localize(datetime.datetime.strptime(custom_schedule_datetime, "%Y-%m-%dT%H:%M"))
    custom_schedule_datetime_end = custom_schedule_datetime_start + datetime.timedelta(hours=int(custom_schedule_hours))

    if db.session.execute(db.select(fci_room).filter_by(room_name = custom_schedule_search_room)).scalar(): # checks with database if room name is valid
        fci_room_name = custom_schedule_search_room
        epoch_start = float(custom_schedule_datetime_start.timestamp())
        epoch_end = float(custom_schedule_datetime_end.timestamp())
        schedule_description = custom_schedule_textarea
        persistence_weeks = 0
        input_from_scheduleORcustomORbutton = "custom" # TODO: change to user email or user id
        availability_weightage_value = int(custom_room_status)
        try: user_id = session["user_id"]
        except:
            user_id = None
        incoming_to_DB = room_availability_schedule(fci_room_name = fci_room_name, epoch_start = epoch_start, epoch_end = epoch_end, schedule_description = schedule_description, persistence_weeks = persistence_weeks, input_from_scheduleORcustomORbutton = input_from_scheduleORcustomORbutton, availability_weightage_value = availability_weightage_value, user_id = user_id)
        if cooldown_checker_return_True_if_accept(room_name=fci_room_name, input_type="custom", seconds=60):
            with app.app_context():
                db.session.add(incoming_to_DB)
                db.session.commit()
            success_fail_flash(True)
            session["custom_schedule_search_room"], session["custom_schedule_datetime"], session["custom_schedule_hours"], session["custom_room_status"], session["custom_schedule_textarea"] = None, None, None, None, None # clears value from last booking
        else:
            session["custom_schedule_search_room"], session["custom_schedule_datetime"], session["custom_schedule_hours"], session["custom_room_status"], session["custom_schedule_textarea"] = custom_schedule_search_room, custom_schedule_datetime, custom_schedule_hours, custom_room_status, custom_schedule_textarea # retains values from failed booking
    else:
        session["custom_schedule_search_room"], session["custom_schedule_datetime"], session["custom_schedule_hours"], session["custom_room_status"], session["custom_schedule_textarea"] = custom_schedule_search_room, custom_schedule_datetime, custom_schedule_hours, custom_room_status, custom_schedule_textarea # retains values from failed booking
        success_fail_flash(False)

def return_dict_all_rooms_weightage(fci_room_name=None):
    current_time_single = current_time()
    total_rooms_weightage_sum = {}
    if fci_room_name: # if room_name argument is given, search according to only that room name
        query = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_name = fci_room_name)).scalars()
    else: # else just search for all schedues
        query = db.session.execute(db.select(room_availability_schedule)).scalars()
    for schedule_single in query: # creates a dict with room name : weightage total
        weightage = 0
        if (schedule_single.input_from_scheduleORcustomORbutton == "schedule") and (schedule_single.datetime_start().weekday() == current_time_single.weekday()) and (int(schedule_single.datetime_start(strftime="%H%M%S%f")) < int(current_time_single.strftime("%H%M%S%f")) <= int(schedule_single.datetime_end(strftime="%H%M%S%f"))):
            weightage = int(schedule_single.availability_weightage_value)
        elif (float(schedule_single.epoch_start) < float(current_time_single.timestamp()) <= float(schedule_single.epoch_end)):
            weightage = int(schedule_single.availability_weightage_value)
        try: 
            total_rooms_weightage_sum[schedule_single.fci_room_name] += int(weightage) # if key already exists
        except:
            total_rooms_weightage_sum[schedule_single.fci_room_name] = int(weightage) # creates new key if it's a new room entry
    if total_rooms_weightage_sum:
        total_rooms_weightage_sum = {k: v for k, v in sorted(total_rooms_weightage_sum.items(), key=lambda item: item[1])} #stolen algo from stackoverflow lesgooooooooo, sorts the dict according to weightage strength
    return total_rooms_weightage_sum # returns a dict

def delete_old_schedule():
    room_obj = db.session.execute(db.select(room_availability_schedule)).scalars() # search for all schedule imputs
    current_time_single = current_time()
    for i in room_obj:
        check_class_start = i.datetime_start()
        timeDelta = current_time_single - check_class_start
        if timeDelta.days > (i.persistence_weeks)*7: # Deletes old inputs that are more than the persistence time/exceeds the limit
            with app.app_context():
                local_obj = db.session.merge(i) # I have no fucking clue what this is, but it might be IMPORTANT TODO ADD THIS TO EVERY COMMIT FUCKKKK refer to https://stackoverflow.com/questions/24291933/sqlalchemy-object-already-attached-to-session
                db.session.delete(local_obj)
                db.session.commit()

def success_fail_flash(boolean):
    if boolean:
        return flash("Success!") # Flask flash message
    elif not boolean:
        return flash("Something's wrong... Try again.")

def cooldown_checker_return_True_if_accept(room_name, input_type, seconds=None):
    try:
        tdelta = (float(session[f"{input_type}_{room_name}_cooldown_end"]) - current_time().timestamp())
        if tdelta > 0:
            if tdelta > 60: 
                flash(f"On cooldown. Please wait {int(tdelta//60)} minutes {int(tdelta%60)} seconds...")
            else:
                flash(f"On cooldown. Please wait {int(tdelta)} seconds...")
            return False
        else:
            if seconds:
                session[f"{input_type}_{room_name}_cooldown_end"] = (current_time() + datetime.timedelta(seconds=seconds)).timestamp()
            return True
    except:
        if seconds:
            session[f"{input_type}_{room_name}_cooldown_end"] = (current_time() + datetime.timedelta(seconds=seconds)).timestamp()
        return True

def search_suggestion_maker():
    search_suggestion = {"name":[], "aliases":[]} # creates a dict with lists of room objs and aliases objs 
    for i in db.session.execute(db.select(fci_room)).scalars():
        search_suggestion["name"].append(i.room_name)
    for i in db.session.execute(db.select(room_aliases)).scalars():
        search_suggestion["aliases"].append(i.room_name_aliases)
    session["search_suggestion"] = search_suggestion

# def in_session_weightage_total(room_name):
#     current_time_single = current_time()
#     query = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_name = room_name)).all()
#     weightage_total = None
#     if query:
#         weightage_total = 0
#         for i in range(len(query)):
#             for ii in range(len(query[i])):
#                 if (query[i][ii].input_from_scheduleORcustomORbutton == "schedule") and (int(query[i][ii].datetime_start(strftime="%H%M%S%f")) < int(current_time_single.strftime("%H%M%S%f")) <= int(query[i][ii].datetime_end(strftime="%H%M%S%f"))):
#                     weightage_total += int(query[i][ii].availability_weightage_value)
#                 elif float(query[i][ii].epoch_start) < float(current_time_single.timestamp()) <= float(query[i][ii].epoch_end):
#                     weightage_total += int(query[i][ii].availability_weightage_value)
#     return weightage_total

# Database for block, floor and number of rooms.
class fci_room(db.Model):
    __tablename__ = "fci_room"
    room_name = db.Column(db.String(50), primary_key=True,  nullable=False )
    room_block = db.Column(db.String(1), nullable=False)
    room_floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    room_classes_schedule = db.relationship("room_availability_schedule", backref="fci_room", lazy=True)
    room_name_aliases = db.relationship("room_aliases", backref="fci_room", lazy=True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    popup = db.Column(db.String(50))

# ChatMessage Model NEW
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship to get the username
    user = db.relationship('User', backref=db.backref('messages', lazy=True))


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
    persistence_weeks = db.Column(db.Integer, nullable=False, default=0) # must set automatically, allow user choice from input
    input_from_scheduleORcustomORbutton = db.Column(db.String(50), nullable=False) # must set automatically
    availability_weightage_value = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    def datetime_start(self, strftime=None): # gives datetime object of start and end, strftime string optional and will return a custom date and time string
        if strftime:
            return datetime.datetime.fromtimestamp(float(self.epoch_start)).astimezone(malaysiaTZ).strftime(strftime)
        else:
            return datetime.datetime.fromtimestamp(float(self.epoch_start)).astimezone(malaysiaTZ)
    def datetime_end(self, strftime=None):
        if strftime:
            return datetime.datetime.fromtimestamp(float(self.epoch_end)).astimezone(malaysiaTZ).strftime(strftime)
        else:
            return datetime.datetime.fromtimestamp(float(self.epoch_end)).astimezone(malaysiaTZ)

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
    schedule_reservation = db.relationship("room_availability_schedule", backref="reservations", lazy=True)
    def __repr__(self):
        return f'<User {self.username}>'

# -------------------------------------------------------

@app.route("/")
def redirect_home():
    return redirect("/map/0")

@app.route("/get_markers/<floor>/<room_name>") # creates data for markers
def get_markers(floor, room_name="None"):
    total_rooms_weightage_sum = return_dict_all_rooms_weightage()
    if room_name!="None":
        query = db.session.execute(db.select(fci_room).filter_by(room_name = room_name)).scalars()
    else: query = db.session.execute(db.select(fci_room).filter_by(room_floor = floor)).scalars()
    markers = []
    for i in query:
            if i.lat and i.lng:
                if i.room_name in total_rooms_weightage_sum:
                    weightage = total_rooms_weightage_sum[i.room_name]
                else: weightage = None
                markers.append({"lat":float(i.lat), "lng":float(i.lng), "popup":f"<a href=\"/roompage/{i.room_name}\">{i.room_name}</a><br/>{i.popup}", "weightage":weightage})
    return jsonify(markers)

@app.route("/map/<floor>/", methods=["GET", "POST"])
def home(floor):
    global total_rooms_weightage_sum
    delete_old_schedule()
    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
    search_suggestion_maker()
    total_rooms_weightage_sum = return_dict_all_rooms_weightage()
    return render_template("index.html", ActivePage="index", ActiveFloor = floor, total_rooms_weightage_sum = total_rooms_weightage_sum)

@app.route("/roompage/<room_name>", methods=["GET", "POST"])
def room_page(room_name):
    delete_old_schedule()
    room = db.session.execute(db.select(fci_room).filter_by(room_name = room_name)).scalar()
    if room:
        pass
    else:
        success_fail_flash(False)
        return render_template("/")
    session["custom_schedule_search_room"] = room.room_name
    current_time_single = current_time()
    # Identify which form is inputed
    if request.method == "POST":
        try:
            search = request.form["search"] # search form
            return redirect(f"/search/{search}")
        except:
            pass
        try:
            room_status = request.form["room_status"] # button form
            fci_room_name = room_name
            epoch_start = current_time_single.timestamp()
            epoch_end = (current_time_single + datetime.timedelta(hours=1)).timestamp()
            persistence_weeks = 1
            input_from_scheduleORcustomORbutton = "button"
            availability_weightage_value = int(room_status)
            incoming_to_DB = room_availability_schedule(fci_room_name = fci_room_name, epoch_start = epoch_start, epoch_end = epoch_end, persistence_weeks = persistence_weeks, input_from_scheduleORcustomORbutton = input_from_scheduleORcustomORbutton, availability_weightage_value = availability_weightage_value)
            if cooldown_checker_return_True_if_accept(room_name=fci_room_name, input_type="button", seconds=300): # cooldown 5 minutes
                with app.app_context():
                    db.session.add(incoming_to_DB)
                    db.session.commit()
                success_fail_flash(True)
        except:
            pass
    # CLIC SCHEDULE
    room_obj = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_name = room.room_name, input_from_scheduleORcustomORbutton = "schedule").order_by(room_availability_schedule.epoch_start)).scalars()
    class_schedule_list = [] # list of all schedule obj for creating the calender thing
    for i in room_obj:
        class_schedule_list.append(i)
    
    class_in_session_list = [] # current class checker, checks if class in in session, creates list of all schedule classes objs in session
    for schedule_single in class_schedule_list:
        if schedule_single.datetime_start().weekday() == current_time_single.weekday():
            if int(schedule_single.datetime_start(strftime="%H%M%S%f")) < int(current_time_single.strftime("%H%M%S%f")) <= int(schedule_single.datetime_end(strftime="%H%M%S%f")):
                class_in_session_list.append(schedule_single)

    # CUSTOM SCHEDULE
    room_obj = db.session.execute(db.select(room_availability_schedule).filter_by(fci_room_name = room.room_name, input_from_scheduleORcustomORbutton = "custom").order_by(room_availability_schedule.epoch_start)).scalars()
    custom_schedule_list = [] # list of all custom obj for creating the calender thing
    for i in room_obj:
        custom_schedule_list.append(i)
    
    custom_in_session_list = [] # current custom booking checker, checks if booking in in session, creates list of all customs booking objs in session
    for custom_single in custom_schedule_list:
        if float(custom_single.epoch_start) < float(current_time_single.timestamp()) <= float(custom_single.epoch_end):
            custom_in_session_list.append(custom_single)

    total_rooms_weightage_sum = return_dict_all_rooms_weightage(fci_room_name=room.room_name) # returns dict containing data of how available a room is
    print(total_rooms_weightage_sum)
    return render_template("roompage.html", room = room, class_schedule_list = class_schedule_list, class_in_session_list = class_in_session_list, current_time_single = current_time_single, custom_schedule_list = custom_schedule_list, custom_in_session_list = custom_in_session_list, total_rooms_weightage_sum = total_rooms_weightage_sum)

@app.route("/account/", methods=["GET", "POST"])
def account():
    return redirect("/signup")

@app.route("/search/<search>", methods=["GET", "POST"])
def search(search):
    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
    session["search"] = search
    room_name_results = db.session.execute(db.select(fci_room).filter(fci_room.room_name.icontains(search))).scalars() # searches in unique room names
    room_name_results_list = []
    for i in room_name_results:
        room_name_results_list.append(i)
    aliases_results = db.session.execute(db.select(room_aliases).filter(room_aliases.room_name_aliases.icontains(search))).scalars() # searches in aliases
    aliases_results_list = []
    for i in aliases_results:
        aliases_results_list.append(i)
    # returns list of unique room names results and list of aliases. Unique room names will be displayed first(jinja in search.html), then aliases results
    return render_template("search.html", ActivePage = "search", room_name_results_list = room_name_results_list, aliases_results_list = aliases_results_list )

@app.route("/schedule_input/", methods=["GET", "POST"])
def schedule_input():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
        try:
            schedule_input = str(request.form["schedule_input"])
            user_input_new_delete_old_schedule_decoder(schedule_input) # function for deleting outdated schedules
        except:
            pass
        try:
            request.form["custom_schedule_search_room"]
            user_input_new_custom()

        except:
            pass
    return render_template("schedule_input.html", ActivePage="schedule_input", current_time=current_time(), current_time_max=(current_time()+datetime.timedelta(weeks=4)))

@app.route("/schedule_input/clic_add_tutorial/")
def clic_add_tutorial():
    return render_template("clic_add_tutorial.html", ActivePage="schedule_input")


# ------------------------------------------------------- # Amin's work below

# Chat Room Route:
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        message = request.form['message']
        user_id = session['user_id']
        new_message = ChatMessage(message=message, user_id=user_id)
        db.session.add(new_message)
        db.session.commit()
    
    # Fetch all chat messages with associated user details
    messages = ChatMessage.query.order_by(ChatMessage.timestamp).all()
    
    return render_template('chat.html', ActivePage="chat", messages=messages)

#JSON format
@app.route('/get_messages', methods=['GET'])
def get_messages():
    messages = ChatMessage.query.order_by(ChatMessage.timestamp).all()
    messages_list = [
        {'user': {'username': message.user.username}, 'message': message.message, 'timestamp': message.timestamp}
        for message in messages
    ]
    return jsonify({'messages': messages_list})


@app.route('/signup_success')
def signup_success():
    return render_template('signup_success.html', ActivePage="account")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
        try:
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
        except:
            pass

    return render_template('signup.html', ActivePage="account")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
        try:
            email = request.form['email']
            password = request.form['password']

            user = User.query.filter_by(email=email).first()

            # Check if the user exists and verify the password
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                flash("Logged in successfully")
                return redirect("/")
            else:
                return render_template('login.html', error="Invalid email or password.")
        except:
            pass

    return render_template('login.html', ActivePage="account")

# Logout route
@app.route('/logout')
def logout():
    if "user_id" in session:
        session.pop('user_id', None)
        flash("Logged out successfully")
    return redirect(url_for('login'))

# Change password route
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
        try:
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            user = User.query.get(session['user_id'])

            if not check_password_hash(user.password, current_password):
                return render_template('change_password.html', error="Current password is incorrect.")

            elif len(new_password) < 8 or not re.search(r'[A-Z]', new_password) or not re.search(r'[a-z]', new_password) or not re.search(r'[0-9]', new_password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
                return render_template('change_password.html', error="New password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.")

            # Check if new password and confirmation match
            elif new_password != confirm_password:
                return render_template('change_password.html', error="New password and confirmation password do not match.")

            # Hash the new password before storing it in the database
            else:
                hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                user.password = hashed_password
                db.session.commit()

                # Redirect to the login page after successful password change
                session.pop("user_id", None)
                return redirect(url_for('login'))
        except:
            pass

    return render_template('change_password.html', ActivePage="account")

@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    if request.method == "POST":
        try:
            search = request.form["search"]
            return redirect(f"/search/{search}")
        except:
            pass
        try:
            request.form["delete_account"]
            user = db.session.execute(db.select(User).filter_by(id = session["user_id"])).scalar()
            with app.app_context():
                local_obj = db.session.merge(user)
                db.session.delete(local_obj)
                db.session.commit()
            flash("Account deleted.")
            session.pop("user_id", None)
            return redirect(url_for("redirect_home"))
        except:
            pass
    try: 
        session["user_id"]
        user = db.session.execute(db.select(User).filter_by(id = session["user_id"])).scalar()
    except:
        return redirect(url_for("redirect_home"))
    if user:
        return render_template("delete_account.html", ActivePage="account", username = user.username)
    else:
        session.pop("user_id", None)
        return redirect(url_for("redirect_home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)