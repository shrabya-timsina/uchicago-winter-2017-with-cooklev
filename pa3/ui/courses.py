### CS122, Winter 2017: Course search engine: search
###

### Steven Cooklev & Shrabya Timsina


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

    connection = sqlite3.connect(DATABASE_FILENAME)
    connection.create_function("time_between", 4, compute_time_between)
    cursor = connection.cursor()

    if 'building' in args_from_ui:
        query_lon_lat = "SELECT lon, lat FROM gps WHERE building_code = ?"
        lon_lat = cursor.execute(query_lon_lat, (args_from_ui['building'],))
        lon_lat_as_list = lon_lat.fetchall()
        lon_lat_as_tuple = lon_lat_as_list[0]
    else:
        lon_lat_as_tuple = tuple()


    (query_string, arguments) = generate_query(args_from_ui, lon_lat_as_tuple)
    #print(query_string)
    #print(query_string)
    #print()
    #print(arguments)
    #print()
    resulting_table = cursor.execute(query_string, arguments)
    resulting_table_as_list = resulting_table.fetchall()
    #print(resulting_table_as_list)
    #print(get_header(cursor))
    
    if not resulting_table_as_list:
        header = []
    else:
        header = get_header(cursor)


    #print(header)


    return (header, resulting_table_as_list)



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
             "walking_time": 10,
             "dept":"CMSC",
             "day":["MWF", "TR"],
             "time_start":1030,
             "time_end":1500,
             "enroll_lower":20,
             "terms":"computer science"}

example_2 = {"dept":"CMSC",
             "day":["MWF", "TR"],
             "time_start":1030,
             "time_end":1500,
             "enroll_lower":20,
             "terms":"computer science"}

eg = {"terms":"biodiversity"}


def determine_output_attributes(dic_input):
    '''
    Given a dictionary that describes a desired query,
    returns the set of attributes to be included in output
    for find_courses functions

    Input: dic_input, a dictionary

    Output: output_attributes: set of strings
    '''
    
    ouput_order = {'courses.dept': 1, 'courses.course_num': 2, 'sections.section_id': 3, 
                   'meeting_patterns.day': 4,'meeting_patterns.time_start': 5, 
                   'meeting_patterns.time_end': 6, 'gps.building_code': 7, 
                   'time_between(gps.lon, gps.lat, ?, ?) AS walking_time': 8,
                   'sections.enrollment': 9, 'courses.title': 10}

    map_input_to_output_attributes = {'terms': ['courses.title'], 
                            'dept':['courses.title'],
                            'day' : ['sections.section_id', 'meeting_patterns.day', 
                                          'meeting_patterns.time_start', 
                                          'meeting_patterns.time_end'], 
                            'time_start': ['sections.section_id', 'meeting_patterns.day', 
                                          'meeting_patterns.time_start', 
                                          'meeting_patterns.time_end'],
                            'time_end': ['sections.section_id', 'meeting_patterns.day', 
                                          'meeting_patterns.time_start', 
                                          'meeting_patterns.time_end'],
                            'walking_time': ['sections.section_id', 'meeting_patterns.day', 
                                         'meeting_patterns.time_start', 
                                          'meeting_patterns.time_end', 'gps.building_code', 
                                          'time_between(gps.lon, gps.lat, ?, ?) AS walking_time'],
                            'enroll_lower': ['sections.section_id', 'meeting_patterns.day', 
                                            'meeting_patterns.time_start', 'meeting_patterns.time_end', 
                                            'sections.enrollment'],
                            'enroll_upper': ['sections.section_id', 'meeting_patterns.day', 
                                            'meeting_patterns.time_start', 'meeting_patterns.time_end', 
                                            'sections.enrollment']}

    output_attributes = set(['courses.dept', 'courses.course_num'])
    
    for key in dic_input:
        if key == 'building':
            continue

        output_attributes.update(map_input_to_output_attributes[key])

    attribute_list = sorted(list(output_attributes), key=lambda x:ouput_order[x])

    selection = 'SELECT ' + ", ".join(attribute_list)

    return selection  


