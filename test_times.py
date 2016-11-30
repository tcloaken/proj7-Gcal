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
    from 8am to 6pm
    from current day to next day
    gives args to "busy_times()" start time, start date, end time and end date
    2 events are from 7am to 9am and 9pm to 10pm
    """
    start_hour = 8
    end_hour = 18
    date_range_len = 1
    start_time = arrow.now().floor('day').replace(hour=start_hour).isoformat()
    start_date = arrow.now().floor('day').isoformat()
    end_time = arrow.get(start_time).replace(hour=end_hour).isoformat()
    end_date = arrow.get(start_date).replace(days=+date_range_len).isoformat()
    
    events = [{ "description": "from 7am to 9am ",
								   "start" : str(arrow.get(start_time).replace(hour=7).isoformat()),
								   "end" : str(arrow.get(start_time).replace(hour=9).isoformat())
                                  },{ "description": "from 5pm to 7pm",
								   "start" : str(arrow.get(end_time).replace(hour=17).isoformat()),
								   "end" : str(arrow.get(end_time).replace(hour=19).isoformat())
                                  }]
    
    open = open_times(events,start_date,end_date,start_time, end_time) 
    ## should produce one block of free time from 9 am to 5 pm
    assert open[0]['start'] == arrow.get(start_time).replace(hour=9).isoformat()
    assert open[0]['end'] == arrow.get(end_time).replace(hour=17).isoformat()
    
    
    
def test_case2():
    """
    from 8am to 6pm
    from current day to next day
    gives args to "busy_times()" start time, start date, end time and end date
    3 events are from 7am to 9am and 12pm-2pm and 5pm to 7pm
    """
    start_hour = 8
    end_hour = 18
    date_range_len = 1
    start_time = arrow.now().floor('day').replace(hour=start_hour).isoformat()
    start_date = arrow.now().floor('day').isoformat()
    end_time = arrow.get(start_time).replace(hour=end_hour).isoformat()
    end_date = arrow.get(start_date).replace(days=+date_range_len).isoformat()
    
    events = [{ "description": "from 7am to 9am ",
								   "start" : str(arrow.get(start_time).replace(hour=7).isoformat()),
								   "end" : str(arrow.get(start_time).replace(hour=9).isoformat())
                                  },{ "description": "from 12pm to 2pm",
								   "start" : str(arrow.get(end_time).replace(hour=12).isoformat()),
								   "end" : str(arrow.get(end_time).replace(hour=14).isoformat())
                                  },
                                  { "description": "from 5pm to 7pm",
								   "start" : str(arrow.get(start_time).replace(hour=17).isoformat()),
								   "end" : str(arrow.get(end_time).replace(hour=19).isoformat())
                                  }]
    
    open = open_times(events,start_date,end_date,start_time, end_time) 
    ## should produce 2 blocks of free time from 9 am to 12 pm and from 2pm to 5pm
    print (open[0]['start'], " is this equal? to ", arrow.get(start_time).replace(hour=9).isoformat())
    print (open[0]['end'], " is this equal? to ", arrow.get(end_time).replace(hour=12).isoformat())
    print (open[1]['start'], " is this equal? to ", arrow.get(end_time).replace(hour=14).isoformat())
    print (open[1]['end'], " is this equal? to ", arrow.get(end_time).replace(hour=17).isoformat())
    assert open[0]['start'] == arrow.get(start_time).replace(hour=9).isoformat()
    assert open[0]['end'] == arrow.get(end_time).replace(hour=12).isoformat()
    assert open[1]['start'] == arrow.get(end_time).replace(hour=14).isoformat()
    assert open[1]['end'] == arrow.get(end_time).replace(hour=17).isoformat()
    

    
def test_case3():
    """
    from 8am to 6pm
    from current day to next day
    gives args to "busy_times()" start time, start date, end time and end date
    2 events are outside of time 
    """
    start_hour = 8
    end_hour = 18
    date_range_len = 1
    start_time = arrow.now().floor('day').replace(hour=start_hour).isoformat()
    start_date = arrow.now().floor('day').isoformat()
    end_time = arrow.get(start_time).replace(hour=end_hour).isoformat()
    end_date = arrow.get(start_date).replace(days=+date_range_len).isoformat()
    
    events = [{ "description": "from 3am to 4am ",
								   "start" : str(arrow.get(start_date).replace(hour=3).isoformat()),
								   "end" : str(arrow.get(start_date).replace(hour=4).isoformat())
                                  },{ "description": "from 7pm to 10pm",
								   "start" : str(arrow.get(start_date).replace(hour=19).isoformat()),
								   "end" : str(arrow.get(start_date).replace(hour=22).isoformat())
                                  }]
    
    open = open_times(events,start_date,end_date,start_time, end_time) 
    ## should produce 1 blocks of free time for all day
    print(open[0]['start'] ," this equals this? " , start_time)
    print(open[0]['end'] ," this equals this? " , end_time)

    assert open[0]['start'] == start_time
    assert open[0]['end'] == end_time
    
def test_case4():
    """
    from 8am to 6pm
    from current day to next day
    gives args to "busy_times()" start time, start date, end time and end date
    2 events are outside of time 
    """
    start_hour = 8
    end_hour = 18
    date_range_len = 1
    start_time = arrow.now().floor('day').replace(hour=start_hour).isoformat()
    start_date = arrow.now().floor('day').isoformat()
    end_time = arrow.get(start_time).replace(hour=end_hour).isoformat()
    end_date = arrow.get(start_date).replace(days=+date_range_len).isoformat()
    
    events = [{ "description": "from 3am to 4am ",
								   "start" : str(arrow.get(start_date).replace(hour=3).isoformat()),
								   "end" : str(arrow.get(start_date).replace(hour=4).isoformat())
                                  },{ "description": "from 3pm to 4pm",
								   "start" : str(arrow.get(start_date).replace(hour=15).isoformat()),
								   "end" : str(arrow.get(start_date).replace(hour=16).isoformat())
                                  },{ "description": "from 7pm to 10pm",
								   "start" : str(arrow.get(start_date).replace(hour=19).isoformat()),
								   "end" : str(arrow.get(start_date).replace(hour=22).isoformat())
                                  }]
    
    open = open_times(events,start_date,end_date,start_time, end_time) 
    ## should produce 2 blocks of free time for all day
    print(open[0]['start'] ," this equals this? " , start_time)
    print(open[0]['end'] ," this equals this? " , arrow.get(start_time).replace(hour=15).isoformat())

    assert open[0]['start'] == start_time
    assert open[0]['end'] == arrow.get(start_time).replace(hour=15).isoformat()
    assert open[1]['start'] == arrow.get(start_time).replace(hour=16).isoformat()
    assert open[1]['end'] == end_time
    
def test_case5():
    """
    from 8am to 6pm
    from current day to next day
    gives args to "busy_times()" start time, start date, end time and end date
    2 events are outside of time 
    """
    start_hour = 8
    end_hour = 18
    date_range_len = 1
    start_time = arrow.now().floor('day').replace(hour=start_hour).isoformat()
    start_date = arrow.now().floor('day').isoformat()
    end_time = arrow.get(start_time).replace(hour=end_hour).isoformat()
    end_date = arrow.get(start_date).replace(days=+date_range_len).isoformat()
    
    events = [{ "description": "from 3pm to 4pm",
								   "start" : str(arrow.get(start_date).replace(hour=15).isoformat()),
								   "end" : str(arrow.get(start_date).replace(hour=16).isoformat())
                                  },{ "description": "from 7pm to 10pm",
								   "start" : str(arrow.get(start_date).replace(hour=19).isoformat()),
								   "end" : str(arrow.get(start_date).replace(hour=22).isoformat())
                                  }]
    
    open = open_times(events,start_date,end_date,start_time, end_time) 
    ## should produce 2 blocks of free time for all day
    print(open[0]['start'] ," this equals this? " , start_time)
    print(open[0]['end'] ," this equals this? " , arrow.get(start_time).replace(hour=15).isoformat())

    assert open[0]['start'] == start_time
    assert open[0]['end'] == arrow.get(start_time).replace(hour=15).isoformat()
    assert open[1]['start'] == arrow.get(start_time).replace(hour=16).isoformat()
    assert open[1]['end'] == end_time   

    
def test_case6():
    """
    from 8am to 6pm
    from current day to next day
    gives args to "busy_times()" start time, start date, end time and end date
    2 events are outside of time 
    """
    start_hour = 8
    end_hour = 18
    date_range_len = 2
    start_time = arrow.now().floor('day').replace(hour=start_hour).isoformat()
    start_date = arrow.now().floor('day').isoformat()
    end_time = arrow.get(start_time).replace(hour=end_hour).isoformat()
    end_date = arrow.get(start_date).replace(days=+date_range_len).isoformat()
    
    events = [{ "description": "from 3pm to 4pm",
								   "start" : str(arrow.get(start_date).replace(hour=15).isoformat()),
								   "end" : str(arrow.get(start_date).replace(hour=16).isoformat())
                                  },{ "description": "from 7pm to 10pm",
								   "start" : str(arrow.get(start_date).replace(hour=19).isoformat()),
								   "end" : str(arrow.get(start_date).replace(hour=22).isoformat())
                                  }]
    
    open = open_times(events,start_date,end_date,start_time, end_time) 
    ## should produce 3 blocks of free time
    print(open[2]['start'] ," this equals this? " , arrow.get(start_time).replace(days=+1).isoformat())
    print(open[2]['end'] ," this equals this? " , arrow.get(end_time).replace(days=+1).isoformat())

    assert open[0]['start'] == start_time
    assert open[0]['end'] == arrow.get(start_time).replace(hour=15).isoformat()
    assert open[1]['start'] == arrow.get(start_time).replace(hour=16).isoformat()
    assert open[1]['end'] == end_time   
    assert open[2]['start'] == arrow.get(start_time).replace(days=+1).isoformat()
    assert open[2]['end'] == arrow.get(end_time).replace(days=+1).isoformat()
