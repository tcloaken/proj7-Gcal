#! /bin/python3



# Date handling 
import arrow


def open_times(elist, begin_date, end_date, begin_time, end_time):
    """
    
    Args:  elist -->List of busy events, list of busy events should be sorted by start time
                    Busy event element should have attributes:
                        "description" : describing the event
                        "start" : start time in isoformat of event
                        "end" : end time in isoformat of event
                        "day" :  "Allday" **optional**  
           begin date, end date, 
           begin time and end time --> These are dates and times set by user to 
                                       narrow scope times to be open
                                       for example: 
                                       user selects from November 22, 2016 to November 30, 2016
                                       and from time 9:00 to 13:00
                                       Then, the only open times will be calculated between
                                       9am and 1pm on dates 22nd to the 30th of November
            
            
    Returns:  List of times that are in the scope and that aren't occupied
              by busy times.
              Each list will have attributes:
                        "description" : describing the time of open *uses busy event description*
                        "start" : start of free time
                        "end"   :  end of free time
    """
    comp = []
    #used to iterate
    date = begin_date
    #for each day in the range
    for days in arrow.Arrow.range('day',arrow.get(begin_date),arrow.get(end_date)):
        begin_time = arrow.get(begin_time).replace(day=arrow.get(days).day,month=arrow.get(days).month,year=arrow.get(days).year).isoformat()
        end_time = arrow.get(end_time).replace(day=arrow.get(days).day,month=arrow.get(days).month,year=arrow.get(days).year).isoformat()

        busies = []
        #build list of busy times for the day
        for elem in elist:
            if (arrow.get(elem['start']).day == arrow.get(date).day):
                busies.append(elem)
            
        if len(busies) == 0:
            #if no busy times during day. All day is free
            comp.append( { "description": "FREE AND CLEAR! ",
								   "start" : begin_time,
								   "end" : end_time
                                  })
            #else, cycle through busy times during the day
            #and add to list of times between them for free times
        for i, el in enumerate(busies):
            
            if(i == 0):
                cur_time = begin_time
            else :
                cur_time = busies[i-1]['end']
            if ('day' in el):
                #all day is booked, no free time
                break
            if el['start'] < cur_time:
                #start of busy time is before the time frame we're interested in
                if el['end'] < end_time:
                    #end of busy time is before the latest time we're interested in
                    cur_time = el['end']
                    if i+1 in range(len(busies)):
                        #Theres another busy time after this one on this day
                        if (busies[i+1]['start'] < end_time):
                            #next busy time is before end of time we're interested in
                            comp.append( { "description": "Free after '"+el['description']+"' until '"+busies[i+1]['description']+"'",
								   "start" : cur_time,
								   "end" : busies[i+1]['start']
                                  })
                            if busies[i+1]['end'] > end_time:
                                # busy time ends after end time we're interested in
                                break
                        else:
                            #next busy time is after end of time we're interested in
                            comp.append( { "description": "Free after '"+el['description']+"'",
								   "start" : cur_time,
								   "end" : end_time
                                  })
                    else:
                        # no more busy times in day
                        comp.append( { "description": "Free after '"+el['description']+"'",
								   "start" : cur_time,
								   "end" : end_time
                                  })
                else:
                    #busy for entire time frame we're interested in, no free time
                    break
            elif el['start'] < end_time:
                #start of busy time is before the end of time frame we're interested in
                if el['end'] < end_time:
                    #end of busy time is before the latest time we're interested in
                    #free time 
                    if cur_time == begin_time:
                        #if starting a new day, add a free block until the time
                        comp.append( { "description": "Free until '"+el['description']+"'",
								   "start" : cur_time,
								   "end" : el['start']
                                  })
                    cur_time = el['end']
                    if i+1 in range(len(busies)):
                        #multiple busy times in day
                        if (busies[i+1]['start'] < end_time):
                            #next busy time is before end of time we're interested in
                            comp.append( { "description": "Free after '"+el['description']+"' until '"+busies[i+1]['description']+"'",
								   "start" : cur_time,
								   "end" : busies[i+1]['start']
                                  })
                        else:
                            #next busy time is after end of time we're interested in
                            comp.append( { "description": "Free after '"+el['description']+"'",
								   "start" : cur_time,
								   "end" : end_time
                                  })
                    else:
                        # no more busy times in day, 
                        
                        comp.append( { "description": "And free after '"+el['description']+"'",
								   "start" : cur_time,
								   "end" : end_time
                                  })
                        
                else:
                    #free from begining to end of time
                    comp.append( { "description": "Free from begin time to '" +el['description']+"'",
								   "start" : cur_time,
								   "end" : el['start']
                                  })
            else:
                #free all day
                comp.append( { "description": "FREE AND CLEAR! ",
								   "start" : cur_time,
								   "end" : end_time
                                  })
            
                            
            
        
        upday = arrow.get(date).replace(days=+1)
        date = upday.isoformat()
        
    return comp    
                
