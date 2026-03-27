
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
                           students=all_students,
                           all_companies=all_companies,
                           pending_drives=pending_drives)



@app.route('/admin/approve_company/<int:company_id>',methods=['POST'])
def approve_company(company_id):
    # Security Check: Only Admins allowed
    if session.get('role')!='admin':
        flash('Unauthorized!','danger')
        return redirect(url_for('login'))
    
    # Find the company or return 404 error if not found
    company=Company.query.get_or_404(company_id)

    # Update the status
    company.is_approved=True
    db.session.commit()

    # Feedback and Redirect
    flash(f'Company "{company.company_name}" approved!','success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_blacklist/<int:user_id>',methods=['POST'])
def toggle_blacklist(user_id):
    # Check if admin
    if session.get('role') != 'admin':
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('login'))
    
    user=User.query.get_or_404(user_id)

    # Safety lock so admin can't blacklist themselves
    if user.id==session.get('user_id'):
        flash('You cannot blacklist yourself!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    user.is_blacklisted=not user.is_blacklisted
    db.session.commit()

    status='blacklisted' if user.is_blacklisted else 'activated'
    flash(f'User {user.username} has been {status}!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_drive/<int:drive_id>',methods=['POST'])
def approve_drive(drive_id):
    if session.get('role')=='admin':
        return redirect(url_for('login'))
    
    drive=PlacementDrive.query.get_or_404(drive_id)
    drive.status='Approved'
    db.session.commit()

    flash(f'Drive "{drive.job_title}" approved!','success')
    return redirect(url_for('admin_dashboard'))


@app.route('/student/dashboard')
def student_dashboard():
    # Check role
    if session.get('role')!='student':
        flash("Please login as a student","danger")
        return redirect(url_for('login'))
    
    #Fetching specific student record based on ID
    student=Student.query.filter_by(user_id=session['user_id']).first()

    if not student:
        flash("Student profile not found. Please contact admin.","warning")
        return redirect(url_for('login'))
    
    # Fetch approved companies
    approved_companies=Company.query.filter_by(is_approved=True).all()

    # fetch application
    applications= student.applications

    return render_template('student_dashboard.html',student=student,approved_companies=approved_companies,applications=applications)


@app.route('/student/edit-profile',methods=['GET','POST'])
def edit_profile():
    if session.get('role')!='student':
        flash('Please login as a student','danger')
        return redirect(url_for('login'))
    student=Student.query.filter_by(user_id=session['user_id']).first()
    if request.method=="POST":
        # Update text fields
        student.name=request.form.get('fullname')
        student.college=request.form.get('college')
        student.branch=request.form.get('branch')
        student.semester=request.form.get('semester')
        student.cgpa=request.form.get('cgpa')

        #resume update
        file=request.files.get('resume')
        if file and allowed_file(file.filename):
            file_path=os.path.join(Upload_Folder,file.filename)
            file.save(file_path)
            student.resume_path=file_path
        
        db.session.commit()
        flash("Profile updated successfully","success")
        return redirect(url_for('student_dashboard'))
    
    return render_template('edit_profile_student.html',student=student)

@app.route('/student/history')
def application_history():
    # Placeholder for now
    return "Application History Page (Coming Soon)"

@app.route('/company/<int:company_id>/details')
def view_company(company_id):
    # This matches the 'View Openings' link
    return f"Details for Company ID: {company_id} (Coming Soon)"

@app.route('/drive/<int:drive_id>/details')
def view_drive(drive_id):
    # This matches the 'View' link in Applied Drives
    return f"Details for Drive ID: {drive_id} (Coming Soon)"


@app.route('/company/dashboard')
def company_dashboard():
    # Check role
    if session.get('role')!='company':
        flash('Please login as a company','danger')
        return redirect(url_for('login'))
    
    company=Company.query.filter_by(user_id=session['user_id']).first()
    drives=PlacementDrive.query.filter_by(company_id=company.id).all()

    #count total applications across all company drives
    total_applications=sum(len(drive.applications) for drive in drives)

    return render_template('company_dashboard.html',company=company,drives=drives,total_applications=total_applications)



# controllers.py

@app.route('/company/create-drive', methods=['GET', 'POST'])
def create_drive():
    # Placeholder for the form to create a new placement drive
    return "Create Placement Drive Page (Coming Soon)"

@app.route('/company/drive/<int:drive_id>/applicants')
def view_applicants(drive_id):
    # Placeholder to see students who applied to a specific drive
    return f"List of Applicants for Drive ID: {drive_id} (Coming Soon)"

@app.route('/company/edit-profile',methods=['GET','POST'])
def edit_company_profile():
    if session.get('role')!='company':
        flash('Please login as the company HR','danger')
        return redirect(url_for('login'))
    company=Company.query.filter_by(user_id=session['user_id']).first()
    if request.method=="POST":
        # Update text fields
        company.company_name=request.form.get('company_name')
        company.website=request.form.get('website')
        company.hr_name=request.form.get('hr_name')
        company.hr_contact=request.form.get('hr_contact')
        
        db.session.commit()
        flash("Company profile updated successfully","success")
        return redirect(url_for('company_dashboard'))
    
    return render_template('edit_profile_company.html',company=company)
