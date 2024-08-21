import os
import psycopg2
from psycopg2 import sql
import logging
import dictionary as dic
import numpy as np
from datetime import datetime
import pandas as pd
import json


SEQUENCES = {
    'users': dic.USER_SEQ,
    'booking': dic.BOOKING_SEQ,
    'customer': dic.CUSTOMER_SEQ,
    'stock': dic.STOCK_SEQ,
    'sale': dic.SALE_SEQ,
    'salesman': dic.SALESMAN_SEQ,
    'purchase': dic.PURCHASE_SEQ
}

PREFIX = {
    'users': 'USR',
    'booking': 'BOOK',
    'customer': 'CUST',
    'stock': 'STK',
    'sale': 'SALE',
    'salesman': 'SLM',
    'purchase': 'PUR'
}

log_file = dic.LOG_DIR+str(datetime.now().strftime("%Y_%m_%d"))+'.log'

logging.basicConfig(filename=log_file,level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Database:
    def __init__(self, database_url: str):
        self.conn = psycopg2.connect(database_url)
        self.cursor = self.conn.cursor()
        self.schema = 'konghin'
    def select(self, table: str, columns: list = None, where: str = None, js: bool = False):
        """
        Selects data from a specified table.

        Args:
            table (str): The table name from which to select data.
            columns (list, optional): List of column names to select. If None, selects all columns. Defaults to None.
            where (str, optional): SQL condition for filtering rows. Defaults to None.
            json (bool, optional): If True, returns the result as a JSON string. If False, returns as a DataFrame. Defaults to False.

        Returns:
            pd.DataFrame or str: A DataFrame of the selected data or a JSON string if json is True. Returns None if an error occurs.
        """
        if columns:
            query = sql.SQL("SELECT {columns} FROM {schema}.{table}").format(
                columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
                schema=sql.Identifier(self.schema),
                table=sql.Identifier(table)
            )
        else:
            query = sql.SQL("SELECT * FROM {schema}.{table}").format(
                schema=sql.Identifier(self.schema),
                table=sql.Identifier(table)
            )

        if where:
            query += sql.SQL(" WHERE {where}").format(where=sql.SQL(where))

        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            df = pd.DataFrame(np.array(results))
            colnames = [desc[0] for desc in self.cursor.description]
            df.columns = colnames
            logging.info(f"Successfully selected data from {self.schema}.{table}.")
            logging.info(f"Query: {query.as_string(self.conn)}")
            if json:
                return json.loads(df.to_json(orient='records', date_format='iso'))
            else:
                return df
        except psycopg2.Error as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            return None
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            return None

    def insert(self, table: str, values: list, columns: list = None) -> None:
        base_query = sql.SQL("INSERT INTO {schema}.{table}").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(table)
        )

        sequence_name = SEQUENCES.get(table.lower())

        if sequence_name ==None:
            logging.error(f"Table not found. Please ensure u entered correct table name.")
            self.conn.rollback()
            return None
        else:
            seq = self.get_nextval(SEQUENCES.get(sequence_name))

        pk = str(PREFIX.get(table))+'_'+str(seq)

        if columns:
            query = base_query + sql.SQL(" ({id_col}, {columns}) VALUES ({id}, {values})").format(
                id_col = sql.Identifier(str(PREFIX.get(table))+'_id'),
                columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
                id = sql.Placeholder(),
                values=sql.SQL(', ').join(sql.Placeholder() * len(values))
            )
        else:
            query = base_query + sql.SQL(" VALUES ({id}, {values})").format(
                id = sql.Placeholder(),
                values=sql.SQL(', ').join(sql.Placeholder() * len(values))
            )

        values = [pk] + values

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logging.info(f"Successfully inserted data into {self.schema}.{table}.")
            logging.info(f"Query: {query.as_string(self.conn)}")
            logging.info(f"Values: {values}")
        except (psycopg2.Error, psycopg2.DatabaseError) as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            self.conn.rollback()
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            self.conn.rollback()


    def update(self, table: str, set_columns: list, set_values: list, where: str) -> None:
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

        try:
            self.cursor.execute(query, set_values)
            self.conn.commit()
            logging.info(f"Successfully updated data in {self.schema}.{table}.")
            logging.info(f"Query: {query.as_string(self.conn)}")
            logging.info(f"Values: {set_values}")
        except psycopg2.Error as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            self.conn.rollback()
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            self.conn.rollback()

    def delete(self, table: str, where: str) -> None:
        query = sql.SQL("DELETE FROM {schema}.{table} WHERE {where}").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(table),
            where=sql.SQL(where)
        )

        try:
            self.cursor.execute(query)
            self.conn.commit() 
            logging.info(f"Successfully deleted data from {self.schema}.{table}.")
            logging.info(f"Query: {query.as_string(self.conn)}")
        except psycopg2.Error as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            self.conn.rollback()
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            self.conn.rollback()

    def get_nextval(self, sequence_name: str):
        query = sql.SQL("select nextval('{schema}.{seq}')").format(
            schema=sql.Identifier(dic.SCHEMA),
            seq=sql.Identifier(sequence_name)
        )

        try:
            self.cursor.execute(query)
            result = self.cursor.fetchone()[0]
            logging.info(f"Next value of sequence {sequence_name}: {result}")
            return result
        except psycopg2.Error as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            return None
        except Exception as e:
            logging.error(f"Query: {query.as_string(self.conn)}")
            logging.error(f"Unexpected error: {e}")
            return None

    def batch_insert(self, table: str, values: list, columns: list = None) -> None:
        base_query = "INSERT INTO {schema}.{table}".format(
            schema=self.schema,
            table=table
        )

        if columns:
            query = base_query + " ({id_col}, {columns}) VALUES ".format(
                id_col = str(PREFIX.get(table))+'_id',
                columns=', '.join(columns)
            )
        else:
            query = base_query + " VALUES "
            
        values_statement = ''

        for row in range(len(values)):
            seq = self.get_nextval(SEQUENCES.get(table))

            pk = str(PREFIX.get(table))+'_'+str(seq)
            formatted_string = ', '.join(f"'{item}'" for item in values[row])
            values_statement += "('" + pk +"',"+ formatted_string+"),"

        values_statement = values_statement[:-1]
        
        insert_query = (query+values_statement).replace("'nan'",'null')


        try:
            self.cursor.execute(insert_query)
            self.conn.commit()
            logging.info(f"Successfully inserted data into {self.schema}.{table}.")
            logging.info(f"Query: {insert_query}")
        except (psycopg2.Error, psycopg2.DatabaseError) as e:
            logging.error(f"Query: {insert_query}")
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            self.conn.rollback()
        except Exception as e:
            logging.error(f"Query: {insert_query}")
            logging.error(f"Unexpected error: {e}")
            self.conn.rollback()
    
    def __del__(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    

# if __name__ == '__main__':
#     db = Database(os.environ["DATABASE_URL"])
    
    # Example usage
    # db.insert(table='abcd', values=['kjunqiang@gmail.com', '11115354', 'JunQiang'])
    # db.insert(table='users', values=['yckng00@gmail.com', '00121800', 'YinChew'])
    # db.update('users', set_columns=['username'], set_values=['qwer'], where='id=3')
    # stock = db.select('stock')
    # print(pd.DataFrame(stock))
    # db.select('users', columns=['username'], where='id=3')
    # db.delete('users', where='id=3')
    # db.batch_insert(table='users', values=[['abcd@gmail.com', '1234567', 'abcd'], ['efgh@gmail.com', 'abcdefg', 'efgh'], ['ijkl@gmail.com', 'abcd1234', 'abcdefgh1234']])

# import psycopg2
# from psycopg2 import sql
# import os, re

# class Database():

#     # def __init__(self, conn):
#     #     self.conn = conn
#     #     self.cursor = conn.cursor()
#     #     self.username = ""

#     def __init__(self, database_url:str):
#         self.conn = psycopg2.connect(database_url)
#         self.cursor = self.conn.cursor()
#         self.schema = 'konghin'

#         self.username = ""
        

    # def authenticate(self, email, password):

    #     with self.cursor as cur:
    #         query = sql.SQL("SELECT * FROM konghin.users WHERE usr_email = %s AND usr_password = %s;")
    #         cur.execute(query, (email,password))
    #         res = cur.fetchone()
    #         self.conn.commit()
            
    #         if res:
    #             self.username = res[3]
    #             return True
    #         else:
    #             return False
            
    # def get_username(self):
    #     return self.username
    

    # def register_new_user(self, username, email, password):
    #     # Check if account exists using MySQL
    #     with self.cursor as cur:
    #         query = sql.SQL("SELECT * FROM konghin.users WHERE usr_email = %s;")
    #         cur.execute(query, (email))
    #         res = cur.fetchone()

    #         # If account exists show error and validation checks
    #         if res:
    #             msg = 'Account already exists!'
    #         elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
    #             msg = 'Invalid email address!'
    #         elif not re.match(r'[A-Za-z0-9]+', username):
    #             msg = 'Username must contain only characters and numbers!'
    #         elif not username or not password or not email:
    #             msg = 'Please fill out the form!'
    #         else:
    #             # Account doesn't exist, and the form data is valid, so insert the new account into the accounts table
    #             cur.execute('INSERT INTO konghin.users VALUES (NULL, %s, %s, %s)', (email, password, username,))
    #             self.conn.commit()
    #             msg = 'You have successfully registered!'