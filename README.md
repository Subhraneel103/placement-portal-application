# Placement Portal Application

Flask project with frontend using HTML CSS (Vanilla and Bootstrap) and database on SQLite3


## Challenges faced

- During logic building, instead of writing a huge chunk of python code in a single file, modularizing it into different files and storing it in /application folder seemed like a good choice. But when connecting the different components like controllers.py, models.py etc to app.py, there was an issue of circular importing...i.e. importing app.py in controllers.py while simulatenously doing the opposite. To solve this, explored a Flask functionality called current_app.

- If we made the PK ID of Student the same as user id from user table, it would cause issues in the future when we change requirements or if we wish to delete records while still keeping historial data in Student table. So made them separate columns.

- Security issues which I fixed by using a Flask secret key that will store flashed messages and login data in a session cookie on the user's browser...otherwise any tech savvy person may change their role to admin and do whatever they want. If i wish to use flash() functionality, using secret key is must
- Created a base.html as a template html which will exist in all pages so as to not reinvent the wheel again and again