def determine_where_statement(dic_input, tables_to_access, sorted_input_keys):


    map_input_to_operation = {'terms': 'catalog_index.word IN',
                            'dept': 'courses.dept = ?',
                            'day' : 'meeting_patterns.day IN',
                            'time_start': 'meeting_patterns.time_start >= ?',
                            #'building': 'A.building_code = ?',
                            'walking_time': 'walking_time <= ?',
                            'time_end': 'meeting_patterns.time_end <= ?', 
                            'enroll_lower': 'sections.enrollment >= ?',
                            'enroll_upper': 'sections.enrollment <= ?'}
    
   

    filter_list = []
    
    for key in sorted_input_keys:
        if key == 'building':
            continue

        elif key == 'terms':
            
            terms_split = dic_input[key].split()
            required_count = len(terms_split)
            required_placeholders = ["?"] * required_count

            query_placeholders = " (" + ", ".join(required_placeholders) + ")"
            pass_to_query = map_input_to_operation[key] + query_placeholders
            filter_list.append(pass_to_query)
            #print(tables_to_access)

            if 'sections' in tables_to_access:
                group_by_statement = ' GROUP BY sections.section_id HAVING COUNT (*) = ?'
            else:
                group_by_statement = ' GROUP BY courses.course_id HAVING COUNT (*) = ?' 


        elif key == 'day':
            required_count = len(dic_input[key])
            required_placeholders = ["?"] * required_count

            query_placeholders = " (" + ", ".join(required_placeholders) + ")"
            pass_to_query = map_input_to_operation[key] + query_placeholders
            filter_list.append(pass_to_query)

        else:
            filter_list.append(map_input_to_operation[key])


    where_statement = ' WHERE ' + " AND ".join(filter_list)

    if "terms" in dic_input:
        where_statement = where_statement + group_by_statement
        
    
    return where_statement


def find_tuple_of_arguments(dic_input, sorted_input_keys, lon_lat_of_building):
    arguments = lon_lat_of_building
    
    for key in sorted_input_keys:
        if key == 'building':
            continue
        
        elif key == 'terms':
            terms_split = dic_input[key].lower().split()
            required_count = len(terms_split)
            
            arguments = arguments + tuple(terms_split)

        elif key == 'day':
            
            arguments = arguments + tuple(dic_input[key])

        else:
            arguments = arguments + (dic_input[key],)


    if "terms" in sorted_input_keys:
        arguments = arguments + (required_count,)
    
    return arguments


def generate_query(dic_input, lon_lat_of_building):

    input_order = {'terms': 1, 'dept': 2, 'day': 3, 'time_start': 4, 
                'time_end': 5, 'walking_time': 6,  'enroll_lower': 7, 
                'enroll_upper': 8}


    sorted_input_keys = sorted(dic_input.keys() - ['building'], key=lambda x:input_order[x])

    map_input_to_tables_needed = {'terms': ['catalog_index'], 
                            'dept':[],
                            'day' : ['sections', 'meeting_patterns'], 
                            'time_start': ['sections', 'meeting_patterns'],
                            'time_end': ['sections', 'meeting_patterns'],
                            'walking_time': ['sections', 'meeting_patterns', 'gps'],
                            'enroll_lower': ['sections', 'meeting_patterns'],
                            'enroll_upper': ['sections', 'meeting_patterns']}
    

    map_primary_foreign_keys = {'sections': "courses.course_id = sections.course_id",
                                'meeting_patterns': "sections.meeting_pattern_id = meeting_patterns.meeting_pattern_id",
                                'gps': 'sections.building_code = gps.building_code',
                                'catalog_index': 'courses.course_id = catalog_index.course_id'}

        
    arguments = find_tuple_of_arguments(dic_input, sorted_input_keys, lon_lat_of_building)

    tables_to_access = set()
    for key in dic_input:
        if key == 'building':
            continue
        tables_to_access.update(map_input_to_tables_needed[key])

    selection_statement = determine_output_attributes(dic_input)   
    where_statement = determine_where_statement(dic_input, tables_to_access, sorted_input_keys)    
    from_statement = ' FROM courses '

    

    if tables_to_access:
        
        for table in tables_to_access:
            from_statement = from_statement + ' JOIN ' + table + ' ON ' + map_primary_foreign_keys[table]

    final_query = selection_statement + from_statement + where_statement + ";"


    return final_query, arguments








