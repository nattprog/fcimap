import re
import datetime
schedule_input = ("""September 2, 2024
10:00am - 12:00pm		CQAR4001 : CMF1114 - LEC (TC1L)
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
3:00pm - 6:00pm		CQAR4005 : LMPU2223 - LEC (FC01)
""")

schedule_input = schedule_input.replace("\n", " ")
months = r"(January.*\d{1,2},.*\d{4})|(February.*\d{1,2},.*\d{4})|(March.*\d{1,2},.*\d{4})|(April.*\d{1,2},.*\d{4})|(May.*\d{1,2},.*\d{4})|(June.*\d{1,2},.*\d{4})|(July.*\d{1,2},.*\d{4})|(Auguest.*\d{1,2},.*\d{4})|(September.*\d{1,2},.*\d{4})|(October.*\d{1,2},.*\d{4})|(November.*\d{1,2},.*\d{4})|(December.*\d{1,2},.*\d{4})"

pattern_date = re.compile(r"(January\s*\d{1,2},\s*\d{4})|(February\s*\d{1,2},\s*\d{4})|(March\s*\d{1,2},\s*\d{4})|(April\s*\d{1,2},\s*\d{4})|(May\s*\d{1,2},\s*\d{4})|(June\s*\d{1,2},\s*\d{4})|(July\s*\d{1,2},\s*\d{4})|(August\s*\d{1,2},\s*\d{4})|(September\s*\d{1,2},\s*\d{4})|(October\s*\d{1,2},\s*\d{4})|(November\s*\d{1,2},\s*\d{4})|(December\s*\d{1,2},\s*\d{4})")
pattern_time = re.compile(r"(\d{1,2}:\d{2}[AaPp][Mm])\s*-\s*(\d{1,2}:\d{2}[AaPp][Mm])\s*(\w{4}\d{4})\s*:")

match_dates = pattern_date.finditer(schedule_input)
match_times = pattern_time.finditer(schedule_input)

dates_list = []
for i in match_dates:
    dates_list.append(i)

len_dates_list = len(dates_list)
for i in range(len_dates_list):
    print(dates_list[i])
    try:
        schedule_day = schedule_input[dates_list[i].end():dates_list[i+1].start()]
    except:
        schedule_day = schedule_input[dates_list[i].end():-1]
    match_times = pattern_time.finditer(schedule_day)
    for match_time in match_times:
        print(match_time)
    


for match_date in match_dates:
    print(match_date)
    



# times_list = []
# for i in match_times:
#     times_list.append(i)

# times_list = []
# for i in match_times:
#     times_list.append(i)

# for dates_i in range(len(dates_list)):
#     date = dates_list[dates_i]
#     schedule_day = schedule_input[dates_list[i]:]

#     for times_i in range(len(times_list)):
#         time = times_list[times_i]
#         try:
#             if dates_list[dates_i].end() < time.start() < dates_list[dates_i+1].start():
#                 day_obj.append(times_list[times_i])
#         except:
#             if dates_list[dates_i].end() < time.start():
#                 day_obj.append(times_list[times_i])
#     for i in day_obj:
#         print(i.group(0))



# for i in range(0, 10):
#     print(sentence[i], end="")