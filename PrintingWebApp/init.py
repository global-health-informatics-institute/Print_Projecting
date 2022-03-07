import os
import time

from flask import Flask, render_template, request, url_for, redirect, session, flash
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

UPLOAD_FOLDER = 'uploads'
path = "uploads"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "super secret key"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'ghii'
app.config['MYSQL_PASSWORD'] = 'mypassword'
app.config['MYSQL_DB'] = 'Printing'

mysql = MySQL(app)


@app.route('/')
def home():
    return render_template('UserLogin.html')


@app.route('/Admin_Dashboard')
def Admin_Dashboard():
    if "u_id" in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users")
        data = cur.fetchall()
        cur.close()
        return render_template('Admin_Dashboard.html', users=data)
    else:
        return render_template('AdminLohin.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    u_id = session['u_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE u_id=%s", (session['u_id'],))
    rec = cur.fetchone()
    username = rec[1]

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            department = request.form['department']
            copies = request.form['copies']
            cur.execute("INSERT INTO print( u_id, department, filename, copies) VALUES(%s,%s,%s,%s)",
                        (u_id, department, filename, copies))
            mysql.connection.commit()
            cur.execute("SELECT * FROM print WHERE u_id=%s", (session['u_id'],))
            p_rec = cur.fetchone()
            copies = p_rec[4]
            x = 0
            while x < copies:
                print_doc()
                x = x + 1
            delete_file()
            return render_template('Print.html', user=username)

    return render_template('Print.html', user=username)


@app.route('/dropdown', methods=['GET'])
def dropdown():
    dir_list = os.listdir(path)
    return render_template('Print.html', dir_list=dir_list)


@app.route('/print_doc')
def print_doc():
    l_files = os.listdir(path)

    for file in l_files:

        file_path = f'{path}\\{file}'

        if os.path.isfile(file_path):
            try:
                os.startfile(file_path, 'print')
                time.sleep(5)
                return render_template('Print.html', msg="Printing file!!!")
            except OSError as e:
                return render_template('Print.html', msg="file could not be printed!" + e.strerror)
        else:
            return render_template('Print.html', msg="{file} is not a file, so can not be printed!")

    return render_template('Print.html', msg="No file to print!!!")


@app.route('/delete_file')
def delete_file():
    l_files = os.listdir(path)
    for file in l_files:
        file_path = f'{path}\\{file}'
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                return render_template('Print.html')
            except OSError as e:
                return render_template('Print.html', msg="Failed to remove file" + e.strerror)
        else:
            return render_template('Print.html', msg="Directory can not be deleted")

    return render_template('Print.html', msg="No file to delete!!!")


@app.route('/staff_login', methods=['GET', 'POST'])
def staff_login():
    msg = ""
    if request.method == 'POST':
        user_details = request.form
        user_name = user_details['user_name']
        password = user_details['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE user_name=%s AND password=%s", (user_name, password))
        record = cur.fetchone()
        if record:
            if record[3] == 'user':
                session["loggedin"] = True
                session["u_id"] = record[0]
                return redirect(url_for('upload_file'))
            else:
                session["loggedin"] = True
                session["u_id"] = record[0]
                return redirect(url_for('Admin_Dashboard'))

        else:
            msg = "Incorrect Username/Password. Try Again!!! "
            return render_template('UserLogin.html', msg=msg)
    return render_template('UserLogin.html', msg=msg)


@app.route('/ulogout')
def logout():
    session.pop('loggedin', None)
    session.pop('u_id', None)
    return render_template('UserLogin.html')


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':

        user_details = request.form
        user_name = user_details['user_name']
        password = user_details['password']
        role = user_details['role']
        # encryptedpassword = generate_password_hash(password, method='sha256')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE user_name=%s", [user_name])
        record = cur.fetchall()

        if record:
            flash("username already exists, try again")
            return redirect(url_for('Admin_Dashboard'))
        else:
            cur.execute("INSERT INTO users( user_name, password, role) VALUES(%s,%s, %s)", (user_name, password, role))
            mysql.connection.commit()
            flash("Data Inserted Successfully")
            return redirect(url_for('Admin_Dashboard'))


@app.route('/delete/<string:id_data>', methods=['GET', 'POST'])
def delete(id_data):
    flash("Data deleted successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE u_id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('Admin_Dashboard'))


@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        user_details = request.form
        u_id = user_details['u_id']
        user_name = user_details['user_name']
        password = user_details['password']
        role = user_details['role']
        cur = mysql.connection.cursor()
        cur.execute("""
        UPDATE users
        SET user_name = %s, password = %s, role = %s
        WHERE u_id = %s  """, (user_name, password, role, u_id))
        flash("Data Updated successfully")
        mysql.connection.commit()
        return redirect(url_for('Admin_Dashboard'))


if __name__ == "__main__":
    app.run(debug=True)
