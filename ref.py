
from flask import Flask, render_template, flash, redirect, request, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from faker import Faker
import pyotp
import uuid

app = Flask(__name__,static_folder='assets')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://dadi:root@localhost/ngo_management'
app.secret_key = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

def generate_uuid():
    return str(uuid.uuid4())

from sqlalchemy import DateTime

from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'in-v3.mailjet.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = '079e64bfb75a32c5aa73dcb1728db675'
app.config['MAIL_PASSWORD'] = '9fbc462b9c77d0bbe6d5fafc113c62de'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

from sqlalchemy import func

class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    phone_no = db.Column(db.String(15), nullable=True)
    email_id = db.Column(db.String(255), nullable=True)
    help_type = db.Column(db.String(255), nullable=False)  # Store as comma-separated values
    donation_amount = db.Column(db.Float, nullable=True)
    donation_date = db.Column(DateTime, nullable=False, default=func.now())

class PendingStudent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(64), unique=True, default=generate_uuid)
    name = db.Column(db.String(64), index=True)
    age = db.Column(db.Integer)
    class_ = db.Column(db.String(64))  # Change this line
    school = db.Column(db.String(128))
    parental_income = db.Column(db.Float)
    help_type = db.Column(db.String(128))

    def __init__(self, name, age, class_, school, parental_income, help_type):  # Change this line
        self.name = name
        self.age = age
        self.class_ = class_  # Change this line
        self.school = school
        self.parental_income = parental_income
        self.help_type = help_type


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(64), unique=True, default=generate_uuid)
    name = db.Column(db.String(64), index=True)
    age = db.Column(db.Integer)
    class_ = db.Column(db.String(64))
    school = db.Column(db.String(128))
    parental_income = db.Column(db.Float)
    help_type = db.Column(db.String(128))
   

    def __repr__(self):
        return '<Student {}>'.format(self.name)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'class': self.class_,
            'school': self.school,
            'parental_income': self.parental_income,
            'help_type': self.help_type
        }

fake = Faker()

@app.route('/home', methods=['GET'])
def admin_home():
    return render_template('home.html')

from datetime import datetime, timezone
now = datetime.now(timezone.utc)
from datetime import datetime, timedelta, timezone

from flask import Flask, render_template, request, redirect, url_for

from flask_login import UserMixin, current_user, login_required, login_user
from werkzeug.security import generate_password_hash, check_password_hash

class Volunteer(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15))
    availability = db.Column(db.String(50))
    subscribe_newsletter = db.Column(db.Boolean, default=False)
    active_volunteer = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Routes for signup, login, and volunteer dashboard

@app.route('/signup_volunteer', methods=['GET', 'POST'])
def signup_volunteer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone')
        availability = request.form.get('availability')
        subscribe_newsletter = 'subscribe_newsletter' in request.form
        active_volunteer = 'active_volunteer' in request.form

        existing_volunteer = Volunteer.query.filter_by(email=email).first()
        if existing_volunteer:
            flash('Email already exists. Please use a different email.')
            return redirect(url_for('signup_volunteer'))

        new_volunteer = Volunteer(
            name=name, 
            email=email, 
            phone=phone, 
            availability=availability, 
            subscribe_newsletter=subscribe_newsletter, 
            active_volunteer=active_volunteer
        )
        new_volunteer.set_password(password)

        db.session.add(new_volunteer)
        db.session.commit()

        flash('Signup successful')
        return redirect(url_for('login_volunteer'))
    return render_template('signup_volunteer.html')

from flask import jsonify

@app.route('/login_volunteer', methods=['GET', 'POST'])
def login_volunteer():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if either field is empty
        if not email or not password or email == "":
            return jsonify(error='Please enter valid login credentials!')

        volunteer = Volunteer.query.filter_by(email=email).first()

        if volunteer and volunteer.check_password(password):
            login_user(volunteer)
            return jsonify(success=True)
        else:
            return jsonify(error='Invalid email or password')

    return render_template('login_volunteer.html')

from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # Return the user from the database
    return Volunteer.query.get(int(user_id))

@app.route('/volunteer')
@login_required
def volunteer():
    # Access current volunteer using 'current_user' provided by Flask-Login
    return render_template('volunteer.html')

