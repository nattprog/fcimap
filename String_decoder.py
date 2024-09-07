import re
import datetime
sentence = ("""September 2, 2024
10:00am - 12:00pm		CQAR4005 : CMF1114 - LEC (TC1L)
2:00pm - 4:00pm		CQAR4005 : CMT1114 - TUT (TT4L)
September 3, 2024
1:00pm - 4:00pm		CQAR4005 : LAE1113 - LEC (FC03)
4:00pm - 6:00pm		CQAR4005 : CIT4163 - TUT (TT2L)
July 4, 2024
8:00am - 10:00am		CQAR4005 : CMA4114 - TUT (TT3L)
10:00am - 12:00pm		CQAR4005 : CMT1134 - TUT (TT5L)
10:00am - 12:00pm		CQAR4005 : CMTJ1132 - LEC (TC1B)
September 5, 2024
8:00am - 10:00am		CQAR4005 : CMA4114 - TUT (TT2L)
10:00am - 12:00pm		CQAR4005 : CMA4124 - TUT (TT1L)
12:00pm - 2:00pm		CQAR4005 : CDS1114 - TUT (TT2L)
2:00pm - 4:00pm		CQAR4005 : CIT4132 - TUT (TT2L)
4:00pm - 6:00pm		CQAR4005 : CMT1114 - TUT (TT3L)
October 6, 2024
8:00am - 10:00am		CQAR4005 : CMT1114 - TUT (TT7L)
10:00am - 12:00pm		CQAR4005 : CMT1124 - TUT (TT1L)
3:00pm - 6:00pm		CQAR4005 : LMPU2223 - LEC (FCM1)
3:00pm - 6:00pm		CQAR4005 : LMPU2223 - LEC (FC01)
""")
# months = "(January\s\d{1,2},.*\d{4})|(February\s\d{1,2},.*\d{4})|(March\s\d{1,2},.*\d{4})|(April\s\d{1,2},.*\d{4})|(May\s\d{1,2},.*\d{4})|(June\s\d{1,2},.*\d{4})|(July\s\d{1,2},.*\d{4})|(Auguest\s\d{1,2},.*\d{4})|(September\s\d{1,2},.*\d{4})|(October\s\d{1,2},.*\d{4})|(November\s\d{1,2},.*\d{4})|(December\s\d{1,2},.*\d{4})"
#pattern = re.compile(r'^January|^February|^March|^April|^May|^June|^July|^Auguest|^September|^October|^November|^December.*,.*', re.MULTILINE)
pattern = re.compile(r"(January\s\d{1,2},.*\d{4})|(February\s\d{1,2},.*\d{4})|(March\s\d{1,2},.*\d{4})|(April\s\d{1,2},.*\d{4})|(May\s\d{1,2},.*\d{4})|(June\s\d{1,2},.*\d{4})|(July\s\d{1,2},.*\d{4})|(Auguest\s\d{1,2},.*\d{4})|(September\s\d{1,2},.*\d{4})|(October\s\d{1,2},.*\d{4})|(November\s\d{1,2},.*\d{4})|(December\s\d{1,2},.*\d{4})")

matches = pattern.finditer(sentence)

for match in matches:
    print(match)