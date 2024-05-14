from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os 
from datetime import datetime
import numpy as np
import joblib
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.secret_key = '1234'  # Change this to a secure secret key


# SQLAlchemy configurations
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create a model for the User table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)

# Create a model for the Performance table
class Performance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(255),unique=True, nullable=False)
    performance_score = db.Column(db.Integer, nullable=False)
    manager_comment = db.Column(db.String(255), nullable=False)
    manager_name = db.Column(db.String(255), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    supervisor_comment = db.Column(db.String(255))

# Create the database tables within the app context
with app.app_context():
    db.create_all()
    
    # Check if admin user exists, if not, create it
    # Check if admin user exists, if not, create it
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password='admin', role='admin', location = "UK")
        db.session.add(admin)
        db.session.commit()

    # Check if any dummy performance records exist, if not, create one
    dummy_performance = Performance.query.filter_by(employee_name='Jane Smith').first()
    if not dummy_performance:
        dummy_performance = Performance(
            employee_name='Jane Smith',
            performance_score=92,
            manager_comment='Excellent work on recent project',
            manager_name='Manager 2'
        )
        db.session.add(dummy_performance)
        db.session.commit()


# Route for the login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            if user.role == 'manager':
                return redirect(url_for('manager'))
            elif user.role == 'supervisor':
                return redirect(url_for('supervisor'))
            elif user.role == 'employee':
                return redirect(url_for('employee'))
            elif user.role == 'admin':
                return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

# Route for the manager page
@app.route('/manager', methods=['GET', 'POST'])
def manager():
    performances = Performance.query.all()
    return render_template('show_performance.html', performances=performances)

# Route for the supervisor page
@app.route('/supervisor',methods=['GET', 'POST'])
def supervisor():
    performances = Performance.query.all()
    return render_template('supervisor.html', performances=performances)

# Route for the employee page
@app.route('/employee')
def employee():
    if 'username' not in session:
        return redirect(url_for('login'))
    performances = Performance.query.all()
    return render_template('dashboard.html', username=session['username'],performances=performances)

# Route for the admin page
@app.route('/admin')
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))

    users = User.query.all()
    return render_template('admin.html', username=session['username'], users=users)

# Route for adding a new user
@app.route('/add_user', methods=['POST'])
def add_user():
    if request.method == 'POST':
        # Extract user data from the form
        username = request.form['username'].lower() 
        password = request.form['password']
        role = request.form['role']
        
        # Check if the location field is present in the form submission
        if 'location' in request.form:
            location = request.form['location'].upper()
        else:
            # Set a default location if the field is missing
            location = "Unknown"
        
        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            # Username already exists, return error message
            return jsonify({'error': 'Username already exists'}), 400
        
        # Create a new user object and add it to the database
        new_user = User(username=username, password=password, role=role, location=location)
        db.session.add(new_user)
        db.session.commit()
        
        # Redirect to the admin page after adding the user
        return redirect(url_for('admin'))

# Route for adding a comment
@app.route('/add_comment', methods=['POST'])
def add_comment():
    if request.method == 'POST':
        # Extract comment data from the form
        employee_name = request.form['employee_name']
        comment = request.form['comment']
        manager_name = request.form['manager_name']
        
        # Retrieve the performance score from the template variable
        performance_score = request.form.get('performance_score', None)
        
        if performance_score is None:
            return "Performance score not provided."
        
        # Create a new Performance object and add it to the database
        new_comment = Performance(employee_name=employee_name, 
                                  performance_score=performance_score,
                                  manager_comment=comment,
                                  manager_name=manager_name)
        db.session.add(new_comment)
        db.session.commit()

        # Redirect to the manager page after adding the comment
        return redirect(url_for('manager'))
    

@app.route('/update_comment', methods=['POST'])
def update_comment():
    if request.method == 'POST':
        # Extract form data
        performance_id = request.form['performance_id']
        new_comment = request.form['comment']
        manager_name = request.form['manager_name']
        
        # Query the performance record by ID
        performance_record = Performance.query.get(performance_id)
        if performance_record:
            # Update manager comment and name
            performance_record.manager_comment = new_comment
            performance_record.manager_name = manager_name
            # Commit changes to the database
            db.session.commit()
            # Redirect to some page (e.g., manager dashboard)
            return redirect(url_for('manager'))
        else:
            # Handle case where performance record does not exist
            return "Performance record not found."
    
@app.route('/add_supervisor_comment', methods=['POST'])
def add_supervisor_comment():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Extract form data
        employee_name = request.form['employee_name']
        supervisor_comment = request.form['supervisor_comment']

        # Retrieve the performance object from the database
        performance = Performance.query.filter_by(employee_name=employee_name).first()

        if performance is None:
            return "Performance not found.", 404

        # Update the supervisor comment
        performance.supervisor_comment = supervisor_comment
        db.session.commit()

        # Redirect back to the supervisor page
        return redirect(url_for('supervisor'))

    # If the request method is not POST, redirect to supervisor page
    return redirect(url_for('supervisor'))
    

@app.route('/add_performance_form', methods=['POST'])
def add_performance_form():
    gender_f = 0
    gender_m = 0
    profession_S = 0
    profession_M = 0
    way_bus = 0
    way_car	= 0
    way_foot = 0
    # Retrieve form data
    name = request.form['employeeList']
    age = request.form['age']
    extraversion = request.form['extraversion']
    independ = request.form['independ']
    selfcontrol = request.form['selfcontrol']
    anxiety = request.form['anxiety']
    novator = request.form['novator']
    gender = request.form['gender']
    profession = request.form['profession']
    way = request.form['way']
    engagement = request.form['engagement']
    employee_satisfaction = request.form['employee_satisfaction']

    if gender == 'm':
        gender_f = 0
        gender_m = 1
    else:
        gender_f = 1
        gender_m = 0
    
    if profession == 'S':
        profession_S = 0
        profession_M = 1
    else:
        profession_S = 1
        profession_M = 0

    if way == 'b':
        way_bus = 1
        way_car	= 0 
        way_foot = 0
    elif way == 'c':
        way_bus = 0
        way_car	= 1
        way_foot = 0
    else:
        way_bus = 0
        way_car	= 0
        way_foot = 1

    model1 = joblib.load('models\\regression_model.h5')
    
    arr1 = np.array([[0.5,int(age),float(extraversion) ,float(independ), float(selfcontrol) ,float(anxiety),float(novator),gender_f,gender_m,0,0,profession_S,profession_M,0,1,way_bus,way_car,way_foot]])
    value1 =  model1.predict( arr1.reshape(1, -1))[0]


    model2 = joblib.load('models\\Dt_model.joblib')
    arr2 = np.array([[int(3),int(engagement),int(employee_satisfaction),int(2)]])
    value2 =  model2.predict(arr2)[0]
    # Weighted Average=(0.7×value1)+(0.3×value2) this is how the performance is calculated 
    performance  = value1 + value2



    users = User.query.all()
    return render_template('add_comment.html',performance_score=performance,users=users,name=name)



@app.route('/test_add_performance')
def test_add_performance():
    users = User.query.all()
    return render_template('add_performance.html',users=users)



if __name__ == '__main__':
    app.run(debug=True)
