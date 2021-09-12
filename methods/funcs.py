from methods.logger import error_log
from datetime import datetime, timedelta
from methods.variables import admins_list, time_difference, lesson_dict, time_dict


def isAdmin(user_id):
    return True if user_id in admins_list else False


def sort_days(days):
    temp, day = [], ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i in days:
        temp.append(day.index(i))
    temp.sort()
    days, index = [], 10
    for i in temp:
        days.append(day[i])
    return days


def number_of_lesson(lsn):
    try:
        return f"{lesson_dict[lsn[:2]]} пара"
    except KeyError:
        return "? пара"


def get_teacher_icon(name):
    try:
        symbol = name.split(' ', 1)[0]
        return "👩‍🏫" if symbol[len(symbol) - 1] == "а" else "👨‍🏫"
    except IndexError:
        return ""


def get_time_icon(local_time):
    try:
        return time_dict[local_time[:2]]
    except Exception as er:
        error_log(er)
        return "🕐"
