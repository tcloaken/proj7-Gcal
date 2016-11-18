#! /bin/python3



"""
Test times from opentimes

"""
## Import modules
import opentimes
from opentimes import open_times
import arrow




def test_case1():
    """
    from 8am to 10pm
    from current day to next day
    gives args to "busy_times()" start time, start date, end time and end date
    2 events are from 7am to 9am and 9pm to 10pm
    """
    start_hour = 8
    length_of_meet = 10
    date_range_len = 1
    start_time = arrow.now().floor('day').replace(hour=start_hour).isoformat()
    start_date = arrow.now().floor('day').isoformat()
    end_time = arrow.get(start_time).replace(hours=+length_of_meet).isoformat()
    end_date = arrow.get(start_date).replace(days=+date_range_len).isoformat()
    
    events = [{ "description": "from 7am to 9am ",
								   "start" : str(arrow.get(start_time).replace(hours=-1).isoformat()),
								   "end" : str(arrow.get(start_time).replace(hours=+1).isoformat())
                                  },{ "description": "from 5pm to 7pm",
								   "start" : str(arrow.get(end_time).replace(hours=-1).isoformat()),
								   "end" : str(arrow.get(end_time).isoformat())
                                  }]
    
    open = open_times(events,start_date,end_date,start_time, end_time) 
    ## should produce one block of free time from 9 am to 5 pm
    print (open[0]['start'], " is this equal to ", str(arrow.get(start_time).replace(hours=+1).isoformat()))
    assert open[0]['start'] == arrow.get(start_time).replace(hour=9).isoformat()
    print (open[0]['end'], " is this equal to ", str(arrow.get(end_time).replace(hours=-1).isoformat()))
    assert open[0]['end'] == arrow.get(end_time).replace(hour=17).isoformat()
    
    
    
    