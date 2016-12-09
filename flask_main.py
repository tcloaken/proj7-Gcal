import flask
from flask import render_template
from flask import request
from flask import url_for
from flask import g
import uuid


import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
# import datetime # But we still need time
from dateutil import tz  # For interpreting local times
# Import module for calculating open times
import opentimes
from opentimes import open_times

# OAuth2  - Google library implementation for convenience
from oauth2client import client
import httplib2   # used in oauth2 flow

# Google API for services 
from apiclient import discovery

# Mongo database
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import secrets.admin_secrets
import secrets.client_secrets
MONGO_CLIENT_URL = "mongodb://{}:{}@localhost:{}/{}".format(
    secrets.client_secrets.db_user,
    secrets.client_secrets.db_user_pw,
    secrets.admin_secrets.port, 
    secrets.client_secrets.db)


####
# Database connection per server process
###

try: 
    dbclient = MongoClient(MONGO_CLIENT_URL)
    db = getattr(dbclient, secrets.client_secrets.db)
    collection = db.dated

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)


###
# Globals
###
import CONFIG

#  Note to CIS 322 students:  client_secrets is what you turn in.
#     You need an admin_secrets, but the grader and I don't use yours. 
#     We use our own admin_secrets file along with your client_secrets
#     file on our Raspberry Pis. 

app = flask.Flask(__name__)
app.debug=CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)
app.secret_key=CONFIG.secret_key

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = secrets.admin_secrets.google_key_file  ## You'll need this
APPLICATION_NAME = 'MeetMe class project'

#############################
#
#  Pages (routed from URLs)
#
#############################

@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Entering index")
  
  if ('user_sel' in flask.session) and (flask.session['user_sel'] == True):
    if ('user_name' not in flask.session) or (flask.session['user_name']==""):
        if flask.request.args.get("name") == "":
            flask.session['user_name'] = "D. Trump"
        else:
            flask.session['user_name'] = flask.request.args.get("name")
    flask.g.cur_b_date = flask.session['begin_date']
    flask.g.cur_e_date = flask.session['end_date']
    flask.g.length = flask.session['length']
    flask.g.b_time = arrow.get(flask.session['begin_time']).format("H:mm")
    flask.g.e_time = arrow.get(flask.session['end_time']).format("H:mm")
    flask.session['user_sel'] = False
    return render_template('splash.html')
  else:
    if ('begin_date' not in flask.session):
        init_session_values()   
    flask.g.b_time = arrow.get(flask.session['begin_time']).format("H:mm")
    flask.g.e_time = arrow.get(flask.session['end_time']).format("H:mm")
    return render_template('index.html')

  
  
@app.route("/choose")
def choose():
    ## We'll need authorization to list calendars 
    ## I wanted to put what follows into a function, but had
    ## to pull it back here because the redirect has to be a
    ## 'return' 
    app.logger.debug("Checking credentials for Google calendar access")
    credentials = valid_credentials()
    if not credentials:
      app.logger.debug("Redirecting to authorization")
      return flask.redirect(flask.url_for('oauth2callback'))

    gcal_service = get_gcal_service(credentials)
    app.logger.debug("Returned from get_gcal_service")
    flask.g.calendars = list_calendars(gcal_service)
    
    return render_template('index.html')

@app.route("/chosen")
def chosen():
    """
    After choosing the calendars this functions gets the calendars the user picked
    creates a list of the calendarIds from the args
    gets busy events from each calendar
    uses a helper function to tidy up and sort the list of events
    creates a flask.g object of the list of busy events
    RETURNS: back to index page with the list of busy events
    """
    app.logger.debug("ENTERING CHOSEN")
    credentials = valid_credentials()
    gcal_service = get_gcal_service(credentials)
    eventList = []
    flask.g.events = []
    cals = flask.request.args.getlist("calendar", type = str)
    for cal in cals:
        eventList.append(get_busies(gcal_service,cal.strip()))
        
    flask.g.events = delister(eventList)
    flask.g.opens = get_open_times(delister(eventList))
    return render_template('index.html')
	
