import time
# import schedule
import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
import requests
import psycopg2
import json
import linecache
import sys
import os
from datetime import datetime, timedelta


def validator():
    if os.environ.get('TOKEN') is None:
        print("Не найдена переменная 'TOKEN'. Завершение работы...")
        exit(0)
    if os.environ.get('DB_host') is None:
        print("Не найдена переменная 'DB_host'. Завершение работы...")
        exit(0)
    if os.environ.get('DB') is None:
        print("Не найдена переменная 'DB'. Завершение работы...")
        exit(0)
    if os.environ.get('DB_user') is None:
        print("Не найдена переменная 'DB_user'. Завершение работы...")
        exit(0)
    if os.environ.get('DB_port') is None:
        print("Не найдена переменная 'DB_port'. Завершение работы...")
        exit(0)
    if os.environ.get('DB_pass') is None:
        print("Не найдена переменная 'DB_pass'. Завершение работы...")
        exit(0)


validator()
vk_session = vk_api.VkApi(token=str(os.environ.get('TOKEN')))
api = vk_session.get_api()
upload = VkUpload(vk_session)
longpoll = VkLongPoll(vk_session)
sm = "🤖"
keyboard = None
group_list = []
admins_list = [492191518, 96641952]
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
response = ""
print("Loading...")


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


def isAdmin(user_id):
    return True if user_id in admins_list else False


def db_connect():
    try:
        con = psycopg2.connect(
            host="ec2-54-217-195-234.eu-west-1.compute.amazonaws.com",
            database=str(os.environ.get('DB')),
            user=str(os.environ.get('DB_user')),
            port="5432",
            password=str(os.environ.get('DB_pass'))
        )
        cur = con.cursor()
        return con, cur
    except Exception as er:
        print(er)


def create_tables():
    try:
        print("Создание таблиц...")
        connect, cursor = db_connect()
        if connect is None or cursor is None:
            print("Я потерял БД, кто найдет оставьте на охране (не получилось подключиться к бд)")
            return
        cursor.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, first_name TEXT,"
                       "last_name TEXT, grp TEXT, ids BIGINT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS errors(reason TEXT)")
        cursor.execute("SELECT COUNT(ids) FROM users")
        print(f"Пользователей в базе {cursor.fetchone()[0]}")
        connect.commit()
        cursor.close()
        connect.close()
        print("Таблицы успешно созданы")
    except Exception as er:
        print(er)


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
            global response
            reason = f"{local_time} EXCEPTION IN ({filename}, LINE {linenos} '{line.strip()}'): {str(response)}"
        else:
            reason = f"{local_time} EXCEPTION IN ({filename}, LINE {linenos} '{line.strip()}'): {exc_obj}"
        cursor.execute(f"INSERT INTO Errors VALUES($taG${reason}$taG$)")
        connect.commit()
        cursor.close()
        connect.close()
        print(f"{delimiter}\n{temp_date}\n{reason}\n")
    except Exception as er:
        print(f"{er} ошибка в обработчике ошибок. ЧТО?")


def log(message, user_id):
    try:
        local_time = correctTimeZone()
        # name = f"{message.from_user.first_name} {message.from_user.last_name}"
        print(f"{delimiter}\n{local_time}\nСообщение от id = {user_id}\nТекст - {message}")
    except Exception as er:
        error_log(er)


def correctTimeZone():
    try:
        curr_time = datetime.now() + timedelta(hours=time_difference)
        return str(curr_time.strftime("%d.%m.%Y %H:%M:%S"))
    except Exception as er:
        error_log(er)


def users(user_id):
    global keyboard
    if user_id in admins_list:
        sql_request = "COPY (SELECT * FROM users) TO STDOUT WITH CSV HEADER"
        if user_id in admins_list:
            connect, cursor = db_connect()
            with open("temp/users.csv", "w") as output_file:
                cursor.copy_expert(sql_request, output_file)
            doc = upload.document_message("temp/users.csv", title='users', peer_id=user_id)
            doc = doc['doc']
            attachment = f"doc{doc['owner_id']}_{doc['id']}"

            api.messages.send(user_id=user_id, random_id=0, message="Пользователи", keyboard=keyboard,
                              attachment=attachment)
            os.remove("temp/users.csv")
            cursor.execute("DELETE FROM errors")
            connect.commit()
            isolation_level = connect.isolation_level
            connect.set_isolation_level(0)
            cursor.execute("VACUUM FULL")
            connect.set_isolation_level(isolation_level)
            connect.commit()
            cursor.close()
            connect.close()
    else:
        send_message(user_id, f"{sm}Я вас не понял")


