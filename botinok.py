import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import requests
import psycopg2
import json
import linecache
import sys
import os
from datetime import datetime, timedelta

vk_session = vk_api.VkApi(token=str(os.environ.get('TOKEN')))
api = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
sm = "🤖"
keyboard = None
group_list = []
admins_list = [496537969]
commands = ["сегодня", "завтра", "на неделю"]
day_dict = {"monday": "Понедельник",
            "tuesday": "Вторник",
            "wednesday": "Среда",
            "thursday": "Четверг",
            "friday": "Пятница",
            "saturday": "Суббота",
            "sunday": "Воскресенье"}
lesson_dict = {"9:": "1", "10": "2", "12": "3", "14": "4", "16": "5", "18": "6", "19": "7", "20": "8"}
time_dict = {"9:": "🕘", "10": "🕦", "12": "🕐", "14": "🕝", "16": "🕟", "18": "🕕", "19": "🕢", "20": "🕘"}
delimiter = "------------------------------------------------"
time_difference = 3
print("start")


def button(text, color):
    global keyboard
    return {
        "action": {
            "type": "text",
            "payload": "{\"button\": \"" + "1" + "\"}",
            "label": text
        },
        "color": color
    }


def send_message(user_id, text):
    global keyboard
    api.messages.send(user_id=user_id, message=text, random_id=0, keyboard=keyboard)


def correctTimeZone():
    try:
        curr_time = datetime.now() + timedelta(hours=time_difference)
        return str(curr_time.strftime("%d.%m.%Y %H:%M:%S"))
    except Exception as er:
        error_log(er)


def create_tables():
    connect, cursor = db_connect()
    cursor.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, first_name TEXT,"
                   "last_name TEXT, grp TEXT, ids BIGINT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS errors(reason TEXT)")
    connect.commit()
    cursor.close()
    connect.close()


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
        reason = f"EXCEPTION IN ({filename}, LINE {linenos} '{line.strip()}'): {exc_obj}"
        connect, cursor = db_connect()
        temp_date = correctTimeZone()
        cursor.execute(f"INSERT INTO Errors VALUES($taG${reason}$taG$)")
        connect.commit()
        cursor.close()
        connect.close()
        print(f"{delimiter}\n{temp_date}\n{reason}\n")
    except Exception as er:
        print(f"{er} ошибка в обработчике ошибок. ЧТО?")


def set_group(user_id, group):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT count(ids) FROM users WHERE ids={user_id}")
        res = cursor.fetchall()[0][0]
        if res == 0:
            cursor.execute(
                f"INSERT INTO users VALUES('None', 'None', 'None', "
                f"$taG${group}$taG$, {user_id})")
        else:
            cursor.execute(f"UPDATE users SET grp=$taG${group}$taG$ WHERE ids={user_id}")
        connect.commit()
        cursor.close()
        connect.close()
        send_message(user_id, f"{sm}Я вас запомнил")
        try:
            group_list.pop(group_list.index(user_id))
        except Exception as er:
            if "is not in list" not in str(er):
                error_log(er)
    except Exception as er:
        error_log(er)
        send_message(user_id, f"{sm}А ой, ошиб04ка")


def log(message, user_id):
    try:
        local_time = correctTimeZone()
        # name = f"{message.from_user.first_name} {message.from_user.last_name}"
        print(f"{delimiter}\n{local_time}\nСообщение от id = {user_id}\nТекст - {message}")
    except Exception as er:
        error_log(er)


def get_week(user_id):
    try:
        week = int((datetime.now() + timedelta(hours=time_difference)).strftime("%V"))
        if week < 39:
            week -= 5
        else:
            week -= 38
        send_message(user_id, f"{week}< неделя")
    except Exception as er:
        error_log(er)


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
    global lesson_dict
    try:
        return f"{lesson_dict[lsn[:2]]} пара"
    except KeyError:
        return "? пара"


def get_teacher_ico(name):
    try:
        symbol = name.split(' ', 1)[0]
        return "👩‍🏫" if symbol[len(symbol) - 1] == "а" else "👨‍🏫"
    except IndexError:
        return ""


def get_time_ico(time):
    global time_dict
    try:
        return time_dict[time[:2]]
    except Exception as er:
        error_log(er)
        return "🕐"


def db_connect():  # функция подключения к первой базе данных
    try:
        con = psycopg2.connect(
            host="ec2-34-252-251-16.eu-west-1.compute.amazonaws.com",
            database=str(os.environ.get('DB')),
            user=str(os.environ.get('DB_user')),
            port="5432",
            password=str(os.environ.get('DB_pass'))
        )
        cur = con.cursor()
        return con, cur
    except Exception as er:
        print(er)


def get_schedule(day, group, title):
    res = requests.get(f"https://schedule-rtu.rtuitlab.dev/api/schedule/{group}/{day}")
    lessons = res.json()
    schedule = title
    for i in lessons:
        j, o = i['lesson'], i['time']
        try:
            schedule += f"{number_of_lesson(o['start'])} ({j['classRoom']}" \
                   f"{get_time_ico(o['start'])}{o['start']} - {o['end']})\n{j['name']} " \
                   f"({j['type']})\n{get_teacher_ico(j['teacher'])} {j['teacher']}\n\n"
        except TypeError:
            pass
        except Exception as er:
            error_log(er)
    return schedule