@app.route("/done")
def done():    
    """
    Puts selected times into mongo database and returns to a completed page
    """
    app.logger.debug("ENTERING DONE")
    times = flask.request.args.getlist("free_events", type = str)
    name = flask.session['user_name']
    if len(times) == 0:
        flask.flash("You must select at least one open time to meet")
        return render_template('index.html')
    else:
        for el in times:
            print(el.split("+")[1])
            add_event(name,max(el.split("+")[0],arrow.get(el.split("+")[0]).replace(hour=get_hour(flask.session['begin_time'])).isoformat()),min(el.split("+")[1],arrow.get(el.split("+")[1]).replace(hour=get_hour(flask.session['end_time'])).isoformat()))
        return doner()

        
def get_hour(string):
    """
    returns hour from string
    """
    print ("THIS IS THE STRING", string)
    parse = string.split("T")[1]
    integer = int(parse.split(":")[0])
    
    return integer
@app.route('/index/<id>')
def user_picks(id):
    #get id from mongodb
    #fill in splash.html with global values
    """
            "start": start_date,
           "end": end_date,
           "b_time" : start_time,
           "e_time" : end_time,
           "length" : length
    """
    meet = get_meet(id)
    cur_meat = meet[0]
    flask.session['begin_date'] = cur_meat['start']
    flask.session['end_date'] = cur_meat["end"]
    flask.session['begin_time'] = cur_meat["b_time"]
    flask.session['end_time'] = cur_meat["e_time"]
    flask.session['length'] = cur_meat["length"]
    flask.session['user_sel'] = True
    flask.session['customID'] = id
    
    return flask.redirect(flask.url_for('index'))
    
    
@app.route("/restart")
def restart():       
    """
    restarts to index depending on if the user is a creator or not
    """
    flask.session['restart'] = True
    return index()

@app.route("/doner")
def doner():  
    """
    creates list of free event times
    """
    
    g.link = flask.url_for('user_picks',id=flask.session['customID'])
    recursive_remove_overlaps(get_events())
    g.free_db = get_events()
    return render_template('done.html')

    

@app.route("/select")
def select(): 
    """
    selects a free time to meet
    displays in new html 
    """
    app.logger.debug("event deleted")
    text = request.args.get("free_db", type=str)
    start = text.split("+")[0]
    new = add_select(start)
    basket = [new]
    flask.g.selected = basket
    return render_template("complete.html")    


@app.route("/send_emails")
def send_emails():  
    pass
    
@app.route("/contin")
def contin():    
    if flask.request.args.get("name") == "":
        flask.session['user_name'] = "H. Clinton"
    else:
        flask.session['user_name'] = flask.request.args.get("name")
    return flask.redirect(flask.url_for("choose"))
    
@app.route("/del_event")
def del_event():
    app.logger.debug("event deleted")
    text = request.args.get("free_db", type=str)
    date = text.split("+")[0]
    id = text.split("+")[2]
    text = text.split("+")[1]
    delete_event(text,date,id)
    return doner()
####
#
#  Google calendar authorization:
#      Returns us to the main /choose screen after inserting
#      the calendar_service object in the session state.  May
#      redirect to OAuth server first, and may take multiple
#      trips through the oauth2 callback function.
#
#  Protocol for use ON EACH REQUEST: 
#     First, check for valid credentials
#     If we don't have valid credentials
#         Get credentials (jump to the oauth2 protocol)
#         (redirects back to /choose, this time with credentials)
#     If we do have valid credentials
#         Get the service object
#
#  The final result of successful authorization is a 'service'
#  object.  We use a 'service' object to actually retrieve data
#  from the Google services. Service objects are NOT serializable ---
#  we can't stash one in a cookie.  Instead, on each request we
#  get a fresh serivce object from our credentials, which are
#  serializable. 
#
#  Note that after authorization we always redirect to /choose;
#  If this is unsatisfactory, we'll need a session variable to use
#  as a 'continuation' or 'return address' to use instead. 
#
####

def valid_credentials():
    """
    Returns OAuth2 credentials if we have valid
    credentials in the session.  This is a 'truthy' value.
    Return None if we don't have credentials, or if they
    have expired or are otherwise invalid.  This is a 'falsy' value. 
    """
    if 'credentials' not in flask.session:
      return None

    credentials = client.OAuth2Credentials.from_json(
        flask.session['credentials'])

    if (credentials.invalid or
        credentials.access_token_expired):
      return None
    return credentials


