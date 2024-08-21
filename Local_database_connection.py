import MySQLdb

conn = MySQLdb.connect (host = "127.0.0.1",
                        user = "root",
                        passwd = "Konghin1928",
                        db='konghin')
cursor = conn.cursor ()
cursor.execute ("SHOW TABLES")
row = cursor.fetchall ()
print(row)
cursor.close ()
conn.close ()