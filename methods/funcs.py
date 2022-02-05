from methods.logger import error_log
from methods.variables import admins_list, time_dict


def isAdmin(user_id):
    return True if user_id in admins_list else False


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
