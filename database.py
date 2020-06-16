import sqlite3

conn = sqlite3.connect('SqliteDB.db')
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
        conn.commit()

    @staticmethod
    def clearTable(tableName):
        cursor.execute("delete * from '{tableName}'".format(tableName=tableName))
        conn.commit()

    @staticmethod
    def addUser(login, password):
        cursor.execute("insert into users(login, password) "
                       "values ('{login}' , '{password}')"
                       .format(login=login, password=password))
        conn.commit()

    @staticmethod
    def updateUser(id, login, password):
        cursor.execute("update users set login='{login}', "
                       "password='{password}' where id='{id}'"
                       .format(id=id, login=login, password=password))
        conn.commit()

    @staticmethod
    def deleteUser(login):
        cursor.execute("delete from users where login='{login}'".format(login=login))
        conn.commit()

    @staticmethod
    def getUsers():
        cursor.execute("select * from users")
        conn.commit()
        return cursor.fetchall()

    @staticmethod
    def checkUser(login):
        cursor.execute("select * from users where login='{login}'".format(login=login))
        conn.commit()
        return cursor.fetchall()

    @staticmethod
    def getUser(login, password):
        cursor.execute("select * from users where login='{login}' and password='{password}'"
                       .format(login=login, password=password))
        conn.commit()
        return cursor.fetchall()

    @staticmethod
    def getUserId(login):
        cursor.execute("select id from users where login='{login}'"
                       .format(login=login))
        conn.commit()
        return cursor.fetchone()
