from flask import Flask,render_template, request, redirect, url_for, session,send_file,jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import smtplib
import os
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
import random
from datetime import datetime
import mysql.connector

 
app = Flask(__name__)
#from app import routes, models
 
app.secret_key = 'your secret key'

aims_email='tarushi.tanejag1112@gmail.com'

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="1147",
    database="aims",
    auth_plugin='mysql_native_password'
)
cursor = conn.cursor(dictionary=True) 
user_type=''
user={}

def init_db():
    with app.app_context():
        with app.open_resource('schema.sql', mode='r') as f:
            sql_commands = f.read().split(';')
            for command in sql_commands:
                if command.strip():
                    cursor.execute(command)
        conn.commit()

def generate_otp(length=6):
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

def send_email(sender,receiver):
    otp = generate_otp()
    cursor.execute(
            'delete from otp_table where user_id = %s', (receiver,) )
    conn.commit()
    cursor.execute('insert into otp_table (user_id,otp,created_at) values (%s,%s,%s)',(receiver,otp,datetime.now(),))
    conn.commit()
    text=f"Subject : OTP for AIMS Login\n\n Your login otp is {otp} \n\n This is valid for 5 minutes"
    server = smtplib.SMTP("smtp.gmail.com",587)
    server.starttls()

    server.login(sender,"eipn qsmt ffbv zqjm")               # dummy passcode. Sender should be your email id. passcode is app password. Explained in detail in readme file
    server.sendmail(sender,receiver,text)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/process_login',methods=['GET','POST'])
def process_login():
    if request.method=='POST' and 'username' in request.form:
        email_id=request.form['username']
        send_email(aims_email,email_id)
        return redirect(url_for("login_otp",email_id=email_id))

@app.route('/login_otp/<email_id>',methods=['GET','POST'])
def login_otp(email_id):
    return render_template('login_otp.html',email_id=email_id)

@app.route('/process_otp/<email_id>',methods=['GET','POST'])
def process_otp(email_id):
    if request.method=='POST' and 'otp' in request.form:
        otp = request.form['otp']
        cursor.execute('select otp from otp_table where user_id = %s and TIMESTAMPDIFF(MINUTE, created_at, NOW()) <= 5',(email_id,))
        otp_given=cursor.fetchone()
        if otp_given:
            if otp_given['otp']==otp:
                cursor.execute('select * from user where email_id = %s and not exists(select request_status from user_requests ur where ur.user_id=user.user_id)',(email_id,))
                global user
                user=cursor.fetchone()
                print(f"user:{user}")
                if user:
                    if user['role']=='student':
                        session['role']=1
                        session['loggedin']=True
                        return redirect(url_for("dashboard_student",username=user['username']))
                    elif user['role']=='faculty':
                        session['role']=2
                        session['loggedin']=True
                        return redirect(url_for("dashboard_faculty",username=user['username']))
                    elif user['role']=='admin':
                        session['role']=3
                        session['loggedin']=True
                        return redirect(url_for("dashboard_admin",username=user['username']))
                else:
                    msg="Email_id user does not exist!! Please re enter correct email id"
                    return render_template("login.html",msg=msg)
            else:
                msg="Incorrect OTP !! Please try again"
                return render_template("login_otp.html",email_id=email_id,msg=msg)
        else:
            msg="Please enter a valid OTP"
            return render_template("login_otp.html",email_id=email_id,msg=msg)

                    

@app.route('/signup_main',methods=['GET','POST'])
def signup_main():
    return render_template("signup_main.html")



@app.route('/dashboard_student/<username>')
def dashboard_student(username):
    if session['role']==1:
        cursor.execute('SELECT * FROM student where user_id = %s',(user['user_id'],)) 
        student = cursor.fetchone()
        cursor.execute('SELECT u.username FROM faculty f join user u on f.user_id = u.user_id where f.dep=%s and faculty_advisor=%s',(student['dep'],1,))
        fa=cursor.fetchone()
        cursor.execute('SELECT * FROM student_course sc JOIN course c on sc.course_id = c.course_id where sc.student_id = %s',(student['student_id'],))  
        courses = cursor.fetchall()
        return render_template("dashboard_student.html",user=user,student=student,courses=courses,fa=fa['username'])
    else:
        return "You are not authorised to view this page!!"

