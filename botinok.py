import time
import schedule as schedule_lib
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import requests
import json
import os
from threading import Thread
from datetime import datetime
from methods.logger import error_log, log
from methods import check_env, find_classroom, variables, funcs, sender
from methods.connect import db_connect, create_tables

api_host = "https://schedule-rtu.rtuitlab.dev/api/"
check_env.validator()
vk_session = vk_api.VkApi(token=str(os.environ.get('TOKEN')))
api = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
sm = "🤖"
group_list = []
print("Loading...")


def users(user_id):
    if funcs.isAdmin(user_id):
        sql_request = "COPY (SELECT * FROM users) TO STDOUT WITH CSV HEADER"
        connect, cursor = db_connect()
        with open("temp/users.csv", "w") as output_file:
            cursor.copy_expert(sql_request, output_file)
        sender.send_doc(user_id, "Пользователи", "temp/users.csv")
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
        sender.send_message(user_id, f"{sm}Я вас не понял")


def errors(user_id, message):
    if funcs.isAdmin(user_id):
        sql_request = "COPY (SELECT * FROM errors) TO STDOUT WITH CSV HEADER"
        connect, cursor = db_connect()
        with open("temp/errors.csv", "w") as output_file:
            cursor.copy_expert(sql_request, output_file)
        sender.send_doc(user_id, "Лог ошибок", "temp/errors.csv")
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
        sender.send_message(user_id, f"{sm}Я вас не понял")


def start(user_id):
    try:
        text = f"{sm}Доступные команды:\n" \
               f"/help - список доступных команд\n" \
               f"/group - установить/изменить группу\n" \
               f"/today - расписание на сегодня\n" \
               f"/tomorrow - расписание на завтра\n" \
               f"/week - расписание на неделю\n" \
               f"/next_week - расписание на некст неделю\n" \
               f"/which_week - узнать номер недели"
        sender.send_message(user_id, text)
    except Exception as er:
        error_log(er)
        try:
            sender.send_message(user_id, f"{sm}А ой, ошиб04ка")
        except Exception as err:
            error_log(err)


def cache():
    print("Caching schedule...")
    week_num = requests.get(f"{api_host}current_week/").json()
    failed, local_groups = 0, 0
    try:
        os.mkdir("cache")
    except FileExistsError:
        pass
    try:
        connect, cursor = db_connect()
        if connect is None or cursor is None:
            sender.send_message(variables.admins_list[0], f"{sm}{variables.lost_db_msg}")
            return
        cursor.execute("SELECT DISTINCT grp FROM users")
        local_groups = cursor.fetchall()
        for i in local_groups:
            res = requests.get(f"{api_host}lesson/?group={i[0]}&specific_week={week_num}")
            if res.status_code != 200:
                failed += 1
                print(f"Caching failed {res} Group '{i[0]}'")
            else:
                print(f"Caching success {res} Group '{i[0]}'")
                lessons = res.json()
                with open(f"cache/{i[0]}.json", "w") as file:
                    json.dump(lessons, file)
                time.sleep(0.1)
    except Exception as er:
        error_log(er)


def set_group(user_id, group):
    try:
        connect, cursor = db_connect()
        valid_group = group.split("-")
        if len(valid_group) < 3:
            sender.send_message(user_id, f"{sm}Неверный формат группы")
            return
        if not valid_group[1].isnumeric() and not valid_group[2].isnumeric():
            sender.send_message(user_id, f"{sm}Неверный формат группы")
            return
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
        sender.send_message(user_id, f"{sm}Я вас запомнил")
        try:
            group_list.pop(group_list.index(user_id))
        except Exception as er:
            if "is not in list" not in str(er):
                error_log(er)
    except Exception as er:
        error_log(er)
        sender.send_message(user_id, f"{sm}А ой, ошиб04ка")


def get_week(user_id):
    try:
        week = requests.get(f"{api_host}current_week/").json()
        sender.send_message(user_id, f"{week} неделя")
    except Exception as er:
        error_log(er)


def get_schedule(user_id, day, group, title):
    day_num = datetime.today().weekday()
    week = "week"
    if day == "tomorrow":
        day_num += 1
        if day_num > 6:
            day_num = 0
            week = "next_week"
    if day_num == 6:
        return ""
    temp = []
    for i in get_week_schedule(user_id, week, group):
        if i.split("\n")[0] == variables.day_dict[day_num + 1]:
            temp = i.split("\n")
            temp.pop(0)
    return title + "\n".join(temp)


