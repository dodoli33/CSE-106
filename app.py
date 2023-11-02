from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
app.secret_key = 'super secret key'  
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 阻止 Flask-SQLAlchemy 的警告

db = SQLAlchemy(app)

student_course = db.Table(
    'student_course',
    db.Column('student_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id')),
    db.Column('grade', db.String)  # 添加成绩列
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    user_type = db.Column(db.String, nullable=False)  # 添加用户类型字段
    enrolled_courses = db.relationship('Course', secondary=student_course, backref='students')

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String, nullable=False)
    teacher_name = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    enrolled_students = db.Column(db.Integer, default=0)
    capacity = db.Column(db.Integer, nullable=False)
    students_list = db.relationship('User', secondary=student_course, backref='courses_enrolled')


# Set up an application context
with app.app_context():
    # Create database tables
    db.create_all()

#class CourseView(ModelView):
    #pass

admin = Admin(app, name='microblog', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
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
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            if user.user_type == "teacher":
                return redirect(url_for('teacher_dashboard'))
            elif user.user_type == "student":
                return redirect(url_for('student_dashboard'))
            return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    return "Welcome to the teacher dashboard, {}".format(current_user.username)

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    student_courses = Course.query.filter(Course.enrolled_students < Course.capacity).all()
    return render_template('student.html', username=current_user.username, courses=student_courses)


@login_manager.user_loader
def load_user(user_id):
    # 在这个函数中根据 user_id 加载用户对象
    # 通常，你会在数据库中查找用户并返回用户对象
    return User.query.get(int(user_id))  # 假设 User 是你的用户模型

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

with app.app_context():

    # 查询所有用户
    users = User.query.all()

    # 打印用户信息
    for user in users:
        print(f"User ID: {user.id}, Username: {user.username}")

    # 或者使用列表推导式打印用户信息
    [print(f"User ID: {user.id}, Username: {user.username}") for user in users]

@app.route('/view_enrolled_courses')
def view_enrolled_courses():
    user1 = User.query.get(1)  # 获取第一个用户（假设ID为1）
    enrolled_courses = user1.enrolled_courses  # 获取该用户关联的课程列表

    enrolled_courses_info = []
    for course in enrolled_courses:
        enrolled_courses_info.append(f"User {user1.username} is enrolled in course: {course.class_name}")

    return render_template('enrolled_courses.html', enrolled_courses=enrolled_courses_info)



if __name__ == '__main__':
    app.run(port=5001)