@app.route('/dashboard_faculty/<username>')
def dashboard_faculty(username):
    if session['role']==2:
        cursor.execute('SELECT * FROM faculty where user_id = %s',(user['user_id'],))  
        faculty = cursor.fetchone()
        cursor.execute('SELECT * FROM course where faculty_id = %s',(faculty['faculty_id'],))  
        courses = cursor.fetchall()
        print(f"courses : {courses}")
        return render_template("faculty_dashboard.html",user=user,faculty=faculty,courses=courses)
    else:
        return "You are not authorised to view this page!!"

@app.route('/dashboard_admin')
def dashboard_admin():
    if session['role']==3:
        cursor.execute('SELECT * FROM admin where user_id = %s',(user['user_id'],))  
        admin = cursor.fetchone()
        return render_template("dashboard_admin.html",user=user)
    else:
        return "You are not authorised to view this page!!"

@app.route('/create_course/<faculty_id>',methods=['GET','POST'])
def create_course(faculty_id):

    if session['role']==2:
        if request.method=='POST':
            course_name=request.form['coursename']
            ltpc=request.form['LTPC']
            sem=request.form['semester']
            code=request.form['coursecode']
            year=request.form['year']
            dep=request.form['department']
            cursor.execute('INSERT INTO course(course_name,faculty_id,course_code,LTPC,sem,course_status,credits) VALUES (%s, %s, %s, %s, %s,%s,%s)', (course_name, faculty_id, code, ltpc, sem,'pending_admin_approval',ltpc[-1],))
            conn.commit()
            return render_template('coursefloat.html',username=user['username'],faculty_id=faculty_id,msg='Course created successfully. Students shall be able to enroll after admin approval!!')
        return render_template('coursefloat.html',username=user['username'],faculty_id=faculty_id,msg='')
    else:
        return "You are not authorised to view this page!!"

@app.route('/pending_approvals/<faculty_id>',methods=['GET','POST'])
def pending_approvals(faculty_id):
    if session['role']==2:
        if request.method=='POST':
            student_id = request.json.get('student_id')
            course_id = request.json.get('course_id')
            action = request.json.get('action')
            curr_status=request.json.get('status')
            print(f'{student_id} {course_id} {action} {curr_status}')
            new_status=""

            if action == "approve":
                if curr_status == 'pending instructor approval':
                    new_status = "pending advisor approval"
                else:
                    new_status='enrolled'
            elif action == "reject":
                new_status = "rejected"
            cursor.execute(
            'UPDATE student_course SET status = %s WHERE student_id = %s AND course_id = %s',(new_status, student_id, course_id))
            conn.commit()
            cursor.execute('SELECT u.username,s.entry_no,stu_course.* from (select sc.student_id,sc.status,c.course_name,c.course_id FROM course c JOIN student_course sc on sc.course_id=c.course_id where c.faculty_id = %s and sc.status = %s) stu_course JOIN student s on s.student_id=stu_course.student_id JOIN user u ON s.user_id = u.user_id',(faculty_id,'pending instructor approval',))
            students = cursor.fetchall()
            cursor.execute('SELECT s.student_id,u.username,s.entry_no,sc.status,c.course_name,c.course_id from student s JOIN user u on s.user_id = u.user_id JOIN student_course sc on sc.student_id=s.student_id JOIN course c on c.course_id = sc.course_id  where s.dep in (select dep from faculty where faculty_id = %s and faculty_advisor = %s) and sc.status = %s',(faculty_id,1,'pending advisor approval'))
            students.extend(cursor.fetchall())
            return jsonify({"success": True, "students": students,"faculty_id":faculty_id,"username":user['username']})
        else:
            cursor.execute('SELECT u.username,s.entry_no,stu_course.* from (select sc.student_id,sc.status,c.course_name,c.course_id FROM course c JOIN student_course sc on sc.course_id=c.course_id where c.faculty_id = %s and sc.status = %s) stu_course JOIN student s on s.student_id=stu_course.student_id JOIN user u ON s.user_id = u.user_id',(faculty_id,'pending instructor approval',))
            students = cursor.fetchall()
            cursor.execute('SELECT s.student_id,u.username,s.entry_no,sc.status,c.course_name,c.course_id from student s JOIN user u on s.user_id = u.user_id JOIN student_course sc on sc.student_id=s.student_id JOIN course c on c.course_id = sc.course_id  where s.dep in (select dep from faculty where faculty_id = %s and faculty_advisor = %s) and sc.status = %s',(faculty_id,1,'pending advisor approval',))
            students.extend(cursor.fetchall())
            print(f'sending students{students}')
            return render_template('faculty_approval.html',students=students,faculty_id=faculty_id,username=user['username'])
    else:
       return "You are not authorised to view this page!!" 

