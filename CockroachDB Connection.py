import os
import psycopg2
from psycopg2 import sql

# conn = psycopg2.connect(os.environ["DATABASE_URL"])

# with conn.cursor() as cur:
#     cur.execute(sql.SQL("Select * from konghin.users"))
#     res = cur.fetchone()
#     conn.commit()
#     conn.close()
#     print(res)

class Database():
    def __init__(self, database_url):
        self.conn = psycopg2.connect(database_url)
        self.cursor = self.conn.cursor()
        self.schema = 'konghin'
    
    def insert(self, table, values, columns=None):

        query = sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values})").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(table),
            columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
            values=sql.SQL(', ').join(sql.Placeholder() * len(values))
        )
        self.cursor.execute(query, values)
        self.conn.commit()
    
    def select(self, table, columns, where=None):
        query = sql.SQL("SELECT {columns} FROM {schema}.{table}").format(
            columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(table)
        )
        if where:
            query += sql.SQL(" WHERE {where}").format(where=sql.SQL(where))
        try:
            # Execute the query
            self.cursor.execute(query)
            
            # Fetch and print the results
            results = self.cursor.fetchall()
            print("Query Results:", results)
            return results
        except Exception as e:
            print("An error occurred:", e)
            return None

    def update(self, table, set_columns, set_values, where):
        set_clause = sql.SQL(', ').join(
            sql.SQL("{col} = {val}").format(col=sql.Identifier(col), val=sql.Placeholder()) 
            for col in set_columns
        )
        query = sql.SQL("UPDATE {schema}.{table} SET {set_clause} WHERE {where}").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(table),
            set_clause=set_clause,
            where=sql.SQL(where)
        )
        self.cursor.execute(query, set_values)
        self.conn.commit()

    def delete(self, table, where):
        query = sql.SQL("DELETE FROM {schema}.{table} WHERE {where}").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(table),
            where=sql.SQL(where)
        )
        print(query.as_string(self.conn))
        self.cursor.execute(query)
        self.conn.commit()

    def __del__(self):
        self.cursor.close()
        self.conn.close()


if __name__=='__main__':
    db = Database(os.environ["DATABASE_URL"])
    # db.insert(table='users',columns=['id','email','password','first_name'],values=[3, 'abcd@gmail.com', '121212', 'abcd'])
    # db.update('users',['first_name'],['qwer'],'id=3')
    # db.select('users',['first_name'],'id=3')
    db.delete('users','id=3')