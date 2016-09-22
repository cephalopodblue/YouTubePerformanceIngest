import datetime
import re
import tempfile
import subprocess

exif = "C:\\Users\\heather\\Desktop\\exiftool.exe"

TODAY = datetime.date.today()

separators = (".", ",", "-", "/", " ")
months = ['0', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
          'September', 'October', 'November', 'December']


def get_year(year_string):
    try:
        y = int(year_string)
        if y < 1990:
            if y <= TODAY.year - 2000:
                y += 2000
            elif y <= 31:
                y += 1900
            else:
                return False
        return y
    except:
        return False


def get_month(month_string):
    if month_string in months:
        return months.index(month_string)
    else:
        try:
            m = int(month_string)
            if m <= 12:
                return m
            else:
                return False
        except:
            return False


def get_day(day_string):
    try:
        d = int(day_string)
        if d > 31:
            # definitely not a day
            return False
        return d
    except:
        return False


def date_rfc(date):
    d = date.isoformat()
    if re.search("\.\d+", d):
        return re.sub("\.\d+", "Z", d)
    else:
        return d + "Z"


def synology_date(date):
    d = date.strftime('%m-%d-%y')
    return d


def move_date(date, year=0, month=0, day=0):
    d = datetime.datetime(date.year + year, date.month + month, date.day+day)
    return d


def get_date(date_string):
    sep = "".join(separators)
    valid_date = months.copy()
    valid_date.pop(0)
    valid_date = "|".join(valid_date)
    date = re.search("(" + valid_date + "|\d+)[" + sep + "]+(" + valid_date + "|\d+)[" + sep + "]+(" + valid_date + "|\d+)", date_string)

    possibilities = []
    
    if date:
        # year-month-day
        year = get_year(date.group(1))
        month = get_month(date.group(2))
        day = get_day(date.group(3))
        if year and month and day:
            possibilities.append(datetime.datetime(year, month, day))

        # day-month-year
        year = get_year(date.group(3))
        month = get_month(date.group(2))
        day = get_day(date.group(1))
        if year and month and day:
            possibilities.append(datetime.datetime(year, month, day))

        # month-day-year
        year = get_year(date.group(3))
        month = get_month(date.group(1))
        day = get_day(date.group(2))
        if year and month and day:
            possibilities.append(datetime.datetime(year, month, day))

    return possibilities

meta_pattern = re.compile("(?P<name>.+(?=\s+:))\s*:(?P<meta>.+)")


def video_meta(file_name):
    file_meta = {}
    with tempfile.TemporaryFile() as temp_results:
        subprocess.run([exif, file_name], stdout=temp_results)
        temp_results.seek(0)
        for line in temp_results:
            cur = line.decode("utf-8")
            m = meta_pattern.match(cur)
            if m:
                name = m.group("name").strip()
                meta = m.group("meta").strip()
                file_meta[name] = meta
    return file_meta
