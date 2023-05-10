import datetime

time = 1683669558.74023
print(int(datetime.fromtimestamp(time).time().strftime('%H')))