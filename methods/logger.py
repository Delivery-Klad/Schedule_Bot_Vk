import sys
import linecache
from datetime import datetime, timedelta

from methods.connect import db_connect
from methods.variables import time_difference, delimiter


def correctTimeZone():
    try:
        curr_time = datetime.now() + timedelta(hours=time_difference)
        return str(curr_time.strftime("%d.%m.%Y %H:%M:%S"))
    except Exception as er:
        error_log(er)


def log(message, user_id):
    try:
        local_time = correctTimeZone()
        # name = f"{message.from_user.first_name} {message.from_user.last_name}"
        print(f"{delimiter}\n{local_time}\nСообщение от id = {user_id}\nТекст - {message}")
    except Exception as er:
        error_log(er)


def error_log(er):
    try:
        if "string indices must be integers" in str(er):
            return
        exc_type, exc_obj, tb = sys.exc_info()
        frame = tb.tb_frame
        linenos = tb.tb_lineno
        filename = frame.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, linenos, frame.f_globals)
        connect, cursor = db_connect()
        temp_date = correctTimeZone()
        local_time = datetime.now() + timedelta(hours=time_difference)
        if "line 1 column 1" in str(er):
            reason = f"{local_time} EXCEPTION IN ({filename}, LINE {linenos} '{line.strip()}'): {exc_obj}"
        else:
            reason = f"{local_time} EXCEPTION IN ({filename}, LINE {linenos} '{line.strip()}'): {exc_obj}"
        cursor.execute(f"INSERT INTO Errors VALUES($taG${reason}$taG$)")
        connect.commit()
        cursor.close()
        connect.close()
        print(f"{delimiter}\n{temp_date}\n{reason}\n")
    except Exception as er:
        print(f"{er} ошибка в обработчике ошибок. ЧТО?")