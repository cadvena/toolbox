
from datetime import datetime as dtdt
from datetime import timedelta
import pytz

tz_suffix = ' %Z%z'
datetime_us_fmt = '%m/%d/%Y %H:%M:%S'
# datetime_w_tz_us_fmt = datetime_us_fmt + tz_suffix
datetime_us_precise_fmt = '%m/%d/%Y %H:%M:%S.%f'
# datetime_w_tz_us_precise_fmt = datetime_us_precise_fmt + tz_suffix
date_us_fmt = '%m/%d/%Y'
time_us_fmt = '%H:%M:%S'
# time_w_tz_us_fmt = time_us_fmt + tz_suffix
time_us_precise_fmt = '%H:%M:%S.%f'
# time_w_tz_us_precise_fmt = time_us_precise_fmt + tz_suffix
datetime_filename_fmt = '%Y%m%d_%H%M%S'
# datetime_w_tz_filename_fmt = datetime_filename_fmt + tz_suffix
datetime_filename_precise_fmt = '%Y%m%d_%H%M%S%f'

# Add to a datetime.
print('Add to a datetime')
print( dtdt(2021, 9, 28, 13, 45) + timedelta(days=0, weeks=0, hours=0,
                                             minutes=0, seconds=0) )


# Convert to string
print('Convert datetime to str')
print( dtdt(2021, 9, 28, 13, 45).strftime('%m/%d/%Y %H:%M:%S') )


# Convert from string
print('Convert str to datetime')
print(dtdt.strptime('01/03/2021 04:05:06.789012', '%m/%d/%Y %H:%M:%S.%f'))


# Now to string to put in filename
print('Convert str to datetime')
date_str = dtdt.now().strftime('%Y%m%d_%H%M%S')
print(date_str)
fp = f'stem_{date_str}.suffix'
print(fp)


# Convert EPT / UTC

# Timezones
ept = pytz.timezone('US/Eastern')
utc = pytz.utc
# str format
fmt = '%Y-%m-%d %H:%M:%S %Z%z'

print("\nEPT/UTC examples:")
print("\nWinter (EST) example:")
# Create a UTC time in the winter
winter_utc = dtdt(2016, 1, 24, 18, 0, 0, tzinfo=utc)
print("    UTC: ", winter_utc.strftime(fmt))
# Convert from UTC to eastern prevailing time.  Since, the timestamp is in the
# winter, prevailing time is standard time.
winter_ept = winter_utc.astimezone(ept)
print("    EPT: ", winter_ept.strftime(fmt))
# Let's convert back to UTC to show we get back to the original value.
winter_utc2 = winter_ept.astimezone(utc)
print("    UTC: ", winter_utc2.strftime(fmt))

# Let's do that again for a summer datetime.
print("\nSummer (EDT) example:")
summer_utc = dtdt(2016, 7, 24, 18, 0, 0, tzinfo=utc)
print("    UTC: ", summer_utc.strftime(fmt))
# Convert from UTC to eastern prevailing time.  Since, the timestamp is in the
# winter, prevailing time is daylight saving time.
summer_ept = summer_utc.astimezone(ept)
print("    EPT: ", summer_ept.strftime(fmt))
# Let's convert back to UTC to show we get back to the original value.
summer_utc2 = summer_ept.astimezone(utc)
print("    UTC: ", summer_utc2.strftime(fmt))

def this_month():
    now = dtdt.now()
    result = dtdt(year=now.year, month=now.month, day=1)
    return result