def get_gcal_service(credentials):
  """
  We need a Google calendar 'service' object to obtain
  list of calendars, busy times, etc.  This requires
  authorization. If authorization is already in effect,
  we'll just return with the authorization. Otherwise,
  control flow will be interrupted by authorization, and we'll
  end up redirected back to /choose *without a service object*.
  Then the second call will succeed without additional authorization.
  """
  app.logger.debug("Entering get_gcal_service")
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('calendar', 'v3', http=http_auth)
  app.logger.debug("Returning service")
  return service

@app.route('/oauth2callback')
def oauth2callback():
  """
  The 'flow' has this one place to call back to.  We'll enter here
  more than once as steps in the flow are completed, and need to keep
  track of how far we've gotten. The first time we'll do the first
  step, the second time we'll skip the first step and do the second,
  and so on.
  """
  app.logger.debug("Entering oauth2callback")
  flow =  client.flow_from_clientsecrets(
      CLIENT_SECRET_FILE,
      scope= SCOPES,
      redirect_uri=flask.url_for('oauth2callback', _external=True))
  ## Note we are *not* redirecting above.  We are noting *where*
  ## we will redirect to, which is this function. 
  
  ## The *second* time we enter here, it's a callback 
  ## with 'code' set in the URL parameter.  If we don't
  ## see that, it must be the first time through, so we
  ## need to do step 1. 
  app.logger.debug("Got flow")
  if 'code' not in flask.request.args:
    app.logger.debug("Code not in flask.request.args")
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)
    ## This will redirect back here, but the second time through
    ## we'll have the 'code' parameter set
  else:
    ## It's the second time through ... we can tell because
    ## we got the 'code' argument in the URL.
    app.logger.debug("Code was in flask.request.args")
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    flask.session['credentials'] = credentials.to_json()
    ## Now I can build the service and execute the query,
    ## but for the moment I'll just log it and go back to
    ## the main screen
    app.logger.debug("Got credentials")
    return flask.redirect(flask.url_for('choose'))

#####
#
#  Option setting:  Buttons or forms that add some
#     information into session state.  Don't do the
#     computation here; use of the information might
#     depend on what other information we have.
#   Setting an option sends us back to the main display
#      page, where we may put the new information to use. 
#
#####

@app.route('/setrange', methods=['POST'])
def setrange():
    """
    User chose a date range with the bootstrap daterange
    widget.
    """
    flask.session['user_name'] = request.form.get('name')
    flask.session['user_sel'] = False
    app.logger.debug("Entering setrange")  
    length = request.form.get('slider')
    daterange = request.form.get('daterange')
    flask.flash("Setrange gave us '{}'".format(daterange))
    flask.flash("From '{}' to '{}'".format(request.form.get('b_time'),request.form.get('e_time')))
    flask.flash(("For '{}' minutes").format(length))
    b_time = request.form.get('b_time')
    e_time = request.form.get('e_time')
    flask.session['daterange'] = daterange
    daterange_parts = daterange.split()
    flask.session['begin_date'] = interpret_date(daterange_parts[0])
    flask.session['end_date'] = interpret_date(daterange_parts[2])
    flask.session['begin_time'] = interpret_time(b_time)
    flask.session['end_time'] = interpret_time(e_time)
    flask.session['length'] = length
    create_meet(flask.session['begin_date'],flask.session['end_date'],flask.session['begin_time'],flask.session['end_time'],length)
    app.logger.debug("Setrange parsed {} - {}  dates as {} - {}".format(
      daterange_parts[0], daterange_parts[1], 
      flask.session['begin_date'], flask.session['end_date']))
    return flask.redirect(flask.url_for("choose"))

####
#
#   Initialize session variables 
#
####

def init_session_values():
    """
    Start with some reasonable defaults for date and time ranges.
    Note this must be run in app context ... can't call from main. 
    """
    # Default date span = tomorrow to 1 week from now
    now = arrow.now('local')     # We really should be using tz from browser
    tomorrow = now.replace(days=+1)
    nextweek = now.replace(days=+7)
    flask.session["begin_date"] = tomorrow.floor('day').isoformat()
    flask.session["end_date"] = nextweek.ceil('day').isoformat()
    flask.session["daterange"] = "{} - {}".format(
        tomorrow.format("MM/DD/YYYY"),
        nextweek.format("MM/DD/YYYY"))
    # Default time span each day, 8 to 5
    flask.session["begin_time"] = interpret_time("9am")
    flask.session["end_time"] = interpret_time("5pm")

