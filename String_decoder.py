import re
import datetime
import pytz
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
        class_start = malaysiaTZ.localize(datetime.datetime.strptime(class_start, "%B %d, %Y %I:%M%p"))
        class_end = f"{dates_list[date_iter].group(0)} {time_iter.group(2)}"
        class_end = malaysiaTZ.localize(datetime.datetime.strptime(class_end, "%B %d, %Y %I:%M%p"))
        print(str(class_start)+"\n"+str(class_end))
        
    # for i in times_list:
    #     print(i.group(0))
    
