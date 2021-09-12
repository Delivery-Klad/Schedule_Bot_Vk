import json
from methods.variables import api


def button(text, color):
    return {
        "action": {
            "type": "text",
            "payload": "{\"button\": \"" + "1" + "\"}",
            "label": text
        },
        "color": color
    }


def send_photo():
    pass


def send_doc():
    pass


def send_message(user_id, text, attachment=None):
    global keyboard
    if attachment is None:
        api.messages.send(user_id=user_id, message=text, random_id=0, keyboard=keyboard)
    else:
        api.messages.send(user_id=user_id, message=text, random_id=0, keyboard=keyboard, attachment=attachment)


keyboard = {
    "one_time": False,
    "buttons": [[button("Сегодня", "positive"), button("Завтра", "positive"), button("На неделю", "positive")]]
}
keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
keyboard = str(keyboard.decode('utf-8'))
