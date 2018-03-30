from flask import Flask, render_template, request, redirect, flash, session
import re
from mysqlconnection import MySQLConnector
import md5 # import md5 module to generate a hash

# create a regular expression object that we can use run operations on
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
NAME_REGEX = re.compile(r'^[a-zA-Z]+$')

app = Flask(__name__)
mysql = MySQLConnector(app,'login and registration')
app.secret_key = "unicorns"

@app.route('/')
def home():
	return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
	if not NAME_REGEX.match(request.form['fn']):
		flash("First name cannot be blank and can only contain valid letters!")
	elif len(request.form['fn']) < 2:
		flash("First name must contain at least 2 characters!")
	elif not NAME_REGEX.match(request.form['ln']):
		flash("Last name cannot be blank and can only contain valid letters!")
	elif len(request.form['ln']) < 2:
		flash("Last name must contain at least 2 characters!")
	elif not EMAIL_REGEX.match(request.form['email']):
		flash("Invalid Email Address!")
	elif len(request.form['pw']) < 9:
		flash("Password must contain more than 8 characters!")
	elif not request.form['pw'] == request.form['confirm_pw']:
		flash("Both passwords must match!")
	else:
		flash("You have successfully registered your information!")
		query = "INSERT INTO users (first_name, last_name, email, password) VALUES (:first_name, :last_name, :email, :password)"
		data = {'first_name': request.form['fn'],
				'last_name': request.form['ln'],
				'email': request.form['email'],
				'password': md5.new(request.form['pw']).hexdigest()
				}
		mysql.query_db(query, data)
		# store newly registered user id in session upon login
		query = "SELECT id FROM users WHERE email = '{}'".format(request.form['email'])
		data = { 'email': request.form['email'] }
		session['user_id']= mysql.query_db( query, data )[0]['id']
		print session['user_id']
		return redirect('/success')

	return redirect('/')

@app.route('/login', methods=['POST'])
def login():
	query = "SELECT * FROM users WHERE users.email = '{}'".format(request.form['email'])
	data = { 'email': request.form['email']}
	user = mysql.query_db(query, data)

	if not user:
		flash("No registered email for this user.")
		return redirect('/')
	else:
		if user[0]['password'] != md5.new(request.form['pw']).hexdigest():
			flash("Invalid Password.")
			return redirect('/')

	# store registered user id in session upon login
	query = "SELECT id FROM users WHERE email = '{}'".format(request.form['email'])
	data = { 'email': request.form['email'] }
	session['user_id']= mysql.query_db( query, data )[0]['id']
	print session['user_id']

	flash("Your are successfully logged in!")
	return redirect('/success')

@app.route('/logoff')
def logoff():
	session.pop['user_id']
	return redirect('/')

@app.route('/success')
def success():
	query = "SELECT * FROM users"
	users = mysql.query_db(query)
	return render_template('success.html', users=users)

@app.route('/remove', methods=["POST"])
def remove():
	query = "DELETE FROM users WHERE id = :id"
	data = { 'id': request.form['id']}
	mysql.query_db(query, data)
	return redirect('/success')

app.run(debug=True)