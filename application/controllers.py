
from flask import current_app as app #current_app refers to the app.py that we have created 
from flask import Flask, render_template,redirect,request,url_for,flash,session
import os
from .models import *
from datetime import datetime

from flask import jsonify

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


### HOMEPAGE INDEX
@app.route('/')
def index():
    stats={
        'active_drives':PlacementDrive.query.filter_by(status='Approved').count(),
        'companies':Company.query.count(),
        'students':Student.query.count(),
        'applications':Application.query.count()
    }

    featured_drives=PlacementDrive.query.filter_by(status='Approved').order_by(PlacementDrive.created_at.desc()).limit(3).all()
    return render_template('index.html',stats=stats,featured_drives=featured_drives)



#### REGISTRATIONS AND LOGINS

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
            web_path=file_path.replace("\\","/")
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
            resume_path=web_path
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

#ADMIN DASH
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
    active_drives=PlacementDrive.query.filter(PlacementDrive.status.in_(['Approved','Stopped'])).all()


    # Statistics
    stats = {
        'students': Student.query.count(),
        'companies': Company.query.filter_by(is_approved=True).count(),
        'drives': PlacementDrive.query.filter_by(status='Approved').count(),
        'applications': Application.query.count()
    }


    ## SEARCH

    s_q=request.args.get('student_q','')
    c_q=request.args.get('company_q','')
    
    student_query=Student.query
    if s_q:
        if s_q.isdigit():
            student_query=student_query.filter(Student.id==s_q)
        else:
            student_query=student_query.filter((Student.name.ilike(f'%{s_q}%')) |
                                                (Student.user.has(User.username).ilike(f'%{s_q}%')) | 
                                                (Student.user.has(User.email).ilike(f'%{s_q}%')) | 
                                                (Student.college.ilike(f'%{s_q}%')))
    
    all_students = student_query.all()
    company_query=Company.query.filter_by(is_approved=True)
    if c_q:
        if c_q.isdigit():
            company_query=company_query.filter(Company.id==c_q)
        else:
            company_query=company_query.filter((Company.company_name.ilike(f'%{c_q}%')) |
                                                (Company.user.has(User.username).ilike(f'%{c_q}%'))|
                                                (Company.user.has(User.email).ilike(f'%{c_q}%'))|
                                                (Company.hr_name.ilike(f'%{c_q}%')))
        
    all_companies = company_query.all()

    d_q = request.args.get('drive_q', '')
    drive_query = PlacementDrive.query.filter(PlacementDrive.status.in_(['Approved', 'Stopped']))
    if d_q:
        drive_query = drive_query.filter(PlacementDrive.job_title.ilike(f'%{d_q}%') | 
                                         PlacementDrive.allowed_branches.ilike(f'%{d_q}%')|
                                         PlacementDrive.allowed_years.ilike(f'%{d_q}%')|
                                         PlacementDrive.company.has(Company.company_name.ilike(f'%{d_q}%')))
    active_drives = drive_query.all()



    return render_template('admin_dashboard.html',
                           stats=stats,
                           pending_companies=pending_companies,
                           students=all_students,
                           all_companies=all_companies,
                           pending_drives=pending_drives,
                           active_drives=active_drives,
                           s_q=s_q,c_q=c_q,d_q=d_q)



## STUDENT DASH
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



## COMPANY DASH
@app.route('/company/dashboard')
def company_dashboard():
    # Check role
    if session.get('role')!='company':
        flash('Please login as a company','danger')
        return redirect(url_for('login'))
    
    company=Company.query.filter_by(user_id=session['user_id']).first()
    drives=PlacementDrive.query.filter_by(company_id=company.id).all()
    active_drive=PlacementDrive.query.filter_by(company_id=company.id,status='Approved').count()
    pending_drive=PlacementDrive.query.filter_by(company_id=company.id,status='Pending').count()
    #count total applications across all company drives
    total_applications=sum(len(drive.applications) for drive in drives)

    return render_template('company_dashboard.html',company=company,drives=drives,active_count=active_drive,pending_count=pending_drive,total_applications=total_applications)


