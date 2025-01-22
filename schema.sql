DROP DATABASE IF EXISTS aims;
create database aims;
use aims;

CREATE TABLE student (
    student_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    student_name VARCHAR(100),
    email_id VARCHAR(100) unique,
    degree ENUM('BTECH','MTECH','PHD','MSC'),
    dep ENUM('COMPUTER SCIENCE AND ENGINEERING','ELECTRICAL ENGINEERING','MECHANICAL ENGINEERING','MATHS AND COMPUTING','CHEMICAL ENGINEERING','METALLURGY ENGINEERING'),
    entry_no varchar(11),
    year_of_entry int
);

CREATE TABLE otp_table(
    otp_id int auto_increment primary key not null,
    user_id varchar(100),
    otp varchar(6),
    created_at datetime
);

CREATE TABLE faculty(
    faculty_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    faculty_name VARCHAR(100),
    email_id VARCHAR(100)
);

CREATE TABLE course (
    course_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    course_name VARCHAR(100),
    faculty_id int,
    status enum('running','completed'),
    no_of_enrollments int,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
);

CREATE TABLE student_course (
    student_id int,
    course_id int ,
    status enum('audit','credit','drop'),
    FOREIGN KEY (student_id) REFERENCES student(student_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id)
);

CREATE TABLE faculty_advisor(
    faculty_id int primary key,
    year_of_entry int,
    degree ENUM('BTECH','MTECH','PHD','MSC'),
    dep ENUM('COMPUTER SCIENCE AND ENGINEERING','ELECTRICAL ENGINEERING','MECHANICAL ENGINEERING','MATHS AND COMPUTING','CHEMICAL ENGINEERING','METALLURGY ENGINEERING')
)

Insert into student(student_name,email_id,degree,dep) values('TARUSHI','2022csb1135@iitrpr.ac.in','BTECH','COMPUTER SCIENCE AND ENGINEERING');