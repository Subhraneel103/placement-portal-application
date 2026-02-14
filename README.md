# Placement Portal Application

Flask project with frontend using HTML CSS (Vanilla and Bootstrap) and database on SQLite3


## Challenges faced

- During logic building, instead of writing a huge chunk of python code in a single file, modularizing it into different files and storing it in /application folder seemed like a good choice. But when connecting the different components like controllers.py, models.py etc to app.py, there was an issue of circular importing...i.e. importing app.py in controllers.py while simulatenously doing the opposite. To solve this, explored a Flask functionality called current_app.