#Stop a drive
@app.route('/company/stop_drive/<int:drive_id>',methods=['POST'])
def company_stop_drive(drive_id):
    drive=PlacementDrive.query.get_or_404(drive_id)

    #Security: Company ka hi drive hona chahiye
    if drive.company.user_id!=session.get('user_id'):
        flash("Unauthorized! Must use company account",'danger')
        return "Unauthorized",403
    
    drive.status='Stopped'
    db.session.commit()
    flash(f"Drive '{drive.job_title}' has been stopped.","success")
    return redirect(url_for('company_dashboard'))

#Route to resume a drive (company side)
@app.route('/company/resume_drive/<int:drive_id>',methods=['POST'])
def company_resume_drive(drive_id):
    drive=PlacementDrive.query.get_or_404(drive_id)
    if drive.company.user_id!=session.get('user_id'):
        flash("Unauthorized! Must use company account",'danger')
        return "Unauthorized",403
    drive.status = 'Approved' # Or 'Pending' if you want Admin to re-verify
    db.session.commit()
    flash(f"Drive '{drive.job_title}' has been resumed.", "success")
    return redirect(url_for('company_dashboard'))

@app.route('/company/edit-drive/<int:drive_id>',methods=['GET','POST'])
def edit_drive(drive_id):
    if session.get('role')!='company':
        return redirect(url_for('login'))
    
    drive=PlacementDrive.query.get_or_404(drive_id)
    company=Company.query.filter_by(user_id=session['user_id']).first()

    if drive.company_id!=company.id:
        flash("Unauthorized access.",'danger')
        return redirect(url_for('company_dashboard'))
    
    if request.method=="POST":
        drive.job_title=request.form.get('job_title')
        drive.job_description=request.form.get('job_description')
        drive.job_location=request.form.get('job_location')
        drive.eligibility_CGPA=request.form.get('eligibility_CGPA')
        drive.eligibility_criteria_others=request.form.get('eligibility_others')
        drive.allowed_branches=request.form.get('allowed_branches')
        drive.allowed_years=request.form.get('allowed_years')

        deadline_str=request.form.get('deadline')
        if deadline_str:
            drive.deadline=datetime.strptime(deadline_str,'%Y-%m-%d')
        
        db.session.commit()
        flash("Drive updated successfully",'success')
        return redirect(url_for('company_dashboard'))
    
    return render_template('edit_drive.html',drive=drive)



    


## ADMIN METHODSS

#APPROVE COMP
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

## REJECT COMP
@app.route('/admin/reject_company/<int:company_id>',methods=['POST'])
def reject_company(company_id):
    if session.get('role')!='admin':
        return redirect(url_for('login'))
    company=Company.query.get_or_404(company_id)
    
    #deleting the user record as well to free up space
    user=User.query.get(company.user_id)
    if user:
        db.session.delete(user)
    
    db.session.commit()
    flash(f"Registration for {company.company_name} has been rejected.","success")

    return redirect(url_for('admin_approvals'))

## REVIEW COMP
@app.route('/admin/review_company/<int:company_id>',methods=['POST','GET'])
def review_company(company_id):
    if session.get('role')!='admin':
        flash('Unauthorized!','danger')
        return redirect(url_for('login'))
    
    company=Company.query.get_or_404(company_id)
    return render_template('admin_review_company.html',company=company)


### USER BLACKLISTING
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


## USER DELETION
@app.route('/admin/delete_user/<int:user_id>',methods=['POST'])
def delete_user(user_id):
    if session.get('role')!='admin':
        flash("Unauthorized! Only admins allowed",'danger')
        return redirect(url_for('login'))
    user=User.query.get_or_404(user_id)
    
    # Logic to prevent Admin self deletion
    if user.id==session.get('user_id'):
        flash('You cannot delete yourself!','danger')
        return redirect(url_for('admin_dashboard'))
    
    username=user.username
    db.session.delete(user)
    db.session.commit()

    flash(f"Account for {username} has been deleted successfully",'success')
    return redirect(url_for('admin_dashboard'))

    

## DRIVE APPROVAL
@app.route('/admin/approve_drive/<int:drive_id>',methods=['POST'])
def approve_drive(drive_id):
    if session.get('role')!='admin':
        flash("Unauthorised access. Login as admin!",'danger')
        return redirect(url_for('login'))
    
    drive=PlacementDrive.query.get_or_404(drive_id)
    drive.status='Approved'
    db.session.commit()

    flash(f'Drive "{drive.job_title}" approved and posted.','success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_drive/<int:drive_id>',methods=['POST'])