@app.route('/courses_available/<username>',methods=['GET','POST'])
def courses_available(username):
    if session['role']==1:
        cursor.execute('SELECT * FROM student where user_id = %s',(user['user_id'],))  
        student = cursor.fetchone()
        if request.method=='POST':
            course_id = request.json.get('course_id')
            action = request.json.get('action')
            faculty_id = request.json.get('faculty_id')
            print(f"{username}")
            cursor.execute('select status from student_course where student_id =%s and course_id =%s',(student['student_id'],course_id,) )
            curr_status=cursor.fetchone()
            if action == 'credit':
                if curr_status['status'] and curr_status['status']!='dropped':
                    return jsonify({"success":True,"msg":'Already credited'})
                cursor.execute('update course set no_of_enrollments = no_of_enrollments+1 where course_id = %s',(course_id,))
                cursor.execute('insert into student_course(student_id,course_id,status,grade) values(%s,%s,%s,%s)',(student['student_id'],course_id,'pending instructor approval','NA',))
                conn.commit()
                return jsonify({"success":True,"msg":'Successfully credited'})
            elif action == 'audit':
                cursor.execute('update student_course set status = %s where student_id=%s and course_id = %s',('audit',student['student_id'],course_id,))
                conn.commit()
                return jsonify({"success":True,"msg":'Successfully audited'})
            else:
                if not curr_status['status']:
                    return jsonify({"success":True,"msg":'Cannot drop a course that is not enrolled'})
                cursor.execute('update student_course set status = %s where student_id=%s and course_id = %s',('dropped',student['student_id'],course_id,))
                conn.commit()
                return jsonify({"success":True,"msg":'Successfully dropped'})
        cursor.execute('SELECT * from course c join faculty f on f.faculty_id=c.faculty_id join user u on u.user_id=f.user_id where c.admin_approval_status = %s',('approved',))  
        courses = cursor.fetchall()
        return render_template("courses_available.html",user=user,student=student,courses=courses)
    else:
        return "You are not authorised to view this page!!"

@app.route('/signup',methods=['GET','POST'])
def signup_process():
 
    '''This handles the signup process for both mentees and mentors. After validating the form
    data, it inserts the user's information into the respective database. For mentors, it also
    saves the uploaded resume file. Upon successful signup, it sends a confirmation email to
    the user's provided email address.'''
    
    msg=''
    if request.method=='POST':
        if user_type=="student": 
            name = request.form['name']
            entry_no = request.form['entry_no']
            email_id = request.form['email']
            degree = request.form['degree']
            department = request.form['department']
            year_of_entry=request.form['year_of_entry']
            cursor.execute('insert into user(username,email_id,role) values(%s,%s,%s)',(name,email_id,'student'))
            cursor.execute('select user_id from user where email_id = %s',(email_id,))
            user_id=cursor.fetchone()
            cursor.execute('insert into user_requests(user_id) values(%s)',(user_id['user_id'],))
            cursor.execute(
            'INSERT INTO student(user_id,entry_no,degree,dep,year_of_entry) VALUES(%s,%s,%s, %s,%s)', (user_id['user_id'],entry_no,degree,department,year_of_entry,) )
            conn.commit()
            print('commited')
            return render_template("login.html",msg="Signup Successful. You will be able to login after admin approval")
        elif user_type =="faculty":
            name = request.form['name']
            email_id = request.form['email']
            dep=request.form['department']
            cursor.execute('insert into user(username,email_id,role) values(%s,%s,%s)',(name,email_id,'faculty'))
            cursor.execute('select user_id from user where email_id = %s',(email_id,))
            user_id=cursor.fetchone()
            cursor.execute('insert into user_requests(user_id) values %s',(user_id['user_id'],))
            cursor.execute(
            'INSERT INTO faculty(user_id,dep) VALUES(%s, %s)', (user_id['user_id'],dep,) )
            conn.commit()
            return render_template("login.html",msg="Signup Successful.You will be able to login after admin approval ")


