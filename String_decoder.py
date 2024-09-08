import re
import datetime
import pytz
from flask import Flask, redirect, url_for, render_template, session, request
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config["SECRET_KEY"] = 'sessionsecretkey'
search = None

class class_availability_schedule(db.Model):
    __tablename__ = "class_availability_schedule"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    room_name_FK = db.Column(db.String(50), nullable=False)
    class_start = db.Column(db.String(50), nullable=False)
    class_end = db.Column(db.String(50), nullable=False)
    class_subject_code = db.Column(db.String(50), nullable=False)
    class_section = db.Column(db.String(50), nullable=False)
    def __repr__(self, id, room_name_FK, class_start, class_end, class_subject_code, class_section):
        self.id = id
        self.room_name_FK = room_name_FK
        self.time_class_start = class_start
        self.time_class_end = class_end
        self.class_subject_code = class_subject_code
        self.class_section = class_section

schedule_input = ("""September 2, 2024
10:00am - 12:00pm		FIRS4001 : CMF1114 - LEC (TC1L)
2:00pm - 4:00pm		CQAR4002 : CMT1114 - TUT (TT4L)
September 3, 2024
1:00pm - 4:00pm		CQAR4003 : LAE1113 - LEC (FC03)
4:00pm - 6:00pm		CQAR4004 : CIT4163 - TUT (TT2L)
July 4, 2024
8:00am - 10:00am		CQAR4005 : CMA4114 - TUT (TT3L)
10:00am - 12:00pm		CQAR4006 : CMT1134 - TUT (TT5L)
10:00am - 12:00pm		CQAR4007 : CMTJ1132 - LEC (TC1B)
December 5, 2024 dsafd
8:00am - 10:00am		CQAR4008 : CMA4114 - TUT (TT2L)
10:00am - 12:00pm		CQAR4009 : CMA4124 - TUT (TT1L)
12:00pm - 2:00pm		CQAR4000 : CDS1114 - TUT (TT2L)
2:00pm - 4:00pm		CQAR4005 : CIT4132 - TUT (TT2L)
4:00pm - 6:00pm		CQAR4005 : CMT1114 - TUT (TT3L)
October 6, 2024
8:00am - 10:00am		CQAR4005 : CMT1114 - TUT (TT7L)
10:00am - 12:00pm		CQAR4005 : CMT1124 - TUT (TT1L)
3:00pm - 6:00pm		CQAR4005 : LMPU2223 - LEC (FCM1)
3:00pm - 6:00pm		LAST4005 : LMPU2223 - LEC (FC01)
""")





def user_input_schedule_decoder(schedule_input):
    malaysiaTZ = pytz.timezone("Asia/Kuala_Lumpur")
    schedule_input = schedule_input.replace("\n", " ")


    dates = r"(January\s*\d{1,2},\s*\d{4})|(February\s*\d{1,2},\s*\d{4})|(March\s*\d{1,2},\s*\d{4})|(April\s*\d{1,2},\s*\d{4})|(May\s*\d{1,2},\s*\d{4})|(June\s*\d{1,2},\s*\d{4})|(July\s*\d{1,2},\s*\d{4})|(August\s*\d{1,2},\s*\d{4})|(September\s*\d{1,2},\s*\d{4})|(October\s*\d{1,2},\s*\d{4})|(November\s*\d{1,2},\s*\d{4})|(December\s*\d{1,2},\s*\d{4})"
    times = r"(\d{1,2}:\d{2}[AaPp][Mm])\s*-\s*(\d{1,2}:\d{2}[AaPp][Mm])\s*([A-Za-z]{4}\d{4})\s*:\s*([A-Za-z]*\d*)\s*-\s*\w*\s*(\(\w*\))"
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

    dates_list = []
    for i in pattern_date.finditer(schedule_input):# puts match objects into a list, so i can count and call through index
        dates_list.append(i)
    for date_iter in range(len(dates_list)): # iterates through dates
        print(dates_list[date_iter].group(0))
        if date_iter < len(dates_list) - 1: # selects text from current date till the next date, so we know which time belongs to which date
            schedule_day = schedule_input[dates_list[date_iter].end():(dates_list[date_iter+1].start() or -1)]
        elif date_iter == len(dates_list) - 1: # to fix list out of bounds
            schedule_day = schedule_input[dates_list[date_iter].end():-1]
        
        for time_iter in pattern_time.finditer(schedule_day):
            class_start = f"{dates_list[date_iter].group(0)} {time_iter.group(1)}"
            class_start = malaysiaTZ.localize(datetime.datetime.strptime(class_start, "%B %d, %Y %I:%M%p")).timestamp()
            class_end = f"{dates_list[date_iter].group(0)} {time_iter.group(2)}"
            class_end = malaysiaTZ.localize(datetime.datetime.strptime(class_end, "%B %d, %Y %I:%M%p")).timestamp()
            class_start = float(class_start)
            class_end = float(class_end)
            room_name_FK = time_iter.group(3)
            class_subject_code = time_iter.group(4)
            class_section = time_iter.group(5)
            incoming_to_DB = class_availability_schedule(room_name_FK = room_name_FK, class_start = class_start, class_end = class_end, class_subject_code = class_subject_code, class_section = class_section)

            with app.app_context():
                db.session.add(incoming_to_DB)
                db.session.commit()

            print(str(malaysiaTZ.localize(datetime.datetime.fromtimestamp(class_start)).time())+" - "+str(malaysiaTZ.localize(datetime.datetime.fromtimestamp(class_end)).time()))


user_input_schedule_decoder(schedule_input)







if __name__ == "__main__":
    with app.app_context():
        db.create_all()