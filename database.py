import sqlite3

conn = sqlite3.connect('SqliteDB.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


class DatabaseManager:
    @staticmethod
    def createTables():
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
    def clearTable(tableName):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("delete * from '{tableName}'".format(tableName=tableName))
        c.commit()

    @staticmethod
    def addUser(login, password):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("insert into users(login, password) "
                       "values ('{login}' , '{password}')"
                       .format(login=login, password=password))
        c.commit()

    @staticmethod
    def addScript(name, userId, sequence):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("insert into scripts(name, userId, sequence)"
                       "values ('{name}', '{userId}', '{sequence}')"
                       .format(name=name, userId=userId, sequence=sequence))
        c.commit()

    @staticmethod
    def addController(name, userId, controllerId, encoding, buttons):
        try:
            c = sqlite3.connect('SqliteDB.db')
            cursor = c.cursor()
            cursor.execute("insert into controllers(name, userId, controllerId, encoding, buttons)"
                           "values ('{name}', '{userId}', '{controllerId}', '{encoding}', '{buttons}')"
                           .format(name=name, userId=userId, controllerId=controllerId, encoding=encoding,
                                   buttons=buttons))
            c.commit()
        except sqlite3.IntegrityError as e:
            return str(e)
        return ''

    @staticmethod
    def addSession(login, token):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("insert into sessions(login, token)"
                       "values('{login}', '{token}')"
                       .format(login=login, token=token))
        c.commit()

    @staticmethod
    def addReceivedCode(key, code):
        connection = sqlite3.connect('SqliteDB.db')
        connection.row_factory = sqlite3.Row
        c = connection.cursor()
        c.execute("insert into receivedbuttoncodes(key, code)"
                  "values('{key}', '{code}')"
                  .format(key=key, code=code))
        connection.commit()

    @staticmethod
    def updateUser(id, login, password):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("update users set login='{login}', "
                       "password='{password}' where id='{id}'"
                       .format(id=id, login=login, password=password))
        c.commit()

    @staticmethod
    def updateController(name, userId, buttons):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("update controllers set buttons='{buttons}' where name='{name}' and userId='{userId}'"
                       .format(buttons=buttons, name=name, userId=userId))
        c.commit()

    @staticmethod
    def deleteUser(login):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("delete from users where login='{login}'".format(login=login))
        c.commit()

    @staticmethod
    def deleteController(name, userId):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("delete from controllers where name='{name}' and userId='{userId}'"
                       .format(name=name, userId=userId))
        c.commit()

    @staticmethod
    def deleteScript(userId, name):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("delete from scripts where name='{name}' and userId='{userId}'"
                       .format(name=name, userId=userId))
        c.commit()

    @staticmethod
    def getUsers():
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("select * from users")
        c.commit()
        return cursor.fetchall()

    @staticmethod
    def checkUser(login):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("select * from users where login='{login}'".format(login=login))
        c.commit()
        return cursor.fetchall()

    @staticmethod
    def getUser(login, password):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("select * from users where login='{login}' and password='{password}'"
                       .format(login=login, password=password))
        c.commit()
        return cursor.fetchall()

    @staticmethod
    def getUserId(login):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("select id from users where login='{login}'"
                       .format(login=login))
        c.commit()
        result = list(cursor.fetchall())
        if len(result) != 0:
            return list(result[0])[0]
        else:
            return -1

    @staticmethod
    def getScript(id):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("select sequence from scripts where id='{id}'".format(id=id))
        c.commit()
        return cursor.fetchone()

    @staticmethod
    def getUserScripts(userId):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("select * from scripts where userId='{userId}'".format(userId=userId))
        c.commit()
        return cursor.fetchall()

    @staticmethod
    def getUserControllers(userId):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("select * from controllers where userId='{userId}'".format(userId=userId))
        c.commit()
        return cursor.fetchall()

    @staticmethod
    def getReceivedCode(key):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("select code from receivedbuttoncodes where key='{key}'".format(key=key))
        c.commit()
        result = list(cursor.fetchall())
        if len(result) != 0:
            return list(result[0])[0]
        else:
            return ''

    @staticmethod
    def checkSession(token):
        c = sqlite3.connect('SqliteDB.db')
        cursor = c.cursor()
        cursor.execute("select login from sessions where token='{token}'".format(token=token))
        c.commit()
        return len(cursor.fetchall()) != 0
