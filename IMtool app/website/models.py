import psycopg2
from psycopg2 import sql

class User():

    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()



    def authenticate(self, email, password):

        with self.cursor as cur:
            query = sql.SQL("SELECT * FROM konghin.users WHERE email = %s AND password = %s;")
            cur.execute(query, (email,password))
            res = cur.fetchone()
            self.conn.commit()
            if res:
                return True
            else:
                return False