def errors(user_id, message):
    global keyboard
    if user_id in admins_list:
        sql_request = "COPY (SELECT * FROM errors) TO STDOUT WITH CSV HEADER"
        if user_id in admins_list:
            connect, cursor = db_connect()
            with open("temp/errors.csv", "w") as output_file:
                cursor.copy_expert(sql_request, output_file)
            doc = upload.document_message("temp/errors.csv", title='errors', peer_id=user_id)
            doc = doc['doc']
            attachment = f"doc{doc['owner_id']}_{doc['id']}"

            api.messages.send(user_id=user_id, random_id=0, message="Лог ошибок", keyboard=keyboard,
                              attachment=attachment)
            os.remove("temp/errors.csv")
            cursor.execute("DELETE FROM errors")
            connect.commit()
            isolation_level = connect.isolation_level
            connect.set_isolation_level(0)
            cursor.execute("VACUUM FULL")
            connect.set_isolation_level(isolation_level)
            connect.commit()
            cursor.close()
            connect.close()
    else:
        send_message(user_id, f"{sm}Я вас не понял")


def start(user_id):
    try:
        text = f"{sm}Камнями кидаться СЮДА ()\n" \
               f"/group - установить/изменить группу\n" \
               f"/today - расписание на сегодня\n" \
               f"/tomorrow - расписание на завтра\n" \
               f"/week - расписание на неделю\n" \
               f"/next_week - расписание на некст неделю"
        send_message(user_id, text)
    except Exception as er:
        error_log(er)
        try:
            send_message(user_id, f"{sm}А ой, ошиб04ка")
        except Exception as err:
            error_log(err)


def cache():
    print("Caching schedule...")
    failed, local_groups = 0, 0
    try:
        os.mkdir("cache")
    except FileExistsError:
        pass
    try:
        connect, cursor = db_connect()
        if connect is None or cursor is None:
            send_message(admins_list[0], f"{sm}Я потерял БД, кто найдет оставьте на охране и повторите попытку позже")
            return
        cursor.execute("SELECT DISTINCT grp FROM users")
        local_groups = cursor.fetchall()
        for i in local_groups:
            res = requests.get(f"https://schedule-rtu.rtuitlab.dev/api/schedule/{i[0]}/week")
            if res.status_code != 200:
                failed += 1
                print(f"Caching failed {res} Group '{i[0]}'")
            else:
                print(f"Caching success {res} Group '{i[0]}'")
                lessons = res.json()
                with open(f"cache/{i[0]}.json", "w") as file:
                    json.dump(lessons, file)
                time.sleep(0.1)
        send_message(admins_list[0], f"Caching success! \n{failed}/{len(local_groups)} failed")
        try:
            doc = upload.document_message("cache/ИКБО-08-18.json", title='users', peer_id=admins_list[0])
            doc = doc['doc']
            attachment = f"doc{doc['owner_id']}_{doc['id']}"

            api.messages.send(user_id=admins_list[0], random_id=0, message="Пользователи", keyboard=keyboard,
                              attachment=attachment)
        except Exception as er:
            error_log(er)
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


def get_teacher_icon(name):
    try:
        symbol = name.split(' ', 1)[0]
        return "👩‍🏫" if symbol[len(symbol) - 1] == "а" else "👨‍🏫"
    except IndexError:
        return ""


def get_time_icon(local_time):
    global time_dict
    try:
        return time_dict[local_time[:2]]
    except Exception as er:
        error_log(er)
        return "🕐"


