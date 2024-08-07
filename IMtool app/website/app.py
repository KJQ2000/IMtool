from flask import Flask, render_template, request
import os
import psycopg2
from psycopg2 import sql
from models import User


app = Flask(__name__)

conn = psycopg2.connect(os.environ["DATABASE_URL"])

<<<<<<< HEAD
=======
def authenticate(email,password):

    with conn.cursor() as cur:
        query = sql.SQL("SELECT * FROM konghin.users WHERE email = %s AND password = %s;")
        cur.execute(query, (email,password))
        res = cur.fetchone()
        conn.commit()
        if res:
            return True
        else:
            return False

>>>>>>> 81e86d33f4d0c0eac02791453b6daaf27432adaf

@app.route("/")
def home():
    return render_template("login.html")
    
@app.route('/login', methods=['POST'])
def login():
    username = request.form['email']
    password = request.form['password']
    user = User(conn)
    if user.authenticate(username, password)==True:
        return render_template("base.html")
    else:
        return "Invalid credentials, please try again."

if __name__ == "__main__":
    app.run(debug=True)