def reject_drive(drive_id):
    if session.get('role') != 'admin':
        flash("Unauthorised access. Login as admin!",'danger')        
        return redirect(url_for('login'))
    
    drive=PlacementDrive.query.get_or_404(drive_id)
    drive.status='Denied'
    db.session.commit()

    flash(f'Drive "{drive.job_title}" rejected.','success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/review_drive/<int:drive_id>')
def admin_review_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    drive = PlacementDrive.query.get_or_404(drive_id)
    return render_template('admin_review_drive.html', drive=drive)


@app.route('/admin/stop_drive/<int:drive_id>', methods=['POST'])
def stop_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Stopped'  # This removes it from the Student's "Active" list
    db.session.commit()
    flash(f"Placement Drive '{drive.job_title}' has been stopped.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_drive/<int:drive_id>', methods=['POST'])
def delete_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    db.session.delete(drive)
    db.session.commit()
    flash("Drive deleted from the system.", "danger")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/resume_drive/<int:drive_id>', methods=['POST'])
def resume_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    #status back to Approved to make it visible to students again
    drive.status = 'Approved'
    db.session.commit()
    
    flash(f"Placement Drive '{drive.job_title}' has been resumed and is now live.", "success")
    return redirect(url_for('admin_dashboard'))


### STUDENT METHODS

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
            web_path = file_path.replace("\\", "/")
            file.save(file_path)
            student.resume_path=file_path
        
        db.session.commit()
        flash("Profile updated successfully","success")
        return redirect(url_for('student_dashboard'))
    
    return render_template('edit_profile_student.html',student=student)

@app.route('/student/history')
def student_history():
    # Auth
    if session.get('role')!='student':
        flash('Login as student','danger')
        return redirect(url_for('login'))
    # Stud obj
    student=Student.query.filter_by(user_id=session.get('user_id')).first_or_404()
    # ordered by ID descending-> show most recent appl first.
    applications=Application.query.filter_by(student_id=student.id).order_by(Application.id.desc()).all()

    return render_template('student_history.html',student=student,applications=applications)

    
@app.route('/drive/<int:drive_id>/details')
def view_drive(drive_id):
    if session.get('role') not in ['student','company','admin']:
        return redirect(url_for('login'))
    drive=PlacementDrive.query.get_or_404(drive_id)
    student=None
    already_applied=None
    if session.get('role')=='student':
        student=Student.query.filter_by(user_id=session['user_id']).first()
        if student:
            already_applied=Application.query.filter_by(student_id=student.id,drive_id=drive.id).first()
    return render_template('view_drive.html',drive=drive,student=student,already_applied=already_applied)

@app.route('/drive/<int:drive_id>/apply',methods=['POST','GET'])
def apply_drive(drive_id):
    if session.get('role')!='student':
        return redirect(url_for('login'))
    
    student=Student.query.filter_by(user_id=session['user_id']).first()
    drive=PlacementDrive.query.get_or_404(drive_id)
    
    #Eligibility Check
    if student.cgpa<drive.eligibility_CGPA:
        flash('Warning! Your CGPA is below the required CGPA','warning')

    existing_app=Application.query.filter_by(student_id=student.id,drive_id=drive.id).first()
    if existing_app:
        flash('You have already applied for this drive','warning')
        return redirect(url_for('view_drive',drive_id=drive.id))
    
    new_application=Application(student_id=student.id,drive_id=drive.id)
    db.session.add(new_application)
    db.session.commit()

    flash(f'Drive Application submitted successfully at {drive.company.company_name}','success')
    return redirect(url_for('view_drive',drive_id=drive.id))


@app.route('/company/<int:company_id>/details')
def view_company(company_id):
    # This matches the 'View Openings' link
    if session.get('role')!='student':
        flash("login as student",'danger')
        return redirect(url_for('login'))
    
    company=Company.query.get_or_404(company_id)

    activeDrives=PlacementDrive.query.filter_by(company_id=company.id,status='Approved').all()

    return render_template('view_company.html',company=company,drives=activeDrives)



@app.route('/company/drive/<int:drive_id>/applicants',methods=['GET','POST'])
def view_applicants(drive_id):
    if session.get('role')!='company':
        flash('Login as company','danger')
        return redirect(url_for('login'))
    
    drive=PlacementDrive.query.get_or_404(drive_id)
    company=Company.query.filter_by(user_id=session['user_id']).first()

    if drive.company_id!=company.id:
        flash("Unauthorised: Not YOUR company drive!",'danger')
        return redirect(url_for('company_dashboard'))
    
    if request.method=="POST":
        application_id=request.form.get('application_id')
        new_status=request.form.get('status')

        application=Application.query.get_or_404(application_id)
        if application:
            application.status=new_status
            db.session.commit()
            flash(f'Updated status for {application.student.name} to {new_status}.','status')
    

    applicants=drive.applications
    return render_template('view_applicants.html',drive=drive,applicants=applicants)


    

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


@app.route('/company/create-drive',methods=['GET','POST'])
def create_drive():
    if session.get('role')!='company':
        flash("Not authorised. Login as company HR","danger")
        return redirect(url_for('login'))
    
    company=Company.query.filter_by(user_id=session['user_id']).first()

    if request.method=="POST":
        job_title=request.form.get('job_title')
        job_description=request.form.get('job_description')
        eligibility_CGPA=request.form.get('eligibility_CGPA')
        job_location=request.form.get('job_location')
        eligibility_others=request.form.get('eligibility_criteria_others')
        deadline=request.form.get('deadline')
        allowed_branches = request.form.get('allowed_branches')
        allowed_years = request.form.get('allowed_years')


        #CGPA float check
        try:
            eligibility_CGPA=float(eligibility_CGPA)
        except (ValueError,TypeError):
            eligibility_CGPA=0.0
            flash("Wrong values for CGPA",'warning')
        
        #deadline conversion to datetime
        deadline=datetime.strptime(deadline,'%Y-%m-%d')

        #drive object
        new_drive=PlacementDrive(
            company_id=company.id,
            job_title=job_title,
            job_description=job_description,
            job_location=job_location,
            eligibility_CGPA=eligibility_CGPA,
            eligibility_criteria_others=eligibility_others,
            deadline=deadline,
            allowed_branches=allowed_branches,
            allowed_years=allowed_years
        )

        db.session.add(new_drive)
        db.session.commit()
        flash("Drive created successfully. Waiting for Admin Approval",'success')
        return redirect(url_for('company_dashboard'))


    return render_template('create_drive.html',company=company)


@app.route('/admin/approvals')
def admin_approvals():
    if session.get('role')!='admin':
        flash("Unauthorized! Need admin access",'danger')
        return redirect(url_for('login'))
    
    pending_companies=Company.query.filter_by(is_approved=False).all()
    pending_drives=PlacementDrive.query.filter_by(status='Pending').all()

    return render_template('admin_approvals.html',pending_companies=pending_companies,pending_drives=pending_drives)

@app.route('/admin/approve_company/<int:company_id>',methods=['POST'])
def admin_approve_company(company_id):
    if session.get('role')!='admin':
        return redirect(url_for('login'))
    
    company=Company.query.get_or_404(company_id)
    company.is_approved=True
    db.session.commit()

    flash(f"Company '{company.company_name}' has been approved",'success')
    return redirect(url_for('admin_approvals'))


@app.route('/admin/history/')
def admin_history():
    if session.get('role')!='admin':
        return redirect(url_for('login'))
    
    # Searching ka query
    q=request.args.get('q','')
    
    # Historical data uthana(descending)
    drive_query=PlacementDrive.query.order_by(PlacementDrive.created_at.desc())
    if q:
        drive_query=drive_query.filter(PlacementDrive.job_title.ilike(f'%{q}%'))
    historical_drives=drive_query.all()

    #jo jo select huye
    successful_placements=Application.query.filter_by(status='Shortlisted').all()

    # kitne applications aur kitne success
    total_applications=Application.query.count()
    placed_count=len(successful_placements)
    success_rate=((placed_count/total_applications)*100) if total_applications>0 else 0

    return render_template('admin_history.html',drives=historical_drives,placements=successful_placements,q=q,placed_count=placed_count,rate=round(success_rate,2))

