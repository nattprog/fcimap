import datetime, pytz
date = datetime.datetime.now().astimezone(pytz.timezone('Asia/Kuala_Lumpur')).strftime("%a, %d %b %Y, %I:%M %p")
print(date)