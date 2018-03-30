from flask import Flask, render_template, request, redirect, flash, session
import re
from mysqlconnection import MySQLConnector
import md5 # import md5 module to generate a hash

# create a regular expression object that we can use run operations on
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
NAME_REGEX = re.compile(r'^[a-zA-Z]+$')

app = Flask(__name__)
mysql = MySQLConnector(app,'the_wall')
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
		query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())"
		data = {'first_name': request.form['fn'], 'last_name': request.form['ln'], 'email': request.form['email'], 'password': md5.new(request.form['pw']).hexdigest()}
		mysql.query_db(query, data)
		flash("You have successfully registered your information!")
		# store newly registered user id in session upon login
		query = "SELECT id FROM users WHERE email = '{}'".format(request.form['email'])
		data = { 'email': request.form['email'] }
		session['user_id']= mysql.query_db( query, data )[0]['id']
		# store newly registered user first name in session upon login
		query = "SELECT first_name FROM users WHERE id = '{}'".format(session['user_id'])
		data = { 'id': session['user_id'] }
		session['first_name'] = mysql.query_db( query, data )[0]['first_name']
		return redirect('/wall')
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
	session['user_id'] = mysql.query_db( query, data )[0]['id']
	# store registered user name in session upon login
	query = "SELECT first_name FROM users WHERE id = '{}'".format(session['user_id'])
	data = { 'id': session['user_id'] }
	session['first_name'] = mysql.query_db( query, data )[0]['first_name']
	flash("You are successfully logged in!")
	return redirect('/wall')

@app.route('/wall')
def wall():
	if "user_id" not in session:
		return render_template('index.html')
	else:
		query = "SELECT users.first_name, users.last_name, messages.content, messages.id, messages.users_id, DATE_FORMAT(messages.created_at, '%M %D, %Y') AS date FROM messages JOIN users ON users.id = messages.users_id ORDER BY messages.created_at DESC"
		messages = mysql.query_db(query)
		query = "SELECT users.first_name, users.last_name, comments.content, comments.messages_id, DATE_FORMAT(comments.created_at, '%M %D, %Y') AS date FROM comments JOIN users ON users.id = comments.users_id ORDER BY comments.created_at ASC"
		comments = mysql.query_db(query)
	return render_template('wall.html', messages=messages, comments=comments)

@app.route('/post_message', methods=['POST'])
def post():
	query = "INSERT INTO messages (content, created_at, updated_at, users_id) VALUES (:content, NOW(), NOW(), :users_id)"
	data = {'content': request.form['post_message'], 'users_id': session['user_id'] }
	mysql.query_db(query, data)
	flash("Your message has been posted.")
	return redirect('/wall')

@app.route('/comment/<message_id>', methods=['POST'])
def comment(message_id):
	query = "INSERT INTO comments (content, created_at, updated_at, messages_id, users_id) VALUES (:content, NOW(), NOW(), :messages_id, :users_id)"
	data = {'content': request.form['comment'], 'messages_id': message_id, 'users_id': session['user_id'] }
	mysql.query_db(query, data)
	flash("Your comment has been saved.")
	return redirect('/wall')

@app.route('/delete_message/<message_user_id>/<message_id>', methods=['POST'])
def delete_message(message_user_id, message_id):
	if session['user_id'] == int(message_user_id):
		query = "DELETE FROM messages WHERE id = :message_id"
		data = { 'message_id': message_id }
		mysql.query_db(query, data)
		flash("You have succesfully deleted your message.")
	else:
		flash("You can only delete your own messages!")
	return redirect('/wall')

@app.route('/logoff')
def logoff():
	session.pop('user_id')
	session.pop('first_name')
	flash("You have successfully logged out.")
	return redirect('/')

app.run(debug=True)