def interpret_time( text ):
    """
    Read time in a human-compatible format and
    interpret as ISO format with local timezone.
    May throw exception if time can't be interpreted. In that
    case it will also flash a message explaining accepted formats.
    """
    app.logger.debug("Decoding time '{}'".format(text))
    time_formats = ["ha", "h:mma",  "h:mm a", "H:mm"]
    try: 
        as_arrow = arrow.get(text, time_formats).replace(tzinfo=tz.tzlocal())
        as_arrow = as_arrow.replace(year=arrow.get(flask.session["begin_date"]).year,month=arrow.get(flask.session["begin_date"]).month,day=arrow.get(flask.session["begin_date"]).day) #HACK see below
        app.logger.debug("Succeeded interpreting time")
    except:
        app.logger.debug("Failed to interpret time")
        flask.flash("Time '{}' didn't match accepted formats 13:30 or 1:30pm"
              .format(text))
        raise
    return as_arrow.isoformat()
    #HACK #Workaround
    # isoformat() on raspberry Pi does not work for some dates
    # far from now.  It will fail with an overflow from time stamp out
    # of range while checking for daylight savings time.  Workaround is
    # to force the date-time combination into the year 2016, which seems to
    # get the timestamp into a reasonable range. This workaround should be
    # removed when Arrow or Dateutil.tz is fixed.
    # FIXME: Remove the workaround when arrow is fixed (but only after testing
    # on raspberry Pi --- failure is likely due to 32-bit integers on that platform)


def interpret_date( text ):
    """
    Convert text of date to ISO format used internally,
    with the local time zone.
    """
    try:
      as_arrow = arrow.get(text, "MM/DD/YYYY").replace(
          tzinfo=tz.tzlocal())
    except:
        flask.flash("Date '{}' didn't fit expected format 12/31/2001")
        raise
    return as_arrow.isoformat()

def next_day(isotext):
    """
    ISO date + 1 day (used in query to Google calendar)
    """
    as_arrow = arrow.get(isotext)
    return as_arrow.replace(days=+1).isoformat()

####
#
#  Functions (NOT pages) that return some information
#
####


def delister(slist):
    """
    Args: list
    helper function to convert list of list of events into one list of events
    Returns: one list, sorted by date
    """
    result = []
    for elem in slist:
        for el in elem:
            result.append(el)
    return sorted(result,key=event_sort)

  
def list_calendars(service):
    """
    Given a google 'service' object, return a list of
    calendars.  Each calendar is represented by a dict.
    The returned list is sorted to have
    the primary calendar first, and selected (that is, displayed in
    Google Calendars web app) calendars before unselected calendars.
    """
    app.logger.debug("Entering list_calendars")  
    calendar_list = service.calendarList().list().execute()["items"]
    result = [ ]
    for cal in calendar_list:
        kind = cal["kind"]
        id = cal["id"]
        if "description" in cal: 
            desc = cal["description"]
        else:
            desc = "(no description)"
        summary = cal["summary"]
        # Optional binary attributes with False as default
        selected = ("selected" in cal) and cal["selected"]
        primary = ("primary" in cal) and cal["primary"]
        
        
        result.append(
          { "kind": kind,
            "id": id,
            "summary": summary,
            "selected": selected,
            "primary": primary
            })
    return sorted(result, key=cal_sort_key)

    
def get_busies(service,cal):
    """
    Args: cal  = calendarId from the calendar to get events from
    Returns: list of events from calendar from user specified range of dates and times
    """
    app.logger.debug("Entering get_busies") 
    results = [ ]
    time_earliest = arrow.get(flask.session['begin_time']).time()
    time_latest = arrow.get(flask.session['end_time']).time()
   
    page_token = None
    while True:
        events = service.events().list(calendarId=cal, pageToken=page_token).execute()
        #find events that are are in the date and time parameters
        for event in events['items']:
            if ('transparency' not in event):
                if ('dateTime' in event['start']):         
                    if event['start']['dateTime'] >= flask.session['begin_date'] and event['end']['dateTime'] <= flask.session['end_date']:
                        event_time_start = arrow.get(event['start']['dateTime']).time()
                        event_time_end = arrow.get(event['end']['dateTime']).time()
                        if (time_earliest <= event_time_start < time_latest) or (time_earliest < event_time_end <= time_latest ):
                            results.append( {"description": event['summary'],
								"start" : event['start']['dateTime'],
								"end" : event['end']['dateTime']
								})
                #elif ('date' in event['start']):
                 #   if event['start']['date'] >= flask.session['begin_date'] and event['end']['date'] <= flask.session['end_date']:
                  #      print( event['summary'], "start:", event['start'], "and end: ", event['end'])
                   #     results.append( {"description": event['summary'],
                    #                     "start" : arrow.get(event['start']['date']).replace(days=+1).floor('day').isoformat(),
                     #                    "end" : arrow.get(event['end']['date']).ceil('day').isoformat(),
                      #                   "day" : "All_day"
                       #                 })
                
        page_token = events.get('nextPageToken')
        if not page_token:
            break    
    return results