@app.route('/user_category',methods=['GET','POST'])
def user_category():
 
    '''This handles the selection of user category (mentee or mentor).After receiving the user's
    selection, it renders the signup form based on the selected category.'''
    
    global user_type
    user_type=request.form['button']
    if(user_type=='student'):   
        return render_template("signup_student.html")
    elif(user_type=='faculty'):
        return render_template("signup_faculty.html")

@app.route('/admin/approve_user', methods=['GET','POST'])
def approve_user():
    if session['role'] != 3:
        return "You are not authorized to perform this action!", 403
    if request.method == 'POST':
        request_id = request.json.get('request_id')
        action = request.json.get('action')  

        if action == 'approve':
            cursor.execute('delete from user_requests WHERE request_id = %s', (request_id,))
        elif action == 'reject':
            cursor.execute('UPDATE user_requests SET request_status = %s WHERE request_id = %s', ('rejected', request_id))
            cursor.execute('select user_id from user_requests where request_id = %s',('rejected',))
            user_id=cursor.fetchone()
            cursor.execute('delete from user where user_id=%s',(user['user_id']))

        conn.commit()
        cursor.execute('select * from user_requests ur JOIN user u on ur.user_id=u.user_id')
        pending_users=cursor.fetchall()
        return jsonify({"success":True,"user":pending_users})
    cursor.execute('select * from user_requests ur JOIN user u on ur.user_id=u.user_id')
    pending_users=cursor.fetchall()
    return render_template('admin_enrollments.html',user=pending_users)

@app.route('/admin/approve_course', methods=['GET','POST'])
def approve_course():
    if session['role'] != 3:
        return "You are not authorized to perform this action!", 403
    if request.method == 'POST':
        course_id = request.json.get('course_id')
        action = request.json.get('action')  # 'approve' or 'reject'
        print(f"{course_id} {action}")
        if action == 'approve':
            cursor.execute('UPDATE course SET admin_approval_status = %s,course_status=%s WHERE course_id = %s', ('approved','running', course_id,))
        elif action == 'reject':
            cursor.execute('delete from course WHERE course_id = %s', (course_id,))
        conn.commit()
        cursor.execute('select * from course where admin_approval_status=%s',('pending',))
        pending_course=cursor.fetchall()
        return jsonify({"success": True,"courses":pending_course})
    else:
        cursor.execute('select c.*,u.username from course c join faculty f on f.faculty_id = c.faculty_id join user u on u.user_id=f.user_id where admin_approval_status=%s',('pending',))
        pending_course=cursor.fetchall()
        return render_template('admin_courses.html',courses=pending_course,user=user)

@app.route("/course/<course_id>/<username>")
def course(course_id,username):
    if session['role']==1:
        cursor.execute('select c.*,u.username,f.dep from course c join faculty f on f.faculty_id = c.faculty_id join user u on u.user_id=f.user_id where course_id = %s',(course_id,))
        course=cursor.fetchone()
        cursor.execute('select s.*,sc.status from student_course sc join student s on sc.student_id=s.student_id where sc.course_id = %s',(course_id,))
        students=cursor.fetchall()
        return render_template('course_details_student.html',course=course,students=students,username=username)
    elif session['role']==2:
        cursor.execute('select c.*,u.username,f.dep,f.faculty_id from course c join faculty f on f.faculty_id = c.faculty_id join user u on u.user_id=f.user_id where course_id = %s',(course_id,))
        course=cursor.fetchone()
        cursor.execute('select s.*,sc.status from student_course sc join student s on sc.student_id=s.student_id where sc.course_id = %s',(course_id,))
        students=cursor.fetchall()
        return render_template('course_details_faculty.html',course=course,students=students,username=username)
    else:
        return "You are not authorised to view this page!!"


@app.route('/logout')
def logout():

    '''This route handles user logout functionality'''
 
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role',None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
            
 
