from flask import Flask, render_template, request, session, redirect, flash, jsonify
import os, re, logging
from datetime import datetime
import psycopg2
from psycopg2 import sql
from models import Database
import dictionary as dic
from datetime import datetime
from werkzeug.utils import secure_filename
import subprocess

UPLOAD_FOLDER = dic.IMPORT_DIR
ALLOWED_EXTENSIONS = {'csv','xlsx'}

app = Flask(__name__)
app.secret_key = b'k0ngh1n888'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
log_file = dic.LOG_DIR+str(datetime.now().strftime("%Y_%m_%d"))+'.log'

logging.basicConfig(filename=log_file,level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

conn = psycopg2.connect(os.environ["DATABASE_URL"])
db = Database(os.environ["DATABASE_URL"])

@app.route("/")
def home():
    return render_template("login.html")
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        db = Database(os.environ["DATABASE_URL"])
        if authenticate(email, password)==True:
            session['loggedin'] = True
            session['email'] = email
            logging.info(f"{email} successfully login at {datetime.now()}")
            stocks = db.select('stock', js=True)
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
        db = Database(os.environ["DATABASE_URL"])
        stocks = db.select('stock', js=True)
        return render_template("stocks.html", stocks=stocks)
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route("/addstocks")
def addstocks():
    # stocks as default home page
    if 'loggedin' in session:
        return render_template("addstocks.html")

    # User is not loggedin redirect to login page
    return redirect('login.html')

@app.route('/add-stock', methods=['POST'])
def add_stock():
    if 'loggedin' in session:
        if request.method == 'POST':
            # print(list(request.form.keys()))
            # print(list(request.form.values()))
            try:
                db.insert(table='stock',columns=list(request.form.keys()),values=list(request.form.values()))
            except ValueError:
                return "Invalid input. Please check your data and try again.", 400
            stocks = db.select('stock', js=True)
            return render_template("stocks.html", stocks=stocks)
    return redirect('login.html')
    
@app.route('/update-stock/<stock_id>', methods=['GET'])
def edit_stock(stock_id):
    if 'loggedin' in session:
        db = Database(os.environ["DATABASE_URL"])
        stock = db.select('stock', where="stk_id='{stk_id}'".format(stk_id=stock_id))
        if stock[0]['stk_pur_date']:
            pur_date_object = datetime.fromisoformat(stock[0].get('stk_pur_date').replace('Z', '+00:00'))
            # datetime.fromisoformat(pur_date_string.replace('Z', '+00:00'))
            stock[0]['stk_pur_date'] = pur_date_object.strftime('%Y-%m-%d')
        if stock[0]['stk_sell_date']    :
            stock[0]['stk_sell_date'] = datetime.fromisoformat(stock[0].get('stk_sell_date'))
        return render_template('updatestock.html', stock=stock[0])
    return redirect('login.html')

@app.route('/updatestock', methods=['POST'])
def update_stock_view():
    print(request.form)
    if 'loggedin' in session:
        try:
            db.update(table='stock',set_columns=list(request.form.keys()),set_values=list(request.form.values()), where="stk_id='{stk_id}'".format(stk_id=request.form['stk_id']))
        except ValueError:
            return "Invalid input. Please check your data and try again.", 400
        stocks = db.select('stock', js=True)
        return render_template("stocks.html", stocks=stocks)
    return redirect('login.html')
    # stock_id = request.form['stk_id']
    # Retrieve other form data
    # stock_data = {
    #     'stk_gold_type': request.form['stk_gold_type'],
    #     'stk_type': request.form['stk_type'],
    #     'stk_pattern': request.form['stk_pattern'],
    #     'stk_weight': request.form['stk_weight'],
    #     'stk_size': request.form['stk_size'],
    #     'stk_length': request.form['stk_length'],
    #     'stk_labor_cost': request.form['stk_labor_cost'],
    #     'stk_labor_sell': request.form['stk_labor_sell'],
    #     'stk_pur_date': request.form['stk_pur_date'],
    #     'stk_sell_date': request.form['stk_sell_date'],
    #     'stk_gold_cost': request.form['stk_gold_cost'],
    #     'stk_gold_sell': request.form['stk_gold_sell'],
    #     'stk_status': request.form['stk_status'],
    #     'stk_profit': request.form['stk_profit'],
    # }
    return 
    # update_stock(stock_id, stock_data)  # Update stock data in database
    # return redirect(url_for('stocks_list'))

# @app.route('/delete-stock/<stock_id>', methods=['GET'])
# def delete_stock(stock_id):
#     if 'loggedin' in session:
#         db = Database(os.environ["DATABASE_URL"])
#         stock = db.select('stock', where="stk_id='{stk_id}'".format(stk_id=stock_id))
#         if stock[0]['stk_pur_date']:
#             pur_date_object = datetime.fromisoformat(stock[0].get('stk_pur_date').replace('Z', '+00:00'))
#             # datetime.fromisoformat(pur_date_string.replace('Z', '+00:00'))
#             stock[0]['stk_pur_date'] = pur_date_object.strftime('%Y-%m-%d')
#         if stock[0]['stk_sell_date']    :
#             stock[0]['stk_sell_date'] = datetime.fromisoformat(stock[0].get('stk_sell_date'))
#         return render_template('updatestock.html', stock=stock[0])
#     return redirect('login.html')

@app.route('/delete/<stock_id>', methods=['POST'])
def deletestock(stock_id):
    # stk_id = request.form.get('stk_id')
    stk_id = stock_id
    if stk_id:
        # Your logic to delete the product with the given stk_id
        # Example:
        # product = Product.query.filter_by(stk_id=stk_id).first()
        # if product:
        #     db.session.delete(product)
        #     db.session.commit()
        
        # After deletion, redirect to the stocks page or any other appropriate page
        db.delete('stock',where="stk_id='{stk_id}'".format(stk_id=stk_id))
        stocks = db.select('stock', js=True)
        return render_template("stocks.html", stocks=stocks)
    return 'Stock ID is missing', 400

@app.route('/batch-import', methods=['GET', 'POST'])
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

@app.route('/your-endpoint', methods=['POST'])
def handle_data():
    data = request.json
    return jsonify({"status": "success", "data": data})

@app.route("/purchases")
def purchases():
    if 'loggedin' in session:
        db = Database(os.environ["DATABASE_URL"])
        stocks = db.select('purchases', js=True)
        return render_template("purchases.html", purchases=purchases)
    
    # User is not loggedin redirect to login page
    return redirect('login.html')

if __name__ == "__main__":
    app.run(debug=True)
