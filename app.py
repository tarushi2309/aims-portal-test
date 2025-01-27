from flask import Flask,render_template, request, redirect, url_for, session,send_file
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
    password="password",
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
            'delete from otp_table where user_id = %s and TIMESTAMPDIFF(MINUTE, created_at, NOW()) > 5', (receiver,) )
    conn.commit()
    cursor.execute('insert into otp_table (user_id,otp,created_at) values (%s,%s,%s)',(receiver,otp,datetime.now(),))
    conn.commit()
    text=f"Subject : OTP for AIMS Login\n\n Your login otp is {otp} \n\n This is valid for 5 minutes"
    server = smtplib.SMTP("smtp.gmail.com",587)
    server.starttls()

    server.login(sender,"eipn qsmt ffbv zqjm")               # dummy passcode. Sender should be your email id. passcode is app password. Explained in detail in readme file
    server.sendmail(sender,receiver,text)

@app.route('/')
def hello2():
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
                cursor.execute('select * from user where email_id = %s',(email_id,))
                global user
                user=cursor.fetchone()
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
                    msg="Incorrect Email Id !! Please re enter correct email id"
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
        cursor.execute('SELECT * FROM student_course sc JOIN course c on sc.course_id = c.course_id where sc.student_id = %s',(student['student_id'],))  
        courses = cursor.fetchall()
        return render_template("dashboard_student.html",user=user,student=student,courses=courses)
    else:
        return "You are not authorised to view this page!!"

@app.route('/dashboard_faculty/<username>')
def dashboard_faculty(username):
    if session['role']==2:
        cursor.execute('SELECT * FROM faculty where user_id = %s',(user['user_id'],))  
        faculty = cursor.fetchone()
        cursor.execute('SELECT * FROM course where faculty_id = %s',(faculty['faculty_id'],))  
        courses = cursor.fetchall()
        return render_template("faculty_dashboard.html",user=user,faculty=faculty,courses=courses)
    else:
        return "You are not authorised to view this page!!"

@app.route('/dashboard_admin/<username>')
def dashboard_admin(username):
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
            print(f"fACULTY ID : {faculty_id}")
            cursor.execute('INSERT INTO course(course_name,faculty_id,course_code,LTPC,sem,course_status,credits) VALUES (%s, %s, %s, %s, %s,%s,%s)', (course_name, faculty_id, code, ltpc, sem,'pending_admin_approval',ltpc[-1],))
            conn.commit()
            return render_template('coursefloat.html',faculty_id=faculty_id,msg='Course created successfully. Students shall be able to enroll after admin approval!!')
        return render_template('coursefloat.html',faculty_id=faculty_id,msg='')
    else:
        return "You are not authorised to view this page!!"

#@app.route('/pending_approvals/<')

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
            cursor.execute(
            'INSERT INTO student(student_name,entry_no,email_id,degree,department,year_of_entry) VALUES(%s,%s, %s,%s, %s,%s)', (name,entry_no,email_id,degree,department,year_of_entry,) )
            conn.commit()
            return render_template("login.html",msg="Signup Successful. You may login Now")
        elif user_type =="faculty":
            name = request.form['name']
            email_id = request.form['email']
            cursor.execute(
            'INSERT INTO faculty(faculty_name,email_id) VALUES(%s, %s)', (name,email_id,) )
            conn.commit()
            return render_template("login.html",msg="Signup Successful. You may login Now")


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