def get_open_times(elist):
    """
    Args:  list of busy events
        Uses date ranges and time ranges to narrow scope
        calls module from open times to compute list of open blocks of time
    Returns: list of times that aren't busy
    """
    earlytime = flask.session['begin_time']
    endtime = flask.session['end_time']
    startdate = flask.session['begin_date']
    enddate = flask.session['end_date']
    return open_times(elist,startdate,enddate,earlytime,endtime)
    
def event_sort( events ):
    """
    sorts events by start date
    """
    return events['start']

def cal_sort_key( cal ):
    """
    Sort key for the list of calendars:  primary calendar first,
    then other selected calendars, then unselected calendars.
    (" " sorts before "X", and tuples are compared piecewise)
    """
    if cal["selected"]:
       selected_key = " "
    else:
       selected_key = "X"
    if cal["primary"]:
       primary_key = " "
    else:
       primary_key = "X"
    return (primary_key, selected_key, cal["summary"])

def add_type(event_list):
    """
    Args: event_list -the list of events that you want to have a type
    returns event_list with an attribute added "type":"dated_events"
    
    """
    for el in event_list:
        el['type'] = "dated_events"
    
    return event_list

def get_events():
    """
    Returns all events in the database, in a form that
    can be inserted directly in the 'session' object.
    """
    records = [ ]
    for record in collection.find( { "type": "dated_events" , "customID": flask.session['customID']}):
        records.append(record)
    rec = sorted(records,key=sortoff)
    
    return sorted(rec,key=sortdate)

def sortoff(el):
    """
    returns a value from dict el of key "offset"
    """
    return int(el["offset"])
    
def sortdate(el):
    """
    returns a value from dict el of key "start"
    """
    return el["start"]
    
def add_events(event_list):
    """
    Args:  list of events with type:"event_list"
           
    adds events to the database
    Returns nothing
    """
    
    for el in event_list:
        collection.insert( el )
    return  

    
def get_meet(id):
    
    cur_meet =[]
    for col in collection.find( { "_id": ObjectId(id) } ):
        cur_meet.append(col)
    return cur_meet
        
    
def create_meet(start_date,end_date, start_time, end_time, length):
    """
    Adds a meeting to the database
    """
  
    record = { "type": "meet", 
           "start": start_date,
           "end": end_date,
           "b_time" : start_time,
           "e_time" : end_time,
           "length" : length
           
          }
    ids = collection.insert( record )
    flask.session['customID']= str(ids)
    #print (flask.session['customID'])
    return record

def add_event_helper(event):
    """
    adds event from just an event
    """
    return add_event(event['text'],event['start'],event['end'])

def add_event(text, start, end):
    """
    Args:  start -the time the event starts
           end -the time the event ends
           text - the description of the event
           
    adds events to the database
    Returns added events record
    """
    
    record = { "type": "dated_events", 
           "text": text,
           "start": start,
           "end": end,
           "offset": offset(start,end),
           "customID" : flask.session['customID']
          }
    collection.insert( record )
    return record

def add_select(start):
    """
    adds the selected time to meet into the database
    """
    text = "We meet!"
    record = {
            "type": "dated_select", 
           "text": text,
           "start": start,
           "length": flask.session['length'],
           "customID" : flask.session['customID']
            
            }
    collection.insert(record)
    return record
    
    
def offset(d1,d2):
    d = arrow.get(d2) - arrow.get(d1)
    secs = d.total_seconds()
    mins = int(secs)/60
    mins = int(mins)
    return mins
    

