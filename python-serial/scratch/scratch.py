from datetime import time as t, datetime as dt
timeparse = dt.now()
mil = lambda x:int(x)//1000
logtime = f'{timeparse.month}/{timeparse.day}/{timeparse.year} {timeparse.hour}:{timeparse.minute}:{timeparse.second}.{mil(timeparse.microsecond)}'

print(logtime)