"""@app.route('/profile_mentee/<username>',methods=['GET','POST'])
def profile_mentee(username):

    '''This is responsible for displaying and updating the profile of a mentee. When accessed
    via GET, it retrieves the mentee's profile details from the database. If accessed via
    POST, it processes the updated profile details submitted by the mentee, updates the
    database accordingly, and renders the updated profile page.'''
 
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
            'SELECT * FROM mentee WHERE username = % s ', (username,) )
    mentee=cursor.fetchone()
    cursor.execute('SELECT * FROM tag')
    all_tags=cursor.fetchall()
    cursor.execute('SELECT * FROM mentee_tag WHERE mentee_id=%s',(mentee['mentee_id'],))
    mentee_tags=cursor.fetchall()
    is_checked={}
    for tag in mentee_tags:
        cursor.execute('SELECT * FROM tag WHERE tag_id = %s',(tag['tag_id'],))
        tag_val=cursor.fetchone()
        tag_name=tag_val['tag_name']
        is_checked[tag_name]=1

    if request.method=='POST':
        new_name=request.form['name']
        new_contact=request.form['contact_no']
        new_email=request.form['email_id']
        new_education=request.form['education']
        new_interest=request.form['interests']
        cursor.execute('DELETE FROM mentee_tag WHERE mentee_id = %s', (mentee['mentee_id'],))
        mysql.connection.commit()
        new_checked={}
        for tag in all_tags:
            tag_name=tag['tag_name']
            
            tag_id=tag['tag_id']
            if tag_name in request.form:
                new_checked[tag_name]=1
                cursor.execute('INSERT INTO mentee_tag(mentee_id,tag_id) VALUES (%s,%s)',(mentee['mentee_id'],tag_id))
                mysql.connection.commit()
    
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE mentee SET mentee_name = %s,contact_no=%s,email_id=%s,education=%s,interests=%s WHERE username = %s',(new_name,new_contact,new_email,new_education,new_interest,username))
    
        mysql.connection.commit()
        return render_template('profile_mentee.html',mentee=mentee,msg='Profile details updated successfully',tags=all_tags,is_checked=new_checked,isview=False)

    return render_template('profile_mentee.html',mentee=mentee,msg='',tags=all_tags,is_checked=is_checked,isview=False)

@app.route('/profile_mentor/<username>',methods=['GET','POST'])
def profile_mentor(username):

    '''This is responsible for displaying and updating the profile of a mentor. When accessed
    via GET, it retrieves the mentor's profile details from the database. If accessed via POST,
    it processes the updated profile details submitted by the mentor, updates the database
    accordingly, and renders the updated profile page.'''
 
    viewer='mentor'
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
            'SELECT * FROM mentor WHERE username = % s ', (username,) )
    mentor=cursor.fetchone()
    if request.method=='POST':
        new_name=request.form['name']
        new_contact=request.form['contact_no']
        new_email=request.form['email_id']
        new_institute=request.form['education']
        new_degree=request.form['degree']
        new_major=request.form['major']
        new_workexp=request.form['work_exp']
        new_interest=request.form['interests']
        new_file=request.files['file']
        if new_file:
            # file_path = os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], username),mentor['file_name'])
            # if os.path.exists(file_path):
            #         os.unlink(file_path)
            filename = secure_filename(new_file.filename)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], username), exist_ok=True)
            new_file.save(os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], username), filename))
            cursor.execute('UPDATE mentor SET mentor_name = %s,contact_no=%s,email_id=%s,institute=%s,degree=%s,major=%s,work_exp=%s,interests=%s,file_name = %s WHERE username = %s',(new_name,new_contact,new_email,new_institute,new_degree,new_major,new_workexp,new_interest,filename,username))
            mysql.connection.commit()
            cursor.execute('SELECT * FROM mentor WHERE mentor_id=%s',(mentor['mentor_id'],))
            mentor_new=cursor.fetchone()
            return render_template('profile_mentor.html',mentor=mentor_new,msg='Profile details updated successfully',view_profile=False,give_approval=False,viewer=viewer)
        elif not new_file:
            cursor.execute('UPDATE mentor SET mentor_name = %s,contact_no=%s,email_id=%s,institute=%s,degree=%s,major=%s,work_exp=%s,interests=%s WHERE username = %s',(new_name,new_contact,new_email,new_institute,new_degree,new_major,new_workexp,new_interest,username,))
            mysql.connection.commit()
            cursor.execute('SELECT * FROM mentor WHERE mentor_id=%s',(mentor['mentor_id'],))
            mentor_new=cursor.fetchone()
            return render_template('profile_mentor.html',mentor=mentor_new,msg='Profile details updated successfully',view_profile=False,give_approval=False,viewer=viewer)


    return render_template('profile_mentor.html',mentor=mentor,msg='',view_profile=False,give_approval=False,viewer=viewer)

@app.route('/view_file/<username>/<filename>')
def view_file(username, filename):

    ''' This helps in viewing the resumes of the mentors by the admin and mentees'''
 
    file_path=os.path.join(os.path.join(app.config['UPLOAD_FOLDER'], username), filename)
    return send_file(file_path, as_attachment=True)

@app.route('/view_mentees')
def view_mentees():

    '''This is responsible for retrieving and displaying mentees enrolled in a specific course.'''
 
    course_id = int(request.args.get('course_id'))
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM course WHERE course_id = %s',(course_id,))
    course_mentor=cursor.fetchone()
    cursor.execute('SELECT * FROM mentor WHERE mentor_id=%s',(course_mentor['mentor_id'],))
    mentor=cursor.fetchone()
    cursor.execute('SELECT * FROM course_mentee WHERE course_id = %s',(course_id,))
    course_mentees=cursor.fetchall()
    mentees=[]
    for each_mentee in course_mentees:
        cursor.execute('SELECT * FROM mentee WHERE mentee_id=%s',(each_mentee['mentee_id'],))
        mentee=cursor.fetchone()
        mentees.append(mentee)
    
    cursor.execute('SELECT * FROM course WHERE course_id=%s',(course_id,))
    course=cursor.fetchone()
    return render_template('view_mentees.html',mentees=mentees,course=course,mentor=mentor)


@app.route('/view_mentor_profile',methods=['GET','POST'])
def view_mentor_profile():

    '''This is responsible for viewing and managing the profile of a mentor. It retrieves the
    mentor's profile details and renders a web page displaying the profile. It allows the
    administrator to approve or reject the mentor's profile.'''
 
    viewer = request.args.get('viewer')
    username=request.args.get('username')
    mentee_id=int(request.args.get('mentee_id'))
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if viewer=='mentee':
        if mentee_id>0:
            cursor.execute(
            'SELECT * FROM mentee WHERE mentee_id = % s ', (mentee_id,) )
            mentee=cursor.fetchone()
            return render_template('profile_mentor.html',mentor=mentor,msg='',view_profile=True,give_approval=False,viewer=viewer,mentee=mentee)

   
    
    cursor.execute(
            'SELECT * FROM mentor WHERE username = % s ', (username,) )
    mentor=cursor.fetchone()

    if mentor['mentor_status']=='verified':
        return render_template('profile_mentor.html',mentor=mentor,msg='',view_profile=True,give_approval=False,viewer=viewer)
    
    if request.method=='POST':
        if 'accept' in request.form:
            cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE mentor SET mentor_status = %s WHERE username = %s' ,('verified',username) )
            mysql.connection.commit()
            send_email(mentify_email,mentor['email_id'],"Approval for Mentorship","Greetings from Mentify! Your profile has been verified by Mentify. Now you can log into our website and create courses, hold mentorship sessions and much more! Welcome onboard!")
        elif 'reject' in request.form:
            cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE mentor SET mentor_status = %s WHERE username = %s' ,('rejected',username) )
            mysql.connection.commit()
            send_email(mentify_email,mentor['email_id'],"Application status for Mentorship","Greetings from Mentify! Your profile has been inspected by Mentify. We regret to inform you that we could not ascertain your application. Please log into our website to update your profile details so that we may inspect it again. ")
        return redirect(url_for('admin'))
    
    return render_template('profile_mentor.html',mentor=mentor,msg='',view_profile=True,give_approval=True,viewer=viewer)
    
@app.route('/create_program/<username>',methods=['GET','POST'])
def create_program(username):

    '''This allows a mentor to create a new program/course. It renders a form for the mentor to
    input program details and then processes the submitted form data to create a new
    program/course.'''
 
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM tag')
    tags=cursor.fetchall()
    cursor.execute('SELECT * FROM mentor WHERE username=%s',(username,))
    mentor=cursor.fetchone()
    
    if request.method=='POST':
        course_name=request.form['course_name']
        start_date=request.form['start_date']
        end_date=request.form['end_date']
        price=request.form['price']
        mentor_id=mentor['mentor_id']
        course_desc=request.form['desc']
        max_mentee=request.form['max_mentee']
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO course(mentor_id, course_name, course_start, course_end, course_price,course_desc,max_limit) VALUES (%s, %s, %s, %s, %s,%s,%s)', (mentor_id, course_name, start_date, end_date, price,course_desc,max_mentee))
        mysql.connection.commit()
        cursor.execute('SELECT * FROM course WHERE course_name = %s',(course_name,))
        course=cursor.fetchone()
        course_id=course['course_id']
        for tag in tags:
            tag_name=tag['tag_name']
            tag_id=tag['tag_id']
            if tag_name in request.form:
                cursor.execute('INSERT INTO course_tag_relation(course_id,tag_id) VALUES(%s,%s)',(course_id,tag_id))
        mysql.connection.commit()
        return render_template('create_program_mentor.html',mentor=mentor,tags=tags,msg='Course proposal successfully submitted. On approval by Mentify, you will receive an email confirming acceptance of your proposal and mentees will be able to join your program ')
    return render_template('create_program_mentor.html',mentor=mentor,tags=tags,msg='')


        
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():

    '''This allows users to reset their passwords if they have forgotten them. It renders a form
    for users to input their username and email. It handles the password reset process,
    including sending an OTP to the user's email and updating the password if the OTP is
    correct.'''
 
    global otp_gen
    global email_fp
    global usertype_fp
    if request.method == 'POST':
        if 'username' in request.form and 'email' in request.form:
            username = request.form['username']
            email_fp = request.form['email']
            cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
            'SELECT * FROM mentee WHERE username = % s ', (username,) )
            user=cursor.fetchone()
            if user:
                usertype_fp='mentee'
                if(email_fp==user['email_id']):
                    otp = str(random.randint(100000, 999999))
                    otp_gen=otp
                    send_email(mentify_email,email_fp,"OTP For Changing Password",f"Hi {user['mentee_name']}!\nOTP for changing password is {otp}. Do not share the OTP with anyone.\nIf you did not apply for changing password kindly report it on Mentify website.")
                    return render_template('forgot_password.html', username=username, show_otp_form=True,msg='')
                else:
                    return render_template('forgot_password.html', username=username, show_otp_form=False,msg='Incorrect Email Id entered')
            else:
                cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute(
                    'SELECT * FROM mentor WHERE username = % s ', (username,) )
                user=cursor.fetchone()
                if user:
                    usertype_fp='mentor'
                    if(email_fp==user['email_id']):
                        otp = str(random.randint(100000, 999999))
                        otp_gen=otp
                        send_email(mentify_email,email_fp,"OTP For Changing Password",f"Hi {user['mentor_name']}!\nOTP for changing password is {otp}. Do not share the OTP with anyone.\nIf you did not apply for changing password kindly report it on Mentify website.")
                        return render_template('forgot_password.html', username=username, show_otp_form=True,msg='')
                    else:
                        return render_template('forgot_password.html', username=username, show_otp_form=False,msg='Incorrect Email Id entered')                   
                else:
                    return render_template('forgot_password.html', username=username, show_otp_form=False,msg='Incorrect username entered')

        elif 'otp' in request.form and 'new_password' in request.form:
            username = request.form['username']
            otp_entered = request.form['otp']
            new_password = request.form['new_password']
            if(otp_entered==otp_gen):
                send_email(mentify_email,email_fp,"Password Changed","Greetings from Mentify! Password of your mentify account has been successfully changed! If you did not initiate the password change, kindly contact mentify support team.")
                cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                if(usertype_fp=='mentee'):
                    cursor.execute('UPDATE mentee SET pass_word = %s WHERE username = %s AND email_id = %s',(new_password,username,email_fp))
                elif(usertype_fp=='mentor'):
                    cursor.execute('UPDATE mentor SET pass_word = %s WHERE username = %s AND email_id = %s',(new_password,username,email_fp))
                mysql.connection.commit()
                return render_template('login.html',msg="Password change successful!")
            else:
                return render_template('forgot_password.html', username=username, show_otp_form=False,msg='Incorrect OTP entered')
            

    # Render the default form for entering username and email
    return render_template('forgot_password.html', show_otp_form=False,msg='')

@app.route('/admin',methods=['GET','POST'])
def admin():
 
    '''This serves as the dashboard for the administrator, providing access to various
    functionalities for managing the platform. It retrieves information about unapproved
    mentors, unapproved courses, and pending complaints and handles actions taken by the
    administrator, such as approving mentors or courses and resolving complaints.'''
 
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM mentor WHERE mentor_status = %s', ('unverified',))
    unapproved_mentors=cursor.fetchall()
    cursor.execute('SELECT course.* FROM course JOIN mentor ON course.mentor_id = mentor.mentor_id WHERE course.course_status = %s AND mentor.mentor_status = %s',('unverified','verified'))
    unapproved_courses=cursor.fetchall()
    cursor.execute("SELECT * FROM mentee_complaints WHERE complaint_status='pending'")
    mentee_pending_complaints = cursor.fetchall()
    cursor.execute("SELECT * FROM mentor_complaints WHERE complaint_status='pending'")
    mentor_pending_complaints = cursor.fetchall()
    return render_template("admin.html",mentors=unapproved_mentors,courses=unapproved_courses,mentee_complaints=mentee_pending_complaints,mentor_complaints=mentor_pending_complaints)

@app.route('/add_tag',methods=['GET','POST'])
def add_tag():       

    '''This allows administrator to add new tags to the system'''
 
    if request.method=='POST':
        new_tag=request.form['tag']
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM tag WHERE tag_name=%s',(new_tag,))
        existing_tag=cursor.fetchone()
        if not existing_tag:
            cursor.execute('INSERT INTO tag(tag_name) VALUES (%s)', (new_tag,))
            mysql.connection.commit()
        return redirect(url_for('admin'))

@app.route('/view_course',methods=['GET','POST'])
def view_course():

    '''This is used to view details about a specific course. Administrators can view course
    details, mentees enrolled in the course, and approve or reject course proposals.
    Mentees and mentors can also view course details.'''
    
    viewer = request.args.get('viewer')
    course_id = int(request.args.get('course_id'))
    mentee_id=int(request.args.get('mentee_id'))
    is_approval=request.args.get('isapproval')
    mentee=[]

    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM course_mentee WHERE course_id=%s',(course_id,))
    course_mentee=cursor.fetchall()
    cursor.execute('SELECT * FROM course WHERE course_id = %s', (course_id,))
    course=cursor.fetchone()
    cursor.execute('SELECT * FROM mentor WHERE mentor_id = %s', (course['mentor_id'],))
    mentor=cursor.fetchone()
    cursor.execute('SELECT * FROM course_tag_relation WHERE course_id=%s',(course['course_id'],))
    tag_rel=cursor.fetchall()
    tags=[]
    for tag in tag_rel:
        cursor.execute('SELECT * FROM tag WHERE tag_id=%s',(tag['tag_id'],))
        tag_new=cursor.fetchone()
        tags.append(tag_new)
    if viewer=='admin':
        return render_template('view_course.html',course=course,viewer=viewer,mentor=mentor,tags=tags,mentee_id=0,course_mentee=course_mentee,is_approval=is_approval,mentee=mentee)
    elif viewer=='mentee':
        if not mentee_id==0:
            cursor.execute('SELECT * FROM mentee WHERE mentee_id=%s',(mentee_id,))
            mentee=cursor.fetchone()
            return render_template('view_course.html',course=course,viewer=viewer,mentor=mentor,tags=tags,mentee_id=mentee_id,course_mentee=course_mentee,is_approval=is_approval,mentee=mentee)
    elif viewer=='mentor':
        return render_template('view_course.html',course=course,viewer=viewer,mentor=mentor,tags=tags,mentee_id=0,course_mentee=course_mentee,is_approval=is_approval,mentee=mentee)

    return render_template('view_course.html',course=course,viewer=viewer,mentor=mentor,tags=tags,mentee_id=0,course_mentee=course_mentee,is_approval=is_approval,mentee=mentee)


@app.route('/process_viewer_request',methods=['GET','POST'])
def process_viewer_request():
    course_id=int(request.args.get('course_id'))
    mentee_id=int(request.args.get('mentee_id'))
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method=='POST':
        if 'admin_comment' in request.form:
            admin_comment=request.form['admin_comment']
            if 'accept' in request.form:
                cursor.execute('UPDATE course SET admin_comment= %s,course_status=%s WHERE course_id=%s',(admin_comment,'verified',course_id))
                mysql.connection.commit()
            elif 'reject' in request.form:
                cursor.execute('UPDATE course SET admin_comment=%s,course_status=%s WHERE course_id=%s',(admin_comment,'rejected',course_id))
                mysql.connection.commit()
            return redirect(url_for('admin'))
        elif 'register' in request.form:
            amount=request.form['price']
            return redirect(('/payment'+ f'?amount={amount}&course_id={course_id}&mentee_id={mentee_id}'))

@app.route('/payment',methods=['GET','POST'])
def payment():

    '''This facilitates the payment process for a course. Upon successful payment, it registers
    the mentee for the course and sends confirmation emails to both the mentee and the
    mentor.'''
    
    amount = request.args.get('amount')
    mentee_id = int(request.args.get('mentee_id'))
    course_id=int(request.args.get('course_id'))
    if request.method=='POST':
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO course_mentee(mentee_id,course_id) VALUES(%s,%s)',(mentee_id,course_id))
        mysql.connection.commit()
        cursor.execute('SELECT * FROM mentee WHERE mentee_id=%s',(mentee_id,))
        mentee=cursor.fetchone()
        cursor.execute('SELECT * FROM course WHERE course_id=%s',(course_id,))
        course=cursor.fetchone()
        cursor.execute('SELECT * FROM mentor WHERE mentor_id=%s',(course['mentor_id'],))
        mentor=cursor.fetchone()
        send_email(mentify_email,mentee['email_id'],"Course registration successful",f"Dear {mentee['mentee_name']}, you have successfully registered for the course {course['course_name']} conducted by mentor {mentor['mentor_name']}.\n Login to your Mentify account to check out course details!")
        send_email(mentify_email,mentor['email_id'],"Course registration",f"Dear {mentor['mentor_name']}, Mentee {mentee['mentee_name']} has enrolled for your course {course['course_name']}. You may now mentor your mentee and help him/her achieve their goals!!Login to your mentify account!!")
        return redirect(url_for('dashboard_mentee',username=mentee['username']))

    return render_template('payment.html',amount=amount)       

@app.route('/my_courses/<username>',methods=['GET','POST'])
def my_courses(username):

    '''This route retrieves and displays the courses enrolled by a mentee'''
 
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM mentee WHERE username=%s',(username,))
    mentee=cursor.fetchone()
    cursor.execute('SELECT * FROM course_mentee WHERE mentee_id=%s',(mentee['mentee_id'],)) #select the courses of a particular mentee from the course_mentee table in the schema
    course_list=cursor.fetchall() #fetch all such courses
    courses=[]
    for course in course_list:
        cursor.execute('SELECT * FROM course WHERE course_id=%s',(course['course_id'],))
        course_details=cursor.fetchone()
        courses.append(course_details)
    return render_template('my_courses_mentee.html',username=username,courses=courses)


@app.route('/search_sort_filter', methods=['POST'])
def search_sort_filter():
    username = request.args.get('username')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM mentee WHERE username=%s',(username,))
    mentee=cursor.fetchone()
    cursor.execute('SELECT * FROM tag')
    tag = cursor.fetchall()
    parameters = []
    sort_option = "(SELECT COUNT(*) FROM course_mentee WHERE course_mentee.course_id = course.course_id) DESC"
    query = "SELECT course.*, mentor.mentor_name FROM course JOIN mentor ON course.mentor_id = mentor.mentor_id"
    sort_choice = request.form['sort']

    if 'sort' in request.form:
        if sort_choice == 'valuation':
            sort_option = "(SELECT COUNT(*) FROM course_mentee WHERE course_mentee.course_id = course.course_id) DESC"
        elif sort_choice == 'equity':
            sort_option = "course_price ASC"
        elif sort_choice == 'investment':
            sort_option = "course_price DESC"

    selected_tag = request.form['filter']
    if 'filter' in request.form:
        if selected_tag != 'none':
            query += " JOIN course_tag_relation ON course.course_id = course_tag_relation.course_id"
            query += " JOIN tag ON course_tag_relation.tag_id = tag.tag_id"
            query += " WHERE tag.tag_name = %s AND course.course_status='verified'"
            parameters.append(selected_tag)
        else:
            query += " WHERE 1=1 AND course.course_status='verified'"

    else:
        query += " WHERE 1=1 AND course.course_status='verified'"  # Ensuring the WHERE clause is present even if no tag is selected

    search_term = request.form.get('search_term')
    search_type = request.form.get('search_type')

    if search_term:

        if search_type == 'mentor':
            query += " AND mentor.mentor_name LIKE %s"
        elif search_type == 'course':
            query += " AND course.course_name LIKE %s"
        parameters.append("%" + search_term + "%")

    query += f" ORDER BY {sort_option}"


    cursor.execute(query, parameters)

    
    print(selected_tag)
    cursor.execute(query, parameters)
    data = cursor.fetchall()
    # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    #     return jsonify(data=data,tag=tag)  # Return JSON response for AJAX request
    # else:
    return render_template('dashboard_mentee.html',mentee=mentee, data=data, tags=tag, selected_filter=selected_tag, sort_option=sort_choice, search_term=search_term, search_type=search_type)

@app.route('/complaint_against_mentor', methods=['GET','POST'])
def complaint_against_mentor():

    '''This route allows mentees to submit complaints.'''
 
    mentee_id = int(request.args.get('mentee_id'))
    course_id = int(request.args.get('course_id'))
    if request.method=='POST':
        complaint_date = datetime.now()
        complaint_desc = request.form['complaint_desc']    
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM course WHERE course_id=%s',(course_id,))
        course=cursor.fetchone()
        cursor.execute('SELECT * FROM mentee WHERE mentee_id=%s',(mentee_id,))
        mentee=cursor.fetchone()
        cursor.execute("INSERT INTO mentee_complaints (course_id,mentee_id, complaint_date, complaint_desc) VALUES (%s,%s, %s, %s)", (course['course_id'],mentee['mentee_id'], complaint_date, complaint_desc))
        mysql.connection.commit()
        send_email(mentify_email,mentee['email_id'],"Complaint registered successfully",f"Dear {mentee['mentee_name']},your complaint has been registered successfully.\nYou may check the status of the complaint on our website.")
        return render_template('raise_ticket.html',msg='Complaint successfully submitted')
        
    return render_template('raise_ticket.html',msg='')

@app.route('/complaint_against_mentee', methods=['GET','POST'])
def complaint_against_mentee():

    '''This route allows mentors to submit complaints.'''
 
    mentee_id = int(request.args.get('mentee_id'))
    course_id = int(request.args.get('course_id'))
    if request.method=='POST':
        complaint_date = datetime.now()
        complaint_desc = request.form['complaint_desc']    
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM course WHERE course_id=%s',(course_id,))
        course=cursor.fetchone()
        cursor.execute('SELECT * FROM mentor WHERE mentor_id=%s',(course['mentor_id'],))
        mentor=cursor.fetchone()
        cursor.execute('SELECT * FROM mentee WHERE mentee_id=%s',(mentee_id,))
        mentee=cursor.fetchone()
        cursor.execute("INSERT INTO mentor_complaints (course_id,mentee_id, complaint_date, complaint_desc) VALUES (%s, %s, %s,%s)", (course_id,mentee['mentee_id'], complaint_date, complaint_desc))
        mysql.connection.commit()
       
        send_email(mentify_email,mentor['email_id'],"Complaint registered successfully",f"Dear {mentor['mentor_name']},your complaint has been registered successfully.\nYou may check the status of the complaint on our website.")
        return render_template('raise_ticket.html',msg='Complaint successfully submitted')
        
    return render_template('raise_ticket.html',msg='')

@app.route('/messages')
def messages():

    '''This method displays all previous messages of a particular course.All important
    announcements made are displayed from the database.'''
 
    course_id = int(request.args.get('course_id'))
    username = (request.args.get('username'))
    viewer = (request.args.get('viewer'))    
    cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
            'SELECT * FROM mentee where username = %s',(username,))
    mentee=cursor.fetchone()
    cursor.execute(
            'SELECT * FROM course where course_id = %s',(course_id,))
    course=cursor.fetchone()
    cursor.execute('SELECT * FROM mentor WHERE mentor_id=%s',(course['mentor_id'],))
    mentor=cursor.fetchone()
    cursor.execute(
            'SELECT * FROM messages where course_id = %s',(course_id,)) #select all previous messages of the particular course
    messages = cursor.fetchall()
    # if viewer=='mentee':
    #     cursor.execute(
    #         'SELECT * FROM mentee where username = %s',(username,))
    #     mentee=cursor.fetchone()
    #     return render_template('my_courses_page_mentee.html',course=course,username=username,messages=messages,mentee=mentee,mentor=mentor)
    # elif viewer=='mentor':
    #     cursor.execute(
    #         'SELECT * FROM mentor where username = %s',(username,))
    #     mentor=cursor.fetchone()
    #     mentee=[]
    #     return render_template('my_courses_page_mentee.html',course=course,username=username,messages=messages,mentee=mentee,mentor=mentor)

    
    return render_template('my_courses_page_mentee.html',course=course,username=username,messages=messages,mentee=mentee,mentor=mentor,viewer=viewer)
 
@socketio.on('new_message') # socketio to handle real time chat
def handle_new_message(data):
 
    '''This method receives the new message input by the user and add it to the database.It
    also uses socketio to handle real time chatting . The new message is emitted.'''
 
    sender = data['sender']
    content = data['content']
    course_id = int(data['course_id'])

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("INSERT INTO messages(sender, content, course_id) VALUES (%s, %s, %s)",
                   (sender, content, course_id)) #insert into database (messages table)
    mysql.connection.commit()
    emit('new_message', {'sender': sender, 'content': content})

@app.route('/view_mentee_complaint',methods=['GET','POST'])
def view_mentee_complaint():

    '''This function views the mentor's complaint to the admin.'''
 
    complaint_id = int(request.args.get('complaint_id'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
            'SELECT * FROM mentee_complaints where complaint_id = %s',(complaint_id,))
    complaint=cursor.fetchone()
    cursor.execute(
            'SELECT * FROM mentee where mentee_id = %s',(complaint['mentee_id'],))
    mentee=cursor.fetchone()
    if request.method=='POST':
        complaint_action=request.form['complaint_action']
        cursor.execute("UPDATE mentee_complaints SET complaint_action = %s,complaint_status=%s WHERE complaint_id=%s", (complaint_action,'resolved',complaint_id))
        mysql.connection.commit()
       
        send_email(mentify_email,mentee['email_id'],"Complaint resolved successfully",f"Dear {mentee['mentee_name']},your complaint has been resolved. Action taken : {complaint_action}\nLogin to our website to continue learning!!.")
        return redirect(url_for('admin'))
        
    return render_template('resolve_ticket.html',complaint=complaint,msg='')

@app.route('/view_mentor_complaint',methods=['GET','POST'])
def view_mentor_complaint():

    ''' This function views the mentor's complaint to the admin.'''
 
    complaint_id = int(request.args.get('complaint_id'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
            'SELECT * FROM mentee_complaints where complaint_id = %s',(complaint_id,))
    complaint=cursor.fetchone()
    cursor.execute(
            'SELECT * FROM course where course_id = %s',(complaint['course_id'],))
    course=cursor.fetchone()
    cursor.execute(
            'SELECT * FROM mentor where mentor_id = %s',(course['mentor_id'],))
    mentor=cursor.fetchone()
    # cursor.execute(
    #         'SELECT * FROM mentee where mentee_id = %s',(complaint['mentee_id'],))
    # mentee=cursor.fetchone()
    if request.method=='POST':
        complaint_action=request.form['complaint_action']
        cursor.execute("UPDATE mentor_complaints SET complaint_action = %s,complaint_status=%s WHERE complaint_id=%s", (complaint_action,'resolved',complaint_id))
        mysql.connection.commit()
       
        send_email(mentify_email,mentor['email_id'],"Complaint resolved successfully",f"Dear {mentor['mentor_name']},your complaint has been resolved. Action taken : {complaint_action}\nLogin to our website to continue learning!!.")
        return redirect(url_for('admin'))
        
    return render_template('resolve_ticket.html',complaint=complaint,msg='')






@app.route('/submit_feedback', methods=['GET', 'POST'])
def submit_feedback():

    '''This function handles the submission of feedback for a course by a user. It expects a 'username' parameter to be provided via the request arguments.
        If the HTTP method is POST, it retrieves course ID, rating, and feedback commentsfrom the form data, inserts them into the 'feedback' table in the database,
        and redirects the user to their mentee dashboard.'''
 
    username=request.args.get('username')
    if request.method == 'POST':
        course_id = request.form['course_id']
        rating = int(request.form['rating'])
        feedback_comments = request.form['feedback_comments']
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO feedback (course_id, rating, feedback_comments) VALUES (%s, %s, %s)",(course_id, rating, feedback_comments))
        mysql.connection.commit()
        return redirect(url_for('dashboard_mentee',username=username))

    return render_template('feedback_form.html',username=username)


@app.route('/logout')
def logout():

    '''This route handles user logout functionality'''
 
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('hello'))"""

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
            
 
