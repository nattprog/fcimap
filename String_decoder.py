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


dates = r"(January\s*\d{1,2},\s*\d{4})|(February\s*\d{1,2},\s*\d{4})|(March\s*\d{1,2},\s*\d{4})|(April\s*\d{1,2},\s*\d{4})|(May\s*\d{1,2},\s*\d{4})|(June\s*\d{1,2},\s*\d{4})|(July\s*\d{1,2},\s*\d{4})|(August\s*\d{1,2},\s*\d{4})|(September\s*\d{1,2},\s*\d{4})|(October\s*\d{1,2},\s*\d{4})|(November\s*\d{1,2},\s*\d{4})|(December\s*\d{1,2},\s*\d{4})"
times = r"(\d{1,2}:\d{2}[AaPp][Mm])\s*-\s*(\d{1,2}:\d{2}[AaPp][Mm])\s*([A-Za-z]{4}\d{4})\s*:\s*([A-Za-z]*\d*)\s*-\s*\w*\s*(\(\w*\))"
# regex string to find in the input. 

# months = string to match the dates
# group(1) = ([month] [day], [year])

# times = string to match the dates
# group(1) = ([start time][AM/PM])
# group(2) = ([end time][AM/PM])
# group(3) = ([room code])
# group(4) = ([subject code])
# group(5) = ([class section])


pattern_date = re.compile(dates)
pattern_time = re.compile(times)

dates_list = []
for i in pattern_date.finditer(schedule_input):
    dates_list.append(i)
for i in range(len(dates_list)):
    print(dates_list[i].group(0))
    try:
        schedule_day = schedule_input[dates_list[i].end():(dates_list[i+1].start() or -1)]
    except:
        schedule_day = schedule_input[dates_list[i].end():-1]
    times_list = []
    for i in pattern_time.finditer(schedule_day):
        times_list.append(i)
    for i in times_list:
        print(i.group(0))
