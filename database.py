import sqlite3

conn = sqlite3.connect('SqliteDB.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


class DatabaseManager:
    @staticmethod
    def create_tables():
        if len(cursor.execute("""SELECT name FROM sqlite_master WHERE type='table';""").fetchall()) == 0:
            cursor.execute("""create table users(
            id integer primary key,
            login text unique,
            password text
            )""")
            cursor.execute("""create table sessions(
            id integer primary key,
            login text,
            token text
            )""")
            cursor.execute("""create table receivedbuttoncodes(
            id integer primary key,
            key text unique,
            code text
            )""")
            cursor.execute("""create table controllers(
            id integer primary key,
            name text,
            userId integer,
            controllerId integer,
            encoding text,
            buttons text
            )""")
            cursor.execute("""create table scripts(
            id integer primary key,
            name text,
            userId integer,
            sequence text
            )""")
            cursor.execute("create unique index controller_unique on controllers(name, userId)")
        conn.commit()

    @staticmethod
    def clear_table(tableName):
        cursor.execute("delete * from '{tableName}'".format(tableName=tableName))
        conn.commit()

    @staticmethod
    def add_user(login, password):
        cursor.execute("insert into users(login, password) "
                       "values ('{login}' , '{password}')"
                       .format(login=login, password=password))
        conn.commit()

    @staticmethod
    def add_script(name, userId, sequence):
        cursor.execute("insert into scripts(name, userId, sequence)"
                       "values ('{name}', '{userId}', '{sequence}')"
                       .format(name=name, userId=userId, sequence=sequence))
        conn.commit()

    @staticmethod
    def add_controller(name, userId, controllerId, encoding, buttons):
        try:
            cursor.execute("insert into controllers(name, userId, controllerId, encoding, buttons)"
                           "values ('{name}', '{userId}', '{controllerId}', '{encoding}', '{buttons}')"
                           .format(name=name, userId=userId, controllerId=controllerId, encoding=encoding,
                                   buttons=buttons))
            conn.commit()
        except sqlite3.IntegrityError as e:
            return str(e)
        return ''

    @staticmethod
    def add_session(login, token):
        cursor.execute("insert into sessions(login, token)"
                       "values('{login}', '{token}')"
                       .format(login=login, token=token))
        conn.commit()

    @staticmethod
    def add_received_code(key, code):
        connection = sqlite3.connect('SqliteDB.db')
        connection.row_factory = sqlite3.Row
        c = connection.cursor()
        c.execute("insert into receivedbuttoncodes(key, code)"
                  "values('{key}', '{code}')"
                  .format(key=key, code=code))
        connection.commit()

    @staticmethod
    def update_user(id, login, password):
        cursor.execute("update users set login='{login}', "
                       "password='{password}' where id='{id}'"
                       .format(id=id, login=login, password=password))
        conn.commit()

    @staticmethod
    def update_controller(name, userId, buttons):
        cursor.execute("update controllers set buttons='{buttons}' where name='{name}' and userId='{userId}'"
                       .format(buttons=buttons, name=name, userId=userId))
        conn.commit()

    @staticmethod
    def delete_user(login):
        cursor.execute("delete from users where login='{login}'".format(login=login))
        conn.commit()

    @staticmethod
    def delete_controller(name, userId):
        cursor.execute("delete from controllers where name='{name}' and userId='{userId}'"
                       .format(name=name, userId=userId))
        conn.commit()

    @staticmethod
    def delete_script(userId, name):
        cursor.execute("delete from scripts where name='{name}' and userId='{userId}'"
                       .format(name=name, userId=userId))
        conn.commit()

    @staticmethod
    def get_users():
        cursor.execute("select * from users")
        conn.commit()
        return cursor.fetchall()

    @staticmethod
    def check_user(login):
        cursor.execute("select * from users where login='{login}'".format(login=login))
        conn.commit()
        return cursor.fetchall()

    @staticmethod
    def get_user(login, password):
        cursor.execute("select * from users where login='{login}' and password='{password}'"
                       .format(login=login, password=password))
        conn.commit()
        return cursor.fetchall()

    @staticmethod
    def get_user_id(login):
        cursor.execute("select id from users where login='{login}'"
                       .format(login=login))
        conn.commit()
        result = list(cursor.fetchall())
        if len(result) != 0:
            return list(result[0])[0]
        else:
            return -1

    @staticmethod
    def get_script(id):
        cursor.execute("select sequence from scripts where id='{id}'".format(id=id))
        conn.commit()
        return cursor.fetchone()

    @staticmethod
    def get_user_scripts(userId):
        cursor.execute("select * from scripts where userId='{userId}'".format(userId=userId))
        conn.commit()
        return cursor.fetchall()

    @staticmethod
    def get_user_controllers(userId):
        cursor.execute("select * from controllers where userId='{userId}'".format(userId=userId))
        conn.commit()
        return cursor.fetchall()

    @staticmethod
    def get_received_code(key):
        cursor.execute("select code from receivedbuttoncodes where key='{key}'".format(key=key))
        conn.commit()
        result = list(cursor.fetchall())
        if len(result) != 0:
            return list(result[0])[0]
        else:
            return ''

    @staticmethod
    def check_session(token):
        cursor.execute("select login from sessions where token='{token}'".format(token=token))
        conn.commit()
        return len(cursor.fetchall()) != 0
