from flask import Flask, render_template, request, session, redirect, flash,send_file
import os, re, logging
from datetime import datetime
import psycopg2
from psycopg2 import sql
from models import Database
import dictionary as dic
import subprocess
from io import BytesIO
from werkzeug.utils import secure_filename
import pandas as pd

UPLOAD_FOLDER = dic.IMPORT_DIR
ALLOWED_EXTENSIONS = {'csv','xlsx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = b'k0ngh1n888'

log_file = dic.LOG_DIR+str(datetime.now().strftime("%Y_%m_%d"))+'.log'

logging.basicConfig(filename=log_file,level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

conn = psycopg2.connect(os.environ["DATABASE_URL"])

@app.route("/")
def home():
    return render_template("login.html")
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        database = Database(os.environ["DATABASE_URL"])
        if authenticate(email, password)==True:
            session['loggedin'] = True
            session['email'] = email
            logging.info(f"{email} successfully login at {datetime.now()}")
            stocks = database.select('stock', js=True)
            # print(stocks)
            # stocks =[('STK_100001', 'Bracelet', Decimal('12.8'), Decimal('14.5'), None, Decimal('120'), None, datetime.date(2024, 1, 1), None, Decimal('345'), None, 'IN STOCK', None, 'cartier', '916')]

            return render_template("stocks.html", stocks=stocks)
        else:
            msg = "Incorrect username/password!"
            return render_template("login.html", msg=msg)
    else:
        return render_template("login.html", msg='')

def authenticate(email, password):

    with conn.cursor() as cur:
        query = sql.SQL("SELECT * FROM konghin.users WHERE usr_email = %s AND usr_password = %s;")
        cur.execute(query, (email,password))
        res = cur.fetchone()
        conn.commit()
        
        if res:
            # username = res[3]
            return True
        else:
            return False
            

def logout():
    # Remove session data, this will log the user out
   logging.info(f"{session['email']} logout at {datetime.now()}")
   
   session.pop('loggedin', None)
   session.pop('email', None)
   
   # Redirect to login page
   return redirect('login.html')

# this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form and 'username' in request.form:
        # Create variables for easy access
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        with conn.cursor() as cur:
            query = sql.SQL("SELECT * FROM konghin.users WHERE usr_email = %s;")
            cur.execute(query, (email, ))
            res = cur.fetchone()

            # If account exists show error and validation checks
            if res:
                # msg = 'Account already exists!'
                flash('Account already exists!', category='warning')
                return render_template('register.html')
                
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                # msg = 'Invalid email address!'
                flash('Invalid email address!', category='warning')
                return render_template('register.html')
            
            elif not re.match(r'[A-Za-z0-9]+', username):
                # msg = 'Username must contain only characters and numbers!'
                flash('Username must contain only characters and numbers!', category='warning')
                return render_template('register.html')
            
            elif not username or not password or not email:
                # msg = 'Please fill out the form!'
                flash('Please fill out the form!', category='warning')
                return render_template('register.html')
            else:
                # Account doesn't exist, and the form data is valid, so insert the new account into the accounts table
                cur.execute('INSERT INTO konghin.users VALUES (%s, %s, %s, %s)', ('asd', email, password, username,))
                conn.commit()
                flash('Account created! Please proceed to login page to login.', category='success')
                return render_template('register.html')
                # msg = 'You have successfully registered!'

        
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

        # if user:
        #     flash('Email already exists.', category='error')
        # elif len(email) < 4:
        #     flash('Email must be greater than 3 characters.', category='error')
        # elif len(first_name) < 2:
        #     flash('First name must be greater than 1 character.', category='error')
        # elif password1 != password2:
        #     flash('Passwords don\'t match.', category='error')
        # elif len(password1) < 7:
        #     flash('Password must be at least 7 characters.', category='error')
        # else:
        #     new_user = User(email=email, first_name=first_name, password=generate_password_hash(
        #         password1, method='sha256'))
        #     db.session.add(new_user)
        #     db.session.commit()
        #     login_user(new_user, remember=True)
        #     flash('Account created!', category='success')
        #     return redirect(url_for('views.home'))

@app.route("/stocks")
def stocks():
    # stocks as default home page
    if 'loggedin' in session:
        # User is loggedin show them the home page
        database = Database(os.environ["DATABASE_URL"])
        stocks = database.select('stock', js=True)
        return render_template("stocks.html", stocks=stocks)
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route('/', methods=['GET', 'POST'])
def uploadFile():
    if request.method == 'POST':
        f = request.files.get('file')
 
        data_filename = secure_filename(f.filename)
 
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],data_filename))
 
        session['uploaded_data_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'],data_filename)
        result = subprocess.run(['python', r'./IMtool app/website/Import.py'], capture_output=True, text=True)
        print('STDOUT:', result.stdout)
        print('STDERR:', result.stderr)
        print('Return Code:', result.returncode)
        return 'File Uploaded Successful'
    return 'FAILED'

if __name__ == "__main__":
    app.run(debug=True)