@app.route('/update_profile_volunteer', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        current_user.name = request.form['name']
        current_user.email = request.form['email']
        current_user.phone = request.form.get('phone')
        current_user.availability = request.form.get('availability')
        current_user.subscribe_newsletter = 'subscribe_newsletter' in request.form
        current_user.active_volunteer = 'active_volunteer' in request.form

        db.session.commit()

        flash('Profile updated successfully')
        return redirect(url_for('volunteer'))
    return render_template('update_profile_volunteer.html')

from flask import request

@app.route('/volunteer_list')
def volunteer_list():
    # Fetch all volunteers from the database
    volunteers = Volunteer.query.all()

    # Get filter parameters from the request
    subscribe_newsletter = request.args.get('subscribe_newsletter')
    active_volunteer = request.args.get('active_volunteer')

    # Apply filters if parameters are provided
    if subscribe_newsletter:
        volunteers = [volunteer for volunteer in volunteers if volunteer.subscribe_newsletter == (subscribe_newsletter == 'Yes')]
    if active_volunteer:
        volunteers = [volunteer for volunteer in volunteers if volunteer.active_volunteer == (active_volunteer == 'Yes')]

    return render_template('volunteer_list.html', volunteers=volunteers)


@app.route('/contact_us', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        user_email = request.form.get('email')
        subject = request.form.get('subject')
        body = request.form.get('body')

        msg = Message(subject, sender='sesidadi.nssc@gmail.com', recipients=['sesidadi.nssc@gmail.com'])
        msg.body = f"Message from {user_email}:\n\n{body}"
        mail.send(msg)

        return jsonify({'message': 'Email sent successfully'}), 200
    else:
        return render_template('contact_us.html')
    
@app.route('/donate', methods=['GET', 'POST'])
def submit_donation():
    if request.method == 'POST':
        name = request.form.get('name')
        phone_no = request.form.get('phone_no')
        email_id = request.form.get('email_id')
        help_type = request.form.getlist('help_type')  # Get list of selected checkboxes
        donation_amount = request.form.get('donation_amount')
        
        # Check if all required fields are filled in
        if not name or not phone_no or not email_id or not help_type:
            return render_template('donate.html', error="All fields are required.")

        # Convert help_type list to comma-separated string
        help_type = ', '.join(help_type)

        if not donation_amount or donation_amount.strip() == '':
            donation_amount = None
        else:
            donation_amount = float(donation_amount)
        
        donation_date = datetime.now(timezone.utc)

        donor = Donor(name=name, phone_no=phone_no, email_id=email_id, help_type=help_type, donation_amount=donation_amount)
        db.session.add(donor)
        db.session.commit()

        donate_now = request.form.get('donate_now')  # Get the value of the "Donate now" checkbox
        if donate_now:
            return redirect(url_for('payment'), code=302)
        else:
            return redirect(url_for('ngo_main'), code=302)  # Replace 'home' with the route for your home page

    else:
        return render_template('donate.html')

@app.route('/coming_soon')
def coming_soon():
    return render_template('coming_soon.html')

@app.route('/payment')
def payment():
    # return redirect("https://buy.stripe.com/test_eVa0064pN0Qyd7WdQQ", code=302)
    return redirect("https://donate.stripe.com/test_9AQ7syg8vbvc1peeUW", code=302)


from sqlalchemy import or_, cast, Date
from datetime import datetime
@app.route('/donor_list')
def donor_list():
    # Get the selected help types and donation dates from the query parameters
    selected_help_types = request.args.getlist('help_type')
    selected_help_types = [help_type for help_type in selected_help_types if help_type]

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Start with a query that includes all donors
    query = Donor.query

    # If help types are selected, filter donors whose help_type field contains any of the selected help types
    if selected_help_types:
        query = query.filter(or_(*[Donor.help_type.like(f"%{help_type}%") for help_type in selected_help_types]))

    # If a date range is selected, filter donors whose donation_date field is within the selected range
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Donor.donation_date.between(start_date, end_date))
        except ValueError:
            pass  # Ignore invalid dates

    # Order the donors by donation_amount from highest to lowest and then by donation_date from newest to oldest
    query = query.order_by(Donor.donation_date.desc(), Donor.donation_amount.desc())
    
    donors = query.all()

    # Get all distinct help types for the select input
    help_types = db.session.query(Donor.help_type).distinct()

    # Render the donor_list.html template and pass the donors and help types to it
    return render_template('donor_list.html', donors=donors, help_types=help_types)

from flask import Flask, request, session, flash, redirect, url_for, render_template
from datetime import datetime, timezone, timedelta
import requests

@app.route('/login', methods=['GET', 'POST'])
def login():
    ban_until = session.get('ban_until')
    if ban_until is not None:
        ban_until = datetime.strptime(ban_until, '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < ban_until:
            return render_template('login.html', ban_until=ban_until)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # hCaptcha verification
        captcha_response = request.form.get('h-captcha-response')
        secret_key = "851b6311-2caa-428c-81eb-d885f1ea4eb9"

        data = {
            'response': captcha_response,
            'secret': '851b6311-2caa-428c-81eb-d885f1ea4eb9'
        }

        response = requests.post('https://hcaptcha.com/siteverify', data=data)

        if not response.json().get('success'):
            flash('hCaptcha verification failed', 'danger')
            return render_template('login.html')

        admin_username = 'admin'
        admin_password = 'admin123'

        if username == admin_username and password == admin_password:
            session.pop('login_attempts', None)
            session.pop('first_failed_login_time', None)
            session.pop('ban_until', None)
            flash('Successful login', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
            now = datetime.now(timezone.utc)

            if 'login_attempts' in session:
                session['login_attempts'] += 1
                if session['login_attempts'] > 5 and now - session['first_failed_login_time'] <= timedelta(minutes=2):
                    if 'ban_until' not in session or now >= ban_until:
                        ban_until = now + timedelta(minutes=5)
                        session['ban_until'] = ban_until.isoformat()
                    flash('Too many failed attempts. Try again in 5 minutes.', 'danger')
                    return render_template('login.html', ban_until=ban_until)
            else:
                session['login_attempts'] = 1
                session['first_failed_login_time'] = now.isoformat()

    return render_template('login.html')

import string 
import random

def random_string(length):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        # Get data from form
        data = request.form

        # Create a new pending student
        new_pending_student = PendingStudent(name=data['name'], age=data['age'], class_=data['class_'], school=data['school'], parental_income=data['parental_income'], help_type=data['help_type'])
        db.session.add(new_pending_student)
        db.session.commit()
        flash("Registration submitted. It will be reviewed by an admin.")
        return redirect('/register_student')
    else:
        # Render the form for registering a new student
        return render_template('register_student.html')  
 
@app.route('/pending_students')
def pending_students():
    pending_students = PendingStudent.query.all()
    return render_template('pending_students.html', students=pending_students)

@app.route('/approve_student/<int:student_id>', methods=['POST'])
def approve_student(student_id):
    # Fetch the pending student
    pending_student = PendingStudent.query.get(student_id)

    if pending_student is None:
        flash('Student not found.')
        return redirect(url_for('pending_students'))

    # Create a new student and add it to the student table
    new_student = Student(
        name=pending_student.name,
        age=pending_student.age,
        class_=pending_student.class_,
        school=pending_student.school,
        parental_income=pending_student.parental_income,
        help_type=pending_student.help_type
    )
    db.session.add(new_student)

    # Delete the pending student
    db.session.delete(pending_student)

    db.session.commit()

    flash('Student approved and added to the student table.')
    return redirect(url_for('pending_students'))

@app.route('/', methods=['GET'])
def ngo_main():
    return render_template('index.html')

@app.route('/create_student', methods=['GET', 'POST'])
def create_student():
    if request.method == 'POST':
        # Generate a random name
        random_name = fake.name()

        # # Hardcoded data for development purposes
        data = {
            'name': random_name,
            'age': random.randint(10, 18),
            'class_': f'{random.randint(1, 12)}th Grade',
            'school': 'XYZ High School',
            'parental_income': random.randint(10000, 100000),
            'help_type': random.choice(['Money', 'Books', 'Fees','Other','Food','Uniform'])
        }
        # # Get data from form
        # data = request.form

        new_student = Student(name=data['name'], age=data['age'], class_=data['class_'], school=data['school'], parental_income=data['parental_income'], help_type=data['help_type'])        
        db.session.add(new_student)
        db.session.commit()
        flash("Student created")
        return redirect('/create_student')
    else:
        # Render the form for creating a new student
        return render_template('create_student.html')
    
@app.route('/students', methods=['GET'])
def get_students():
    page = request.args.get('page', 1, type=int)
    per_page = 100  # Change this as needed

    # Get filter terms from query parameters
    class_filter = request.args.get('class_filter')
    help_type_filter = request.args.get('help_type_filter')

    # Filter students
    students_query = Student.query
    if class_filter:
        students_query = students_query.filter(Student.class_ == class_filter)
    if help_type_filter:
        students_query = students_query.filter(Student.help_type == help_type_filter)

    students = students_query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Construct pagination URLs with filters if they exist
    next_url = url_for('get_students', page=students.next_num, class_filter=class_filter, help_type_filter=help_type_filter) if students.has_next else None
    prev_url = url_for('get_students', page=students.prev_num, class_filter=class_filter, help_type_filter=help_type_filter) if students.has_prev else None
    return render_template('students.html', students=students.items, next_url=next_url, prev_url=prev_url)

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/students/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def student(id):
    if request.method == 'GET':
        # Get the student from the database
        student = Student.query.get_or_404(id)
        return render_template('student.html', student=student)
    elif request.method == 'PUT':
        data = request.get_json()
        student = Student.query.get_or_404(id)
        student.name = data['name']
        student.age = data['age']
        student.class_ = data['class_']
        student.school = data['school']
        student.parental_income = data['parental_income']
        student.help_type = data['help_type']
        db.session.commit()
        return jsonify({"message": "Student updated"}), 200
    elif request.method == 'DELETE':
        student = Student.query.get_or_404(id)
        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "Student deleted"}), 200



@app.route('/students/<int:id>/update', methods=['GET', 'POST'])
def update_student(id):
    old_student = Student.query.get_or_404(id)

    if request.method == 'GET':
        # Render the update form with the old student's details
        return render_template('update_student.html', student=old_student)

    elif request.method == 'POST':
        data = request.form

        # Create a new student with the updated details
        new_student = Student(
            name=data.get('name', old_student.name),
            age=int(data.get('age', old_student.age)),
            school=data.get('school', old_student.school),
            parental_income=float(data.get('parental_income', old_student.parental_income)),
            help_type=data.get('help_type', old_student.help_type)
        )

        # Add the new student to the database
        db.session.add(new_student)

        # Delete the old student from the database
        db.session.delete(old_student)

        db.session.commit()
        return jsonify({'message': 'Student updated successfully'}), 200
  
@app.route('/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": "Student account deleted"}), 200

if __name__ == "__main__":
    app.run(debug=True)

