
from flask import current_app as app #current_app refers to the app.py that we have created 
from flask import Flask, render_template,redirect,request

from .models import *

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        