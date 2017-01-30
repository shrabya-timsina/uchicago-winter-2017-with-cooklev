### CS122, Winter 2017: Course search engine: search
###
### Steven Cooklev

from math import radians, cos, sin, asin, sqrt
import sqlite3
import json
import re
import os


# Use this filename for the database
DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'course-info.db')

def find_courses(args_from_ui):
    '''
    Takes a dictionary containing search criteria and returns courses
    that match the criteria.  The dictionary will contain some of the
    following fields:

      - dept a string
      - day is array with variable number of elements  
           -> ["'MWF'", "'TR'", etc.]
      - time_start is an integer in the range 0-2359
      - time_end is an integer an integer in the range 0-2359
      - enroll is an integer
      - walking_time is an integer
      - building ia string
      - terms is a string: "quantum plato"]

    Returns a pair: list of attribute names in order and a list
    containing query results.
    '''

    # replace with a list of the attribute names in order and a list
    # of query results.
    return ([], [])


########### auxiliary functions #################
########### do not change this code #############

def compute_time_between(lon1, lat1, lon2, lat2):
    '''
    Converts the output of the haversine formula to walking time in minutes
    '''
    meters = haversine(lon1, lat1, lon2, lat2)

    #adjusted downwards to account for manhattan distance
    walk_speed_m_per_sec = 1.1 
    mins = meters / (walk_speed_m_per_sec * 60)

    return mins


def haversine(lon1, lat1, lon2, lat2):
    '''
    Calculate the circle distance between two points 
    on the earth (specified in decimal degrees)
    '''
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c
    m = km * 1000
    return m 



def get_header(cursor):
    '''
    Given a cursor object, returns the appropriate header (column names)
    '''
    desc = cursor.description
    header = ()

    for i in desc:
        header = header + (clean_header(i[0]),)

    return list(header)


def clean_header(s):
    '''
    Removes table name from header
    '''
    for i in range(len(s)):
        if s[i] == ".":
            s = s[i+1:]
            break

    return s



########### some sample inputs #################

example_0 = {"time_start":930,
             "time_end":1500,
             "day":["MWF"]}

example_1 = {"building":"RY",
             "dept":"CMSC",
             "day":["MWF", "TR"],
             "time_start":1030,
             "time_end":1500,
             "enroll_lower":20,
             "terms":"computer science"}


'''
obtain connections and cursor for database
loop through input keys and get output attributes
this will determine the SELECT statement of the query 
generate query string based on input 
this generates the WHERE statement of the query
FROM and ON statements remain constaint (generally)
c.execute(query, args)

'''

def determine_output_attributes(dic_input):
  '''
  Given a dictionary that describes a desired query,
  returns the set of attributes to be included in output
  for find_courses functions

  Input: dic_input, a dictionary

  Output: output_attributes: set of strings
  '''
  output_attributes = set(['courses.dept', 'courses.course_num'])
  order_dict = {'courses.dept': 1, 'courses.course_num': 2, 'sections.section_id': 3, 'meeting_patterns.day': 4, 
                'meeting_patterns.time_start': 5, 'meeting_patterns.time_end': 6, 'gps.building': 7, 'walking_time': 8, 
                'sections.enrollment': 9, 'courses.title': 10}

  for key in dic_input:

    if key in ['terms', 'dept']:
      output_attributes.add('courses.title')

    if key in ['time_start', 'time_end']:
      output_attributes.update(['sections.section_id', 'meeting_patterns.day', 'meeting_patterns.time_start', 'meeting_patterns.time_end'])   

    if key in ['walking_time', 'gps.building']:
      output_attributes.update(['sections.section_id', 'meeting_patterns.day', 'meeting_patterns.time_start', 
                            'meeting_patterns.time_end', 'gps.building', 'walking_time'])

    if key in ['enroll_lower', 'enroll_upper']:
      output_attributes.update(['sections.section_id', 'meeting_patterns.day', 'meeting_patterns.time_start', 'meeting_patterns.time_end', 'sections.enrollment'])

  attribute_list = sorted(list(output_attributes), key=lambda x:order_dict[x])

  return attribute_list  

def determine_where_filters(dic_input):
    map_input_to_operation = {'terms': 'catalog_index.word = ?', 'dept': 'courses.dept = ?',
                            'day' : 'meeting_patterns.day = ?', 'time_start': 'meeting_patterns.day >= ?',
                            'time_end': 'meeting_patterns.day <= ?', 'walking_time': 'gps---',
                            'building': 'gps.building_code----', 'enroll_lower': 'meeting_patterns.time_end >= ?',
                             'enroll_upper': 'meeting_patterns.time_end <= ?'}
    
    input_filters = []
    
    for key in dic_input:
        input_filters.append(map_input_to_operation[key])
    
    return input_filters



def generate_query(dic_input):
    """
    selection part done

    """


    
    map_output_to_table = {'courses.dept': 'courses', 'courses.course_num': 'courses', 'sections.section_id': 'sections', 
                   'meeting_patterns.day': 'meeting_patterns', 'meeting_patterns.time_start': 'meeting_patterns', 
                   'meeting_patterns.time_end': 'meeting_patterns', 'gps.building': 'gps', 'walking_time': 'gps', 
                'sections.enrollment': 'sections', 'courses.title': 'sections'}

    map_primary_foreign_keys = {'sections': "courses.course_id = sections.course_id",
                                'meeting_patterns': "sections.meeting_pattern_id = meeting_patterns.meeting_pattern_id",
                                'gps': 'sections.building_code = gps.building_code',
                                'catalog_index': 'courses.course_id = catalog_index.course_id'}

    


    attribute_list = determine_output_attributes(dic_input)
    selection = 'SELECT ' + ", ".join(attribute_list)

    filter_list = determine_where_filters(dic_input)
    where_statement = ' WHERE ' + " AND ".join(filter_list)


    tables_to_access = set()
    for attribute in attribute_list:
        if map_output_to_table[attribute] != 'courses':
            tables_to_access.add(map_output_to_table[attribute])

    if not tables_to_access:

        from_statement = ' FROM courses '
        final_query = selection + from_statement + where_statement + ";"
       
    else:
        from_join_statement = ' FROM courses JOIN ' + " JOIN ".join(list(tables_to_access))

        on_list = []
        for table in tables_to_access:
            on_list.append(map_primary_foreign_keys[table])
        on_statement = ' ON ' + ' AND '.join(on_list) 

        final_query = selection + from_join_statement + on_statement + where_statement + ";"




    return final_query






def go():
    ex0 = determine_output_attributes(example_0)
    print(ex0)
    print()
    ex1 = determine_output_attributes(example_1)
    print(ex1)
    print("---")
    zz = generate_query(example_1)
    print(zz)