def get_week_schedule(user_id, week, group):
    res = requests.get(f"https://schedule-rtu.rtuitlab.dev/api/schedule/{group}/{week}")
    lessons = res.json()
    rez, days = "", []
    try:
        for i in lessons:
            days.append(i)
        days = sort_days(days)
        for i in days:
            rez += f"{day_dict[i]}\n"
            for k in lessons[i]:
                j, o = k['lesson'], k['time']
                try:
                    rez += f"{number_of_lesson(o['start'])} ({j['classRoom']}" \
                           f"{get_time_ico(o['start'])}{o['start']} - {o['end']})\n{j['name']} " \
                           f"({j['type']})\n{get_teacher_ico(j['teacher'])} {j['teacher']}\n\n"
                except TypeError:
                    pass
                except Exception as er:
                    error_log(er)
            rez += "------------------------\n"
    except Exception as er:
        error_log(er)
        try:
            send_message(user_id, f"{sm}А ой, ошиб04ка")
        except Exception as err:
            error_log(err)
    if len(rez) > 50:
        send_message(user_id, rez)
    else:
        send_message(user_id, f"{sm}Пар не обнаружено")


def start(user_id):
    try:
        text = f"{sm}Камнями кидаться СЮДА ()\n" \
               f"/group - установить/изменить группу\n" \
               f"/today - расписание на сегодня\n" \
               f"/tomorrow - расписание на завтра\n" \
               f"/week - расписание на неделю" \
               f"/next_week - расписание на некст неделю"
        send_message(user_id, text)
    except Exception as er:
        error_log(er)
        try:
            send_message(user_id, f"{sm}А ой, ошиб04ка")
        except Exception as err:
            error_log(err)


def handler_group(message, user_id):
    log(message, user_id)
    try:
        if user_id not in group_list:
            send_message(user_id, f"{sm}Напишите вашу группу")
            group_list.append(user_id)
        else:
            send_message(user_id, f"{sm}Напишите вашу группу")
    except Exception as er:
        error_log(er)
        try:
            send_message(user_id, f"{sm}А ой, ошиб04ка")
        except Exception as err:
            error_log(err)


def get_group(user_id):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT grp FROM users WHERE ids={user_id}")
        try:
            group = cursor.fetchone()[0]
            cursor.close()
            connect.close()
            return group
        except TypeError:
            send_message(user_id, f"{sm}У вас не указана группа\n/group, чтобы указать группу")
            return
        except Exception as er:
            error_log(er)
    except Exception as er:
        error_log(er)
        try:
            send_message(user_id, f"{sm}Не удается получить вашу группу\n/group, чтобы указать группу")
        except Exception as err:
            error_log(err)
        return


def message_handler(user_id, message):
    if user_id in group_list:
        set_group(user_id, message.upper())
        return
    day = datetime.today().weekday()
    if "group" in message:
        handler_group(message, user_id)
    elif message == "начать" or "start" in message:
        start(user_id)
    elif message == "неделя" or "which_week" in message:
        get_week(user_id)
    elif "сегодня" in message or "today" in message:
        group = get_group(user_id)
        if group:
            try:
                schedule = get_schedule("today", group, "Пары сегодня:\n")
                if len(schedule) > 50:
                    send_message(user_id, schedule)
                else:
                    send_message(user_id, f"{sm}Пар не обнаружено")
            except Exception as er:
                if "line 1 column 1" in str(er):
                    text = "Сегодня воскресенье" if day == 6 else "Не удается связаться с API"
                    send_message(user_id, f"{sm}{text}")
                else:
                    error_log(er)
    elif "завтра" in message or "tomorrow" in message:
        group = get_group(user_id)
        if group:
            try:
                schedule = get_schedule("tomorrow", group, "Пары завтра:\n")
                if len(schedule) > 50:
                    send_message(user_id, schedule)
                else:
                    send_message(user_id, f"{sm}Пар не обнаружено")
            except Exception as er:
                if "line 1 column 1" in str(er):
                    text = "Сегодня воскресенье" if day == 6 else "Не удается связаться с API"
                    send_message(user_id, f"{sm}{text}")
                else:
                    error_log(er)
    elif "на неделю" in message or "week" in message:
        group = get_group(user_id)
        if group:
            get_week_schedule(user_id, "week", group)
    elif "на следующую неделю" in message or "next_week" in message:
        group = get_group(user_id)
        if group:
            get_week_schedule(user_id, "next_week", group)
    else:
        send_message(user_id, f"{sm}Я вас не понял")


create_tables()
keyboard = {
    "one_time": False,
    "buttons": [
        [button("Сегодня", "positive"), button("Завтра", "positive"), button("На неделю", "positive")]
    ]
}
keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
keyboard = str(keyboard.decode('utf-8'))


for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            try:
                msg = event.text.lower()
                user = event.user_id
                log(msg, user)
                message_handler(user, msg)
                # (user, "kk")
            except Exception as e:
                print(e)
