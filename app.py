from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Implement user authentication logic here
        # You can query a database or use other authentication methods
        # Assuming a successful authentication, you can determine the user's identity

        if username == 'admin' and password == '111':
            # Admin login
            return redirect('/admin')
        elif username == 'teacher' and password == '111':
            # Teacher login
            return redirect('/teacher')
        elif username == 'student' and password == '111':
            # Student login, render student.html
            return render_template('student.html')
        else:
            # Authentication failed
            return "Authentication failed"

    return render_template('login.html')

# Pages for different user types
@app.route('/admin')
def admin_dashboard():
    return "Welcome, Admin!"

@app.route('/teacher')
def teacher_dashboard():
    return "Welcome, Teacher!"

if __name__ == '__main__':
    app.run(port=5001, debug=True)
