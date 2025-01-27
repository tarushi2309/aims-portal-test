DROP DATABASE IF EXISTS aims;
create database aims;
use aims;

CREATE TABLE user(
    user_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    email_id varchar(100) unique,
    username varchar(100),
    role ENUM('student', 'faculty', 'admin') NOT NULL 
);
CREATE TABLE student (
    student_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    user_id int,
    degree ENUM('BTECH','MTECH','PHD','MSC'),
    dep ENUM('COMPUTER SCIENCE AND ENGINEERING','ELECTRICAL ENGINEERING','MECHANICAL ENGINEERING','MATHS AND COMPUTING','CHEMICAL ENGINEERING','METALLURGY ENGINEERING','CIVIL ENGINEERING'),
    entry_no varchar(11),
    year_of_entry int,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE otp_table(
    otp_id int auto_increment primary key not null,
    user_id varchar(100),
    otp varchar(6),
    created_at datetime
);

CREATE TABLE faculty(
    faculty_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    user_id int,
    dep ENUM('COMPUTER SCIENCE AND ENGINEERING','ELECTRICAL ENGINEERING','MECHANICAL ENGINEERING','MATHS AND COMPUTING','CHEMICAL ENGINEERING','METALLURGY ENGINEERING','CIVIL ENGINEERING'),
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE course (
    course_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    course_name VARCHAR(100),
    faculty_id int,
    course_status enum('running','completed','pending_admin_approval'),
    no_of_enrollments int default 0,
    LTPC varchar(8),
    credits int,
    sem varchar(10),
    course_code varchar(100),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
);

CREATE TABLE student_course (
    student_id int,
    course_id int ,
    status enum('audit','enrolled','dropped','pending instructor approval', 'pending advisor approval','completed'),
    grade varchar(2),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id)
);

CREATE TABLE faculty_advisor(
    faculty_id int primary key,
    year_of_entry int,
    degree ENUM('BTECH','MTECH','PHD','MSC'),
    dep ENUM('COMPUTER SCIENCE AND ENGINEERING','ELECTRICAL ENGINEERING','MECHANICAL ENGINEERING','MATHS AND COMPUTING','CHEMICAL ENGINEERING','METALLURGY ENGINEERING'),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
);

CREATE TABLE admin(
    admin_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    user_id int,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

INSERT into user(username,email_id,role) values('TARUSHI','2022csb1135@iitrpr.ac.in','student');
INSERT into user(username,email_id,role) values('Dr. Puneet Goyal','puneet@iitrpr.ac.in','faculty');
Insert into student(user_id,degree,dep,entry_no,year_of_entry) values(1,'BTECH','COMPUTER SCIENCE AND ENGINEERING','2022csb1135',2022);
INSERT into faculty(user_id,dep) values(2,'COMPUTER SCIENCE AND ENGINEERING');
INSERT into course(course_name,faculty_id,course_status,LTPC,credits,course_code,sem) values('Development Engineering Project',1,'running','3-5-5-3',3,'CP301','2024-II');
INSERT into student_course(student_id,course_id,status,grade) values(1,1,'enrolled','NA');
insert into user(username,email_id,role) values('tarushi','tarushi.tanejag1112@gmail.com','faculty');
insert into faculty(user_id,dep) values(3,'ELECTRICAL ENGINEERING');