def set_group(user_id, group):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT count(ids) FROM users WHERE ids={user_id}")
        res = cursor.fetchall()[0][0]
        user_info = vk_api.vk_api.VkApi.method(vk_session, 'users.get', {'user_ids': user})[0]
        if res == 0:
            cursor.execute(
                f"INSERT INTO users VALUES('None', $taG${user_info['first_name']}$taG$,"
                f"$taG${user_info['last_name']}$taG$, $taG${group}$taG$, {user_id})")
        else:
            cursor.execute(f"UPDATE users SET grp=$taG${group}$taG$, first_name=$taG${user_info['first_name']}$taG$,"
                           f" last_name=$taG${user_info['last_name']}$taG$ WHERE ids={user_id}")
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


def get_week(user_id):
    try:
        week = int((datetime.now() + timedelta(hours=time_difference)).strftime("%V"))
        if week < 39:
            week -= 5
        else:
            week -= 38
        send_message(user_id, f"{week} неделя")
    except Exception as er:
        error_log(er)


def get_schedule(day, group, title):
    global response
    res = requests.get(f"https://schedule-rtu.rtuitlab.dev/api/schedule/{group}/{day}")
    response = str(res)
    lessons = res.json()
    group_schedule = title
    for i in lessons:
        j, o = i['lesson'], i['time']
        try:
            group_schedule += f"{number_of_lesson(o['start'])} ({j['classRoom']}" \
                              f"{get_time_icon(o['start'])}{o['start']} - {o['end']})\n{j['name']} " \
                              f"({j['type']})\n{get_teacher_icon(j['teacher'])} {j['teacher']}\n\n"
        except TypeError:
            pass
        except Exception as er:
            error_log(er)
    return group_schedule


def get_week_schedule(user_id, week, group):
    global response
    res = requests.get(f"https://schedule-rtu.rtuitlab.dev/api/schedule/{group}/{week}")
    response = str(res)
    day = datetime.today().weekday()
    try:
        lessons = res.json()
    except Exception as er:
        if "line 1 column 1" in str(er):
            text = "Сегодня воскресенье" if day == 6 else "Не удается связаться с API\nПроверяю кэшированное расписание"
            send_message(user_id, f"{sm}{text}")
    if res.status_code == 503:
        try:
            print(f"Поиск кэшированного расписания для группы '{group}'")
            with open(f"cache/{group}.json") as file:
                lessons = json.load(file)
        except FileNotFoundError:
            send_message(user_id, f"{sm}Кэшированое расписание для вашей группы не найдено")
            return
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
                           f"{get_time_icon(o['start'])}{o['start']} - {o['end']})\n{j['name']} " \
                           f"({j['type']})\n{get_teacher_icon(j['teacher'])} {j['teacher']}\n\n"
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
                error_log(er)
    elif "на следующую неделю" in message or "next_week" in message:
        group = get_group(user_id)
        if group:
            try:
                get_week_schedule(user_id, "next_week", group)
            except Exception as er:
                if "line 1 column 1" in str(er):
                    text = "Сегодня воскресенье" if day == 6 else "Не удается связаться с API"
                    send_message(user_id, f"{sm}{text}")
                error_log(er)
    elif "на неделю" in message or "week" in message:
        group = get_group(user_id)
        if group:
            try:
                get_week_schedule(user_id, "week", group)
            except Exception as er:
                if "line 1 column 1" in str(er):
                    text = "Сегодня воскресенье" if day == 6 else "Не удается связаться с API"
                    send_message(user_id, f"{sm}{text}")
                error_log(er)
    elif "errors" in message:
        errors(user_id, message)
    elif "users" in message:
        users(user_id)
    elif "weeknum" in message:
        group = get_group(user_id)
        if group:
            try:
                week = int(message.text.split()[1])
                get_week_schedule(user_id, f"{week}/week_num", group)
            except Exception as er:
                if "line 1 column 1" in str(er):
                    text = "Сегодня воскресенье" if day == 6 else "Не удается связаться с API\n/week - чтобы " \
                                                                  "посмотреть кэшированное расписание на " \
                                                                  "текущую неделю"
                    send_message(user_id, f"{sm}{text}")
                else:
                    send_message(user_id, f"{sm}Неверный ввод")
                error_log(er)
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
cache()
print("Бот запущен")
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        try:
            msg = event.text.lower()
            user = event.user_id
            log(msg, user)
            message_handler(user, msg)
        except Exception as e:
            print(e)
