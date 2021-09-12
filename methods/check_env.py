import os


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
