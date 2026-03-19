
from flask import current_app as app #current_app refers to the app.py that we have created 
from flask import Flask, render_template,redirect,request,url_for,flash,session
import os
from .models import *


#Upload storage
Upload_Folder='static/uploads/resumes'
Allowed_Extensions=['pdf','docx','pptx']

def allowed_file(filename):
    if('.' not in filename):
        return False
    ext=filename.rsplit('.',1)[1].lower()
    if ext in Allowed_Extensions:
        return True
    else:
        return False


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')

        user=User.query.filter_by(username=username).first()
        if user and user.password==password:
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            #Blacklisted user
            if user.is_blacklisted:
                session.clear()
                flash("Your account has been deactivated by the Admin.", "danger")
                return redirect(url_for('login'))
            
            if user.role == 'company':
                #Company not approved
                if not user.company.is_approved:
                    session.clear()
                    flash("Your company account is still pending admin approval.", "warning")
                    return redirect(url_for('login'))
                else:
                    return redirect(url_for('company_dashboard'))
            
            elif user.role=='admin':
                return redirect(url_for('admin_dashboard'))
            
            elif user.role=='student':
                return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid username or password", "warning")

            
            #Role based redirect
        return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/register/student',methods=['GET','POST'])
def register_student():
    if request.method=="POST":
        # taking data from html
        email=request.form.get('email')
        username=request.form.get('username')
        password=request.form.get('password')
        confirm_password=request.form.get('confirm_password')
        
        #Basic Validation
        if password!=confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('register_student'))
        
        #resume
        file=request.files.get('resume')
        if file and allowed_file(filename=file.filename):
            file_path=os.path.join(Upload_Folder,file.filename)

            os.makedirs(Upload_Folder,exist_ok=True)
            file.save(file_path)
        else:
            flash('Invalid file type. Only .docx,.pptx and .pdf files are allowed.')
            return redirect(url_for('register_student'))


        new_user=User(email=email,password=password,username=username,role="student")
        db.session.add(new_user)
        db.session.flush() 

        new_student=Student(
            user_id=new_user.id,
            name=request.form.get('fullname'),
            college=request.form.get('college'),
            branch=request.form.get('branch'),
            semester=request.form.get('semester'),
            cgpa=request.form.get('cgpa'),
            resume_path=file_path
        )
        db.session.add(new_student)
        db.session.commit()
        flash("Registration successful! You can now login!")
        return redirect(url_for('login'))
    return render_template('register_student.html')

@app.route('/register/company',methods=['GET','POST'])
def register_company():
    if request.method=="POST":
        # Data from html
        email=request.form.get('email')
        username=request.form.get('username')
        password=request.form.get('password')
        confirm_password=request.form.get('confirm_password')
        
        if password!=confirm_password:
            flash("Passwords do not match!","danger")
            return redirect(url_for('register_company'))        

        new_user=User(email=email,password=password,username=username,role="company")
        db.session.add(new_user)
        db.session.flush() 

        new_company=Company(
            user_id=new_user.id,
            company_name=request.form.get('company_name'),
            website=request.form.get('website'),
            hr_name=request.form.get('hr_name'),
            hr_contact=request.form.get('hr_contact')
        )
        db.session.add(new_company)
        db.session.commit()
        
        flash("Successful registration. Waiting for approval")
        return redirect(url_for('login'))
    return render_template('register_company.html')


        

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out!",'info')
    return redirect(url_for('login'))



## DASHBOARDS

@app.route('/admin/dashboard')
def admin_dashboard():
    # Check
    if session.get('role')!='admin':
        flash('Unauthorized!','danger')
        return redirect(url_for('login'))
    
    #Table data
    pending_companies=Company.query.filter_by(is_approved=False).all()
    all_students=Student.query.all()
    all_companies=Company.query.all()
    pending_drives=PlacementDrive.query.filter_by(status='Pending').all()

    # Statistics
    stats = {
        'students': Student.query.count(),
        'companies': Company.query.count(),
        'drives': PlacementDrive.query.count(),
        'applications': Application.query.count()
    }
    return render_template('admin_dashboard.html',
                           stats=stats,
                           pending_companies=pending_companies,
                           all_students=all_students,
                           all_companies=all_companies,
                           pending_drives=pending_drives)

