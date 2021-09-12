import os
import psycopg2


def db_connect():
    try:
        con = psycopg2.connect(
            host=str(os.environ.get('DB_host')),
            database=str(os.environ.get('DB')),
            user=str(os.environ.get('DB_user')),
            port=str(os.environ.get('DB_port')),
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
