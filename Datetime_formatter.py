import datetime
import pytz

#now = datetime.datetime.now()

naiveDT = datetime.datetime(2024, 9, 9, 23, 35, 37, 810921)
malaysiaTZ = pytz.timezone("Asia/Kuala_Lumpur")


dtnow = datetime.datetime.now(tz=malaysiaTZ)
print(dtnow)

localizedDT = malaysiaTZ.localize(naiveDT)
print(localizedDT.hour)

print(localizedDT.strftime("%B %d, %Y"))

strTime = "January 2, 1999"

strppedTime = malaysiaTZ.localize(datetime.datetime.strptime(strTime, "%B %d, %Y"))
print(strppedTime)

classstart = "July 4, 2024 8:00pm"
classstart = malaysiaTZ.localize(datetime.datetime.strptime(classstart, "%B %d, %Y %I:%M%p"))

current_time = datetime.datetime.now(tz=malaysiaTZ)
print(current_time)
print(classstart)
tdelta = current_time-classstart
tdeltaaa = datetime.timedelta(hours=5)
nextime = dtnow + tdeltaaa
print(current_time)
print(nextime)