def recursive_remove_overlaps(elist):
    """
    requires elist to be sorted by sortoff() then sortdate()
    recursively remove overlaps
    """
   
    if len(elist) == 0:
       # print ("EXITING RECUSION")
        return
    
    
    else:
        
        bin = []
        for elm in elist:
            bin.append(elm)
            
        for i, elem in enumerate(bin):
           
            #iterates throu list to find overlaps
            if i+1 not in range(len(bin)): # if next item does not exist
               
                bin.remove(elem)
                break
            elif bin[i+1]['start'] >= elem['end']: #next item start is after current items end
              
                bin.remove(elem)
                break
            elif elem['start'] <= bin[i+1]['start'] < elem['end']:
               
                two = [elem,bin[i+1]]
                bin.remove(bin[i+1])
                bin.remove(elem)
                
                overs = combine_overlap(two)
                for i, el in enumerate(overs):
                    bin.insert(i,el)
              
                break
            else:
                
                bin.remove(elem)
        return recursive_remove_overlaps(bin)
    
def remove_from_list(smlist,blist):
    """
    takes a small list (sub set of big list) and removes it from the big list
    """
    for el in smlist:
        blist.remove(el)
    return blist
    
    
def combine_overlap(two_events):
    """
    combines two events into one
    returns list of events
    """
    start = "start"
    end = "end"
    results = []
    first = two_events[0] 
    second = two_events[1]
    ##get names of people with overlapping times
    names2 = second['text'].split(",") 
    names1 = first['text'].split(",")
    names = names2 + names1
    text = ""
    
    for el in names2:
        if el in names1:
            names.remove(el)
    for i in range(len(names)-1):
        text += str(names[i])
        if i+1 in range(len(names)):
            text += ","+str(names[i+1])
    
    if (second['start'] == first['start']):
        new = {
           "text": text,
           "start": first['start'],
           "end": first['end'],
           "customID" : flask.session['customID']
            }   
       
        delete_helper(first)
        add_event_helper(new)
        results.append(new)
        if second['end'] == first['end']:
            delete_helper(second)
        else:
            results.append(find_and_modify(second,start,first['end']))
    else: # first['end'] > second['start']:    
        new = {
           
           "text": text,
           "start": second['start'],
           "end": first['end'],
           "customID" : flask.session['customID']
            }  
        
        add_event_helper(new)
        results.append(find_and_modify(first,end,second['start']))
        results.append(new)
        results.append(find_and_modify(second,start,first['end']))
    
    
    return results
    
    

def find_and_modify(doc,point,update):
    """
    finds a document in the collection of the mongodb and updates a "point"
    Args: doc -> (the document in the db)
          point ->(either a "start" or "end")
          update ->(a new value)
          
    """
   
    for record in collection.find( { "type": "dated_events" } ):
        if(record['text'] == doc['text']) and (record['start'] == doc['start']) and (record['customID'] == doc['customID']):
            new = record
            collection.remove(record)
            new[point] = update
            print ("This is new end:",new['end'])
            return add_event_helper(new)
        else:
            continue
    return
    
    
    

def delete_helper(event):
    """
    picks out text,start, and id
    """
    return delete_event(event['text'],event['start'],event['customID'])
    
def delete_event(text,start,id):
    """
    Args:  
           text -what the says
           start -what time the event starts
    deletes a events
    Returns nothing
    """
    
    for record in collection.find( { "type": "dated_events" } ):
        if(record['text'] == text) and (record['start'] == start) and (record['customID'] == id):
            collection.remove(record)
            break
        else:
            continue
    
    return 
#################
#
# Functions used within the templates
#
#################

@app.template_filter( 'fmtdate' )
def format_arrow_date( date ):
    try: 
        normal = arrow.get( date )
        return normal.format("ddd MM/DD/YYYY")
    except:
        return "(bad date)"

@app.template_filter( 'fmttime' )
def format_arrow_time( time ):
    try:
        normal = arrow.get( time )
        return normal.format("HH:mm")
    except:
        return "(bad time)"
        
@app.template_filter( 'humanize' )
def humanize_arrow_date( date ):
    """
    Args: date in isoformat
    Returns: formated date string
    """
    
    return str(arrow.get(date).format("MMMM DD @ HH:mm"))    
#############


if __name__ == "__main__":
  # App is created above so that it will
  # exist whether this is 'main' or not
  # (e.g., if we are running under green unicorn)
  app.run(port=CONFIG.PORT,host="0.0.0.0")
    
