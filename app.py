from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.orm import relationship
import sys

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
app.secret_key = 'super secret key'  
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

db = SQLAlchemy(app)

student_course = db.Table(
    'student_course',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id')),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id')),
    db.Column('grade', db.String)
)

class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    enrolled_courses = db.relationship('Course', secondary=student_course, backref='students')

class Teacher(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String, nullable=False)
    teacher_name = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    enrolled_students = db.Column(db.Integer, default=0)
    capacity = db.Column(db.Integer, nullable=False)
    #students_list = db.relationship('Student', secondary=student_course, backref='courses_enrolled')



admin = Admin(app, name='microblog', template_mode='bootstrap3')
admin.add_view(ModelView(Student, db.session))
admin.add_view(ModelView(Teacher, db.session))
admin.add_view(ModelView(Course, db.session))

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app)

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")

@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Student.query.filter_by(username=form.username.data).first()
        if not user:
            user = Teacher.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            if isinstance(user, Teacher):
                return redirect(url_for('teacher_dashboard'))
            elif isinstance(user, Student):
                return redirect(url_for('student_dashboard_add_courses'))
            #return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


@app.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    return "Welcome to the teacher dashboard, {}".format(current_user.username)

def not_courses(student_courses):
    #print(student_courses + '\n', file=sys.stderr)
    result = []

    for course in Course.query.all():
        is_student_course = False
        for student_course in student_courses:
            if course == student_course:
                is_student_course = True
        if not is_student_course:
            result.append(course)
    return result

@app.route('/student_dashboard_your_courses')
@login_required
def student_dashboard_your_courses():
    student_courses = current_user.enrolled_courses #should give you all courses student is enrolled in
    all_courses = Course.query.filter(Course.enrolled_students < Course.capacity).all()
    not_student_courses = not_courses(student_courses) #should give you all courses student isn't enrolled in
    return render_template('student.html', username=current_user.username, courses=student_courses, student_courses=student_courses, all_courses=all_courses, not_student_courses=not_student_courses)
#render_template('student.html', username=current_user.username, courses=student_courses)


@app.route('/student_dashboard_add_courses')
@login_required
def student_dashboard_add_courses():
    all_courses = Course.query.filter(Course.enrolled_students < Course.capacity).all()
    student_courses = current_user.enrolled_courses #should give you all courses student is enrolled in
    not_student_courses = not_courses(student_courses) #should give you all courses student isn't enrolled in
    return render_template('student_add.html', username=current_user.username, student_courses=student_courses, all_courses=all_courses, not_student_courses=not_student_courses)

@app.route('/reload_student_add_courses/<courseId>')
@login_required
def reload_student_add_courses(courseId):
    print("This is reaching a reload\n")
    course = Course.query.filter(Course.id == courseId).first()
    print("This has found a course by searching for course Id\nCourse Id: %d course name: %s", course.id, course.class_name)
    student = Student.query.filter(Student.id == current_user.id).first()
    adding = True
    print("Student enrolled courses: ", student.enrolled_courses)

    for enrolled in student.enrolled_courses:
        if course == enrolled:
            student.enrolled_courses.remove(course)
            adding = False

    if adding:
        student.enrolled_courses.append(course)

    db.session.commit()

    return redirect(url_for('student_dashboard_add_courses'))

@login_manager.user_loader
def load_user(user_id):
    # 在这个函数中根据 user_id 加载用户对象(In this function load the user object based on user_id)
    # 通常，你会在数据库中查找用户并返回用户对象(Typically, you would look up the user in the database and return the user object)
    student = Student.query.get(user_id)
    teacher = Teacher.query.get(user_id)
    if student:
        return student
    elif teacher:
        return teacher
    return None


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


#These codes are used to test whether students successfully registered for the course
@app.route('/view_enrolled_courses')
def view_enrolled_courses():
    # 获取所有学生
    all_students = Student.query.all()
    
    # 创建一个字典，用于存储学生的注册课程信息(Create a dictionary to store students' registered course information)
    student_course_info = {}
    
    # 遍历每个学生，获取他们的注册课程信息(Iterate through each student and get their registered course information)
    for student in all_students:
        enrolled_courses_info = []
        for course in student.enrolled_courses:
            enrolled_courses_info.append(f"User {student.username} is enrolled in course: {course.class_name}")
        student_course_info[student.username] = enrolled_courses_info
    
    return render_template('enrolled_courses.html', student_course_info=student_course_info)


if __name__ == '__main__':
    app.run(port=5001)