def get_week_schedule(user_id, week, group):
    week_num = requests.get(f"{api_host}current_week/").json()
    if week == "next_week":
        week_num = 2 if week_num == 1 else 1
    schedule = requests.get(f"{api_host}lesson/?group={group}&specific_week={week_num}")
    try:
        lessons = schedule.json()
    except Exception as er:
        error_log(er)
        text = "Не удается связаться с API\nПроверяю кэшированное расписание"
        sender.send_message(user_id, f"{sm}{text}")
    if schedule.status_code == 503:
        try:
            print(f"Поиск кэшированного расписания для группы '{group}'")
            with open(f"cache/{group}.json") as file:
                lessons = json.load(file)
        except FileNotFoundError:
            sender.send_message(user_id, f"{sm}Кэшированое расписание для вашей группы не найдено")
            return
    messages, message, prev_day = [], "", -1
    for i in lessons:
        try:
            if i['day_of_week'] != prev_day:
                if message != "":
                    messages.append(message)
                message = ""
                message += f"{variables.day_dict[i['day_of_week']]}\n"
                prev_day = i['day_of_week']
            try:
                lesson_type = f" ({i['lesson_type']['short_name']})"
            except TypeError:
                lesson_type = ""
            if i['teacher'] is None:
                teacher = ""
            else:
                name = i['teacher'][0]['name']
                teacher = f"{funcs.get_teacher_icon(name)} {name}"
            if i['room'] is None:
                room = ""
            else:
                room = i['room']['name']
            message += f"{i['call']['call_num']} пара ({room}" \
                       f"{funcs.get_time_icon(i['call']['begin_time'])}" \
                       f"{i['call']['begin_time']} - {i['call']['end_time']})\n" \
                       f"{i['discipline']['name']}{lesson_type}\n" \
                       f"{teacher}\n\n"
        except Exception as er:
            error_log(er)
    messages.append(message)
    return messages


def handler_group(message, user_id):
    log(message, user_id)
    try:
        if user_id not in group_list:
            sender.send_message(user_id, f"{sm}Напишите вашу группу")
            group_list.append(user_id)
        else:
            sender.send_message(user_id, f"{sm}Напишите вашу группу")
    except Exception as er:
        error_log(er)
        try:
            sender.send_message(user_id, f"{sm}А ой, ошиб04ка")
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
            sender.send_message(user_id, f"{sm}У вас не указана группа\n/group, чтобы указать группу")
            return
        except Exception as er:
            error_log(er)
    except Exception as er:
        error_log(er)
        try:
            sender.send_message(user_id, f"{sm}Не удается получить вашу группу\n/group, чтобы указать группу")
        except Exception as err:
            error_log(err)
        return


def message_handler(user_id, message):
    if user_id in group_list:
        set_group(user_id, message.upper())
        return
    message = find_classroom.find_match(message)
    day = datetime.today().weekday()
    if "group" in message:
        handler_group(message, user_id)
    elif message in ["/help", "/start", "help", "start", "помощь", "начать"]:
        start(user_id)
    elif message in ["неделя", "какая неделя"] or "which_week" in message:
        get_week(user_id)
    elif "сегодня" in message or "today" in message:
        group = get_group(user_id)
        if group:
            try:
                schedule = get_schedule(user_id, "today", group, "Пары сегодня:\n")
                if len(schedule) > 50:
                    sender.send_message(user_id, schedule)
                else:
                    text = f"{sm}Сегодня воскресенье" if day == 6 else f"{sm}Пар не обнаружено"
                    sender.send_message(user_id, text)
            except Exception as er:
                sender.send_message(user_id, f"{sm}Ooops, ошибо4ка, попробуйте позже")
                error_log(er)
    elif "завтра" in message or "tomorrow" in message:
        group = get_group(user_id)
        if group:
            try:
                schedule = get_schedule(user_id, "tomorrow", group, "Пары завтра:\n")
                if len(schedule) > 50:
                    sender.send_message(user_id, schedule)
                else:
                    text = f"{sm}Завтра воскресенье" if day == 5 else f"{sm}Пар не обнаружено"
                    sender.send_message(user_id, text)
            except Exception as er:
                sender.send_message(user_id, f"{sm}Ooops, ошибо4ка, попробуйте позже")
                error_log(er)
    elif "на следующую неделю" in message or "next_week" in message:
        group = get_group(user_id)
        if group:
            try:
                message = "------------------------\n".join(get_week_schedule(user_id, "next_week", group))
                if len(message) > 50:
                    sender.send_message(user_id, message)
                else:
                    sender.send_message(user_id, f"{sm}Пар не обнаружено")
            except Exception as er:
                sender.send_message(user_id, f"{sm}Ooops, ошибо4ка, попробуйте позже")
                error_log(er)
    elif "на неделю" in message or "week" in message:
        group = get_group(user_id)
        if group:
            try:
                message = "------------------------\n".join(get_week_schedule(user_id, "week", group))
                if len(message) > 50:
                    sender.send_message(user_id, message)
                else:
                    sender.send_message(user_id, f"{sm}Пар не обнаружено")
            except Exception as er:
                sender.send_message(user_id, f"{sm}Ooops, ошибо4ка, попробуйте позже")
                error_log(er)
    elif "errors" in message:
        errors(user_id, message)
    elif "users" in message:
        users(user_id)
    elif len(message) < 8:
        text, pic = find_classroom.find_classroom(message)
        if text is None and pic is None:
            sender.send_message(user_id, f"{sm}Я вас не понял")
            return
        if pic is not None:
            try:
                sender.send_photo(user_id, text, f"maps/{pic}.png")
                return
            except FileNotFoundError:
                sender.send_message(user_id, f"{sm}Аудитория не найдена на схемах")
                return
        else:
            sender.send_message(user_id, f"{sm}Аудитория не найдена на схемах")
            return


def create_thread():
    while True:
        schedule_lib.run_pending()


create_tables()
start_cache = Thread(target=cache)
start_cache.start()
schedule_lib.every().day.at("01:00").do(cache)
cache_thread = Thread(target=create_thread)
print("Расписание кэширования создано!")
cache_thread.start()
print("Загрузка бота завершена")
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        try:
            msg = event.text.lower()
            user = event.user_id
            log(msg, user)
            message_handler(user, msg)
        except Exception as e:
            print(e)
