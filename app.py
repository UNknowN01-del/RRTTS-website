from flask import Flask, render_template, request, flash, session, redirect, url_for
from models import *
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static', template_folder='static/templates')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = 'thisissecretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='Admin Role')
        db.session.add(admin_role)
    
    customer_role = Role.query.filter_by(name='customer').first()
    if not customer_role:
        customer_role = Role(name='customer', description='Customer Role')
        db.session.add(customer_role)

    db.session.commit()

    admin = User.query.filter_by(email='admin@gmail.com').first()
    if not admin:
        admin = User(
            name='Admin User',
            email='admin@gmail.com',
            password=generate_password_hash('admin'),
            role_id=admin_role.id 
        )
        db.session.add(admin)
        db.session.commit()

#------------------------------------------------------------------------------------------------------------------------------------
# ROUTERS 
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/career')
def career():
    # Check if user is logged in
    if 'user_email' not in session:
        flash('Please log in to view job listings!', 'danger')
        return redirect(url_for('login'))
        
    user = User.query.filter_by(email=session['user_email']).first()
    return render_template('career.html', user=user)

@app.route('/login', methods=["GET", "POST"])
def login():
    # For GET requests, clear the session completely to force a fresh login
    if request.method == "GET":
        # Clear the entire session when accessing the login page
        session.clear()
        return render_template('login.html')

    # Handle POST request (login form submission)
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        flash('Credentials invalid', 'danger')
        return render_template('login.html')

    user = User.query.filter_by(email=email).first()

    if not user:
        flash('Invalid credentials', 'danger')
        return render_template('login.html')
    
    # Try to verify with hashed password first
    password_correct = False
    try:
        password_correct = check_password_hash(user.password, password)
    except:
        # If check_password_hash fails, it might be a plain text password
        pass
    
    # If hashed verification fails, check if the password is stored in plain text (for existing users)
    if not password_correct and user.password == password:
        # Update the user's password to be hashed for future logins
        user.password = generate_password_hash(password)
        db.session.commit()
        password_correct = True
    
    if not password_correct:
        flash('Invalid credentials', 'danger')
        return render_template('login.html')

    # Clear any existing flash messages before setting the success message
    session.pop('_flashes', None)
    session['user_email'] = user.email
    session['role'] = user.role.name if user.role else "customer"
    flash("Login successful!", "success")

    if session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

@app.route('/register', methods=["GET", "POST"])
def register():
    # For GET requests, clear the session completely
    if request.method == 'GET':
        # Clear the entire session when accessing the register page
        session.clear()
        return render_template('register.html')
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists. Try logging in.", "danger")
            return redirect('/register')

        customer_role = Role.query.filter_by(name='customer').first()
        if not customer_role:
            flash("Customer role missing. Please contact admin.", "danger")
            return redirect('/register')

        password_hash = generate_password_hash(password)
        new_user = User(name=username, email=email, password=password_hash, role_id=customer_role.id)
        db.session.add(new_user)
        db.session.commit()

        # Clear any existing flash messages before setting the success message
        session.pop('_flashes', None)
        flash("Registration Successful! You can now log in.", "success")
        return redirect('/login')

    return render_template('register.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        flash("Access Denied!", "danger")
        return redirect(url_for('user_dashboard'))
    
    user = User.query.filter_by(email=session['user_email']).first()
    return render_template('admin_dashboard.html', user=user)

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_email' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['user_email']).first()
    return render_template('user_dashboard.html', user=user)

@app.route('/profile_dashboard')
def profile_dashboard():
    if 'user_email' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))
        
    user = User.query.filter_by(email=session['user_email']).first()
    return render_template('profile_dashboard.html', user=user)

@app.route('/job_detail/<job_id>')
def job_detail(job_id):
    # Check if user is logged in
    if 'user_email' not in session:
        flash('Please log in to view job details!', 'danger')
        return redirect(url_for('login'))
        
    user = User.query.filter_by(email=session['user_email']).first()
    
    # In a real application, you would fetch the job details from a database
    # using the job_id parameter. For now, we'll just pass the job_id to the template.
    return render_template('job_detail.html', user=user, job_id=job_id)

#------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)