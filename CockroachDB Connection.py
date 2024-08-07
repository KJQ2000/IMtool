import os
import psycopg2
from psycopg2 import sql
import logging
import dictionary as dic


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Database:
    def __init__(self, database_url: str):
        self.conn = psycopg2.connect(database_url)
        self.cursor = self.conn.cursor()
        self.schema = 'konghin'

    def select(self, table: str, columns: list = None, where: str = None):
        
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
            logging.info(f"Successfully selected data from {self.schema}.{table}.")
            logging.info(f"Query: {query.as_string(self.conn)}")
            logging.info(f"Results: {results}")
            return results
        except psycopg2.Error as e:
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return None

    def insert(self, table: str, values: list, columns: list = None) -> None:
        base_query = sql.SQL("INSERT INTO {schema}.{table}").format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(table)
        )

        if columns:
            query = base_query + sql.SQL(" ({columns}) VALUES ({values})").format(
                columns=sql.SQL(', ').join(map(sql.Identifier, columns)),
                values=sql.SQL(', ').join(sql.Placeholder() * len(values))
            )
        else:
            query = base_query + sql.SQL(" VALUES ({values})").format(
                values=sql.SQL(', ').join(sql.Placeholder() * len(values))
            )

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            logging.info(f"Successfully inserted data into {self.schema}.{table}.")
            logging.info(f"Query: {query.as_string(self.conn)}")
            logging.info(f"Values: {values}")
        except (psycopg2.Error, psycopg2.DatabaseError) as e:
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            self.conn.rollback()
        except Exception as e:
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
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            self.conn.rollback()
        except Exception as e:
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
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            self.conn.rollback()
        except Exception as e:
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
            logging.error(f"Database error: {e.pgcode} - {e.pgerror}")
            logging.error(f"Error details: {e.diag.message_detail}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return None

    def __del__(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

if __name__ == '__main__':
    db = Database(os.environ["DATABASE_URL"])
    # Example usage
    # db.insert(table='users', values=[3, 'abcd@gmail.com', '121212', 'abcd'])
    # db.update('users', set_columns=['username'], set_values=['qwer'], where='id=3')
    # db.select('users')
    # db.select('users', columns=['username'], where='id=3')
    # db.delete('users', where='id=3')

    results=db.get_nextval(dic.USER_SEQ)
    print(results)
