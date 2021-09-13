from methods import variables
import difflib


def find_match(word: str):
    best_match = 0.0
    result = ""
    for element in variables.commands:
        matcher = difflib.SequenceMatcher(None, word.lower(), element)
        if matcher.ratio() > best_match:
            best_match = matcher.ratio()
            result = element
    if best_match < 0.49:
        return word
    return result


def make_header(name: str, number: int):
    if name == "ивц":
        local_header = f"Корпус A, спускаться по главной лестнице"
    else:
        local_header = f"Корпус {name.upper()}"
    if name == "в" or name == "б" or name == "д":
        local_header += f" {str(number)[0]} этаж, направо от главной лестницы"
    elif name == "г":
        local_header += f" {str(number)[0]} этаж, налево от главной лестницы"
    elif name == "и":
        local_header += f" {str(number)[0]} этаж, налево от главного входа"
    elif name == "а":
        if number < 5 or 202 < number < 214:
            local_header += " 2 этаж, направо от главной лестницы"
        elif 4 < number < 9 or 213 < number < 236:
            local_header += " 2 этаж, налево от главной лестницы"
        elif number in [137, 135, 131, 129, 172, 171, 170, 168, 166, 164, 162, 160, 158, 156]:
            local_header = f"Корпус A 1 этаж, спускаться по главной лестнице"
        elif 99 < number < 139:
            local_header = f"Корпус A 1 этаж, направо от главной лестницы"
        elif 172 < number < 200:
            local_header = f"Корпус A 1 этаж, налево от главной лестницы, спускаться за аудиторийей А-6"
        elif 312 < number < 319 or 8 < number < 14:
            local_header += " 3 этаж, направо от главной лестницы"
        elif 318 < number < 325 or 13 < number < 19:
            local_header += " 3 этаж, налево от главной лестницы"
        elif 299 < number < 313:
            local_header += " 3 этаж, направо от главной лестницы, подниматься за аудиторией А-1"
        elif 224 < number < 337:
            local_header += " 3 этаж, налево от главной лестницы, подниматься за аудиторией А-8"
        elif 400 < number < 413:
            local_header += " 4 этаж, направо от главной лестницы, подниматься за аудиторией А-1"
        elif number in [416, 417, 418, 419, 420, 421, 422, 423, 424, 439]:
            local_header += " 4 этаж, подниматься по главной лестнице"
        elif number in [425, 426, 427, 428, 429, 430, 433, 434, 436, 438]:
            local_header += " 4 этаж, налево от главной лестницы, подниматься за аудиторией А-8"
    return local_header


def find_classroom(classroom: str):
    try:
        classroom = classroom.replace("-", " ")
        print(classroom)
        temp = classroom.split(" ")
        print(temp)
        if len(temp) > 1:
            if temp[0].lower() in variables.parts:
                name, number = temp[0].lower(), int(temp[1])
            else:
                return None, None
        else:
            if not temp[0][0].isnumeric() and temp[0][1:].isnumeric():
                name, number = temp[0][0].lower(), int(temp[0][1:])
            else:
                return None, None
        if name == "ивц":
            filename = "ivc.png"
        elif name == "а":
            if number < 5 or 202 < number < 214:
                filename = "a_2_r"
            elif 4 < number < 9 or 213 < number < 236:
                filename = "a_2_l"
            elif number in [137, 135, 131, 129, 172, 171, 170, 168, 166, 164, 162, 160, 158, 156]:
                filename = "a_1_m"
            elif 99 < number < 139:
                filename = "a_1_r"
            elif 172 < number < 200:
                filename = "a_1_l"
            elif 312 < number < 319 or 8 < number < 14:
                filename = "a_3_r"
            elif 318 < number < 325 or 13 < number < 19:
                filename = "a_3_l"
            elif 299 < number < 313:
                filename = "a_3_r_r"
            elif 224 < number < 337:
                filename = "a_3_l_l"
            elif 400 < number < 413:
                filename = "a_4_r"
            elif number in [416, 417, 418, 419, 420, 421, 422, 423, 424, 439]:
                filename = "a_4_m"
            elif number in [425, 426, 427, 428, 429, 430, 433, 434, 436, 438]:
                filename = "a_4_l"
            else:
                filename = None
        elif name == "б":
            filename = f"b_{str(number)[0]}"
        elif name == "в":
            filename = f"v_{str(number)[0]}"
        elif name == "г":
            filename = f"g_{str(number)[0]}"
        elif name == "д":
            filename = f"d_{str(number)[0]}"
        elif name == "и":
            filename = f"i_{str(number)[0]}"
        else:
            filename = None
        return make_header(name, number), filename
    except Exception as e:
        print(e)
        return None, None
