from .database import db
from datetime import datetime

class User(db.Model):
    #Name of table
    __tablename__="users"
    #attributes
    id=db.Column(db.Integer(),primary_key=True)
    username=db.Column(db.String(100),nullable=False,unique=True)
    email=db.Column(db.String(200),nullable=False,unique=True)
    password=db.Column(db.String(255),nullable=False)
    role=db.Column(db.String(10),nullable=False,default="student")
    created_at=db.Column(db.DateTime(),default=datetime.now)
    is_blacklisted=db.Column(db.Boolean(),default=False)

    #relationships (Both are parent side relns)
    company=db.relationship("Company",back_populates="user",uselist=False,cascade="all,delete-orphan")
    student=db.relationship("Student",back_populates="user",uselist=False,cascade="all,delete-orphan")


class Student(db.Model):
    __tablename__="students"
    id=db.Column(db.Integer(),primary_key=True)
    user_id=db.Column(db.Integer(),db.ForeignKey("users.id"),nullable=False)
    name=db.Column(db.String(100),nullable=False)
    college=db.Column(db.String(200),nullable=False)
    branch=db.Column(db.String(100),nullable=False)
    semester=db.Column(db.String(10),nullable=False)
    cgpa=db.Column(db.Float(),nullable=False)
    resume_path=db.Column(db.String(400)) #This will store the file path of where the resume is stored
    
    #relationships
    user=db.relationship("User",back_populates="student") #Child side
    applications=db.relationship("Application",back_populates="student",cascade="all,delete-orphan") #Parent side

class Company(db.Model):
    __tablename__="companies"
    id=db.Column(db.Integer(),primary_key=True)
    user_id=db.Column(db.Integer(),db.ForeignKey("users.id"),nullable=False)
    company_name=db.Column(db.String(200),nullable=False)
    hr_name=db.Column(db.String(100),nullable=True)
    hr_contact=db.Column(db.String(100),nullable=True)
    website=db.Column(db.String(200),nullable=True)
    is_approved=db.Column(db.Boolean(),default=False) # Until Admin toggles this on the company wont be approved and wont be shown in dashboard


    #relationships
    user=db.relationship("User",back_populates="company") #Child side
    drives=db.relationship("PlacementDrive",back_populates="company",cascade="all,delete-orphan") #Parent side

    
class PlacementDrive(db.Model):
    __tablename__="placement_drives"
    id=db.Column(db.Integer(),primary_key=True)
    company_id=db.Column(db.Integer(),db.ForeignKey("companies.id"),nullable=False)
    job_title=db.Column(db.String(200),nullable=False)
    job_description=db.Column(db.Text(),nullable=False)
    job_location=db.Column(db.String(200),nullable=False)
    eligibility_CGPA=db.Column(db.Float(),nullable=False)
    eligibility_criteria_others=db.Column(db.Text(),nullable=True)
    deadline=db.Column(db.DateTime(),nullable=False)
    status=db.Column(db.String(30),default='Pending') #Pending, Approved, Denied or Closed. Will be done by Admin
    allowed_branches=db.Column(db.Text(),nullable=False)
    allowed_years=db.Column(db.Text(),nullable=False)


    #relationships
    company=db.relationship("Company",back_populates="drives") #Child side
    applications=db.relationship("Application",back_populates="drive",cascade="all,delete-orphan") #Parent side


class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer(), primary_key=True)
    student_id = db.Column(db.Integer(), db.ForeignKey("students.id"), nullable=False)
    drive_id = db.Column(db.Integer(), db.ForeignKey("placement_drives.id"), nullable=False)
    application_date = db.Column(db.DateTime(), default=datetime.now)
    status=db.Column(db.String(30),default='Applied') #Applied, Shortlisted, Selected, rejected

    #relationships (Both child side)
    student=db.relationship("Student",back_populates="applications")
    drive=db.relationship("PlacementDrive",back_populates="applications")

    # Table level constraints (since neither student id or drive id can be separately unique but they can together be unique)
    __table_args__=(db.UniqueConstraint('student_id','drive_id',name='unique_application'))
