import os
from time import sleep
import json
import vk_api


vk_session = vk_api.VkApi(token=str(os.environ.get('TOKEN')))
api = vk_session.get_api()
upload = vk_api.VkUpload(vk_session)


def button(text, color):
    return {
        "action": {
            "type": "text",
            "payload": "{\"button\": \"" + "1" + "\"}",
            "label": text
        },
        "color": color
    }


def send_photo(user_id, text: str, filename: str):
    photo = upload.photo_messages(filename, peer_id=user_id)
    attachment = f"photo{photo[0]['owner_id']}_{photo[0]['id']}"
    send_message(user_id, text, attachment)


def send_doc(user_id, text: str, filename: str, title=None):
    doc = upload.document_message(filename, title=title, peer_id=user_id)
    doc = doc['doc']
    attachment = f"doc{doc['owner_id']}_{doc['id']}"
    send_message(user_id, text, attachment)


def send_message(user_id, text: str, attachment=None):
    global keyboard
    try:
        if attachment is None:
            api.messages.send(user_id=user_id, message=text, random_id=0, keyboard=keyboard)
        else:
            api.messages.send(user_id=user_id, message=text, random_id=0, keyboard=keyboard, attachment=attachment)
    except Exception as e:
        if "timeout" in str(e).lower():
            sleep(5)
            api.messages.send(user_id=user_id, message=text, random_id=0, keyboard=keyboard)


keyboard = {
    "one_time": False,
    "buttons": [[button("Сегодня", "positive"), button("Завтра", "positive"), button("На неделю", "positive")]]
}
keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
keyboard = str(keyboard.decode('utf-8'))
