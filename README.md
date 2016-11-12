# proj7-Gcal
# Author = Trevor Enright ,  tenright@uoregon.edu

Grab appointment data from a selection of a user's Google calendars 
Provides list of busy times with a description



to get started:
bash ./configure
make run

localhost:5000 or ip address

you'll need secrets folder with admin_secrets.py
pointing to other file in secrets folder: a json file 
the json file must be the downloaded google_key_file
from https://console.developers.google.com/apis/credentials
and set it up with https://manage.auth0.com/

flask_main.py has a lots of code to handshake with google calendars