"""
def go():
    #ex0 = determine_output_attributes(example_0)
    #print(ex0)
    #print()
    #ex1 = determine_output_attributes(example_1)
    #print(ex1)
    #print()
    yy = generate_query(example_0)
    print("---ex0 query follows")
    print(yy)
    print()
    print("---ex1 query follows------")
    zz = generate_query(example_1)
    print(zz)
    print()

    #print("---ex2 query follows------")
    #zzz = generate_query(example_2)
    #print(zzz)


example_2 = {"dept":"CMSC",
             "day":["MWF", "TR"],
             "time_start":1030,
             "time_end":1500,
             "enroll_lower":20,
             "terms":"computer science"}

SELECT courses.dept, courses.course_num, 
sections.section_id, meeting_patterns.day, meeting_patterns.time_start, 
meeting_patterns.time_end, sections.enrollment, courses.title 
FROM courses JOIN meeting_patterns 
JOIN catalog_index 
JOIN sections 
ON sections.meeting_pattern_id = meeting_patterns.meeting_pattern_id 
AND courses.course_id = catalog_index.course_id 
AND courses.course_id = sections.course_id 
WHERE meeting_patterns.time_start >= 1030
AND meeting_patterns.time_end <= 1500
AND meeting_patterns.day IN ('MWF','TR') 
AND courses.dept = 'CMSC'
AND catalog_index.word IN ('computer','science') 
GROUP BY sections.section_id HAVING COUNT (*) = 2;

SELECT courses.dept, courses.course_num, 
sections.section_id, meeting_patterns.day, meeting_patterns.time_start, 
meeting_patterns.time_end, sections.enrollment, courses.title 
FROM courses JOIN meeting_patterns 
JOIN catalog_index 
JOIN sections 
ON sections.meeting_pattern_id = meeting_patterns.meeting_pattern_id 
AND courses.course_id = catalog_index.course_id 
AND courses.course_id = sections.course_id 
AND meeting_patterns.day IN ('MWF','TR') 
AND courses.dept = 'CMSC'
AND catalog_index.word IN ('computer','science') 
GROUP BY sections.section_id HAVING COUNT (*) = 2;
"""

"""
connection = sqlite3.connect(DATABASE_FILENAME)
connection.create_function("time_between", 4, compute_time_between)
cursor = connection.cursor()
s = "SELECT a.building_code, b.building_code, time_between(a.lon, a.lat, b.lon, b.lat) AS walking_time FROM gps AS a JOIN gps AS b WHERE a.building_code = 'RY' AND walking_time <= 10"



st = 'SELECT courses.dept, courses.course_num, sections.section_id, meeting_patterns.day, meeting_patterns.time_start, meeting_patterns.time_end, A. building_code, B.building_code, time_between(A.lon, A.lat, B.lon, B.lat) AS walking_time, sections.enrollment, courses.title FROM courses  JOIN meeting_patterns ON sections.meeting_pattern_id = meeting_patterns.meeting_pattern_id JOIN catalog_index ON courses.course_id = catalog_index.course_id JOIN sections ON courses.course_id = sections.course_id JOIN gps AS A ON sections.building_code = A.building_code JOIN gps AS B ON sections.building_code = B.building_code WHERE catalog_index.word IN (?, ?) AND courses.dept = ? AND meeting_patterns.day IN (?, ?) AND meeting_patterns.time_start >= ? AND meeting_patterns.time_end <= ? AND A.building_code = ? AND sections.enrollment >= ? GROUP BY sections.section_id HAVING COUNT (*) = ?;'
args = ('computer', 'science', 'CMSC', 'MWF', 'TR', 1030, 1500, 'RY',20, 2)
resulting_table = cursor.execute(st, args)
resulting_table_as_list = resulting_table.fetchall()
print(resulting_table_as_list)
"""