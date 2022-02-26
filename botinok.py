import os
from threading import Thread
from datetime import datetime

import vk_api
import schedule as schedule_lib
from vk_api.longpoll import VkLongPoll, VkEventType

from methods.logger import error_log
from methods import check_env, find_classroom, funcs, sender
from methods.connect import create_tables

check_env.validator()
vk_session = vk_api.VkApi(token=str(os.environ.get('TOKEN')))
api = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
sm = "🤖"
group_list = []
print("Loading...")


def handler_group(message, user_id):
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


def message_handler(user_id, message):
    if user_id in group_list:
        user_info = vk_api.vk_api.VkApi.method(vk_session, 'users.get', {'user_ids': user})[0]
        data = funcs.create_class('None', user_info['first_name'], user_info['last_name'],
                                  message.upper(), user_id)
        if funcs.set_group(data):
            group_list.pop(group_list.index(data.ids))
        return
    message = find_classroom.find_match(message)
    day = datetime.today().weekday()
    if "group" in message:
        handler_group(message, user_id)
    elif message in ["/help", "/start", "help", "start", "помощь", "начать"]:
        funcs.start(user_id)
    elif message in ["неделя", "какая неделя"] or "which_week" in message:
        funcs.get_week(user_id)
    elif "сегодня" in message or "today" in message:
        group = funcs.get_group(user_id)
        if group:
            try:
                schedule = funcs.get_schedule(user_id, "today", group, "Пары сегодня:\n")
                if len(schedule) > 50:
                    sender.send_message(user_id, schedule)
                else:
                    text = f"{sm}Сегодня воскресенье" if day == 6 else f"{sm}Пар не обнаружено"
                    sender.send_message(user_id, text)
            except Exception as er:
                sender.send_message(user_id, f"{sm}Ooops, ошибо4ка, попробуйте позже")
                error_log(er)
    elif "завтра" in message or "tomorrow" in message:
        group = funcs.get_group(user_id)
        if group:
            try:
                schedule = funcs.get_schedule(user_id, "tomorrow", group, "Пары завтра:\n")
                if len(schedule) > 50:
                    sender.send_message(user_id, schedule)
                else:
                    text = f"{sm}Завтра воскресенье" if day == 5 else f"{sm}Пар не обнаружено"
                    sender.send_message(user_id, text)
            except Exception as er:
                sender.send_message(user_id, f"{sm}Ooops, ошибо4ка, попробуйте позже")
                error_log(er)
    elif "на следующую неделю" in message or "next_week" in message:
        group = funcs.get_group(user_id)
        if group:
            try:
                message = "------------------------\n".join(funcs.get_week_schedule(user_id, "next_week", group,
                                                                                    None, None))
                if len(message) > 50:
                    sender.send_message(user_id, message)
                else:
                    sender.send_message(user_id, f"{sm}Пар не обнаружено")
            except Exception as er:
                sender.send_message(user_id, f"{sm}Ooops, ошибо4ка, попробуйте позже")
                error_log(er)
    elif "на неделю" in message or "week" in message:
        group = funcs.get_group(user_id)
        if group:
            try:
                message = "------------------------\n".join(funcs.get_week_schedule(user_id, "week", group,
                                                                                    None, None))
                if len(message) > 50:
                    sender.send_message(user_id, message)
                else:
                    sender.send_message(user_id, f"{sm}Пар не обнаружено")
            except Exception as er:
                sender.send_message(user_id, f"{sm}Ooops, ошибо4ка, попробуйте позже")
                error_log(er)
    elif "errors" in message:
        funcs.get_errors(user_id)
    elif "users" in message:
        funcs.get_users(user_id)
    elif "room" in message:
        try:
            number = message.split()[1]
        except IndexError:
            sender.send_message(user_id, f"{sm}Не указан номер аудитории")
            return
        local_schedule = funcs.get_week_schedule(user_id, "week", None, None, number)
        if not local_schedule:
            sender.send_message(user_id, f"{sm}Пар не обнаружено")
            return
        message = "------------------------\n".join(local_schedule)
        if len(message) > 50:
            sender.send_message(user_id, message)
        else:
            sender.send_message(user_id, f"{sm}Пар не обнаружено")
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
    else:
        teacher = message[0].upper()
        teacher += message[1:]
        try:
            temp = teacher.split()[1]
            teacher = teacher.split()[0] + f" {temp.upper()}"
        except IndexError:
            pass
        local_schedule = funcs.get_week_schedule(user_id, "week", None, teacher, None)
        if not local_schedule:
            sender.send_message(user_id, f"{sm}Пар не обнаружено")
            return
        message = "------------------------\n".join(local_schedule)
        if len(message) > 50:
            sender.send_message(user_id, message)
        else:
            sender.send_message(user_id, f"{sm}Пар не обнаружено")


def create_thread():
    while True:
        schedule_lib.run_pending()


create_tables()
# start_cache = Thread(target=funcs.cache)
# start_cache.start()
# schedule_lib.every().day.at("01:00").do(funcs.cache)
# cache_thread = Thread(target=create_thread)
# print("Расписание кэширования создано!")
# cache_thread.start()
print("Загрузка бота завершена")
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        try:
            msg = event.text.lower()
            user = event.user_id
            message_handler(user, msg)
        except Exception as e:
            print(e)
