### CS122, Winter 2017: Course search engine: search
###
### Steven Cooklev & Shrab-daddy Timsina


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

    cursor = connection.cursor()

    c = generate_query(args_from_ui)

    access_object = cursor.execute(c, args)
    connection = sqlite3.connect(DATABASE_FILENAME)
    connection.create_function("time_between", 4, compute_time_between)
    cursor = connection.cursor()

    (query_string, arguments) = generate_query(args_from_ui)
    print(query_string)
    print()
    print(arguments)
    print()
    resulting_table = cursor.execute(query_string, arguments)
    print(resulting_table.fetchall())






    



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

args_from_ui = {"dept":"CMSC",
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
    
    ouput_order = {'courses.dept': 1, 'courses.course_num': 2, 'sections.section_id': 3, 
                   'meeting_patterns.day': 4,'meeting_patterns.time_start': 5, 
                   'meeting_patterns.time_end': 6, 'gps.building': 7, 
                   'walking_time': 8,'sections.enrollment': 9, 'courses.title': 10}

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
                            'building': ['sections.section_id', 'meeting_patterns.day', 
                                         'meeting_patterns.time_start', 
                                          'meeting_patterns.time_end', 'gps.building', 
                                          'walking_time'],
                            'walking_time': ['sections.section_id', 'meeting_patterns.day', 
                                         'meeting_patterns.time_start', 
                                          'meeting_patterns.time_end', 'gps.building', 
                                          'walking_time'],
                            'enroll_lower': ['sections.section_id', 'meeting_patterns.day', 
                                            'meeting_patterns.time_start', 'meeting_patterns.time_end', 
                                            'sections.enrollment'],
                            'enroll_upper': ['sections.section_id', 'meeting_patterns.day', 
                                            'meeting_patterns.time_start', 'meeting_patterns.time_end', 
                                            'sections.enrollment']}

    output_attributes = set(['courses.dept', 'courses.course_num'])
    for key in dic_input:
        output_attributes.update(map_input_to_output_attributes[key])

    attribute_list = sorted(list(output_attributes), key=lambda x:ouput_order[x])

    selection = 'SELECT ' + ", ".join(attribute_list)

    return selection  


def determine_where_statement(dic_input, tables_to_access, sorted_input_keys):


    map_input_to_operation = {'terms': 'catalog_index.word IN ?',
                            'dept': 'courses.dept = ?',
                            'day' : 'meeting_patterns.day IN ?',
                            'time_start': 'meeting_patterns.time_start >= ?',
                            'walking_time': '******',
                            'building' : '******',
                            'time_end': 'meeting_patterns.time_end <= ?', 
                            'enroll_lower': 'sections.enrollment >= ?',
                            'enroll_upper': 'sections.enrollment <= ?'}
    
   

    filter_list = []
    
    for key in sorted_input_keys:

        if key == 'terms':
            if not tables_to_access:
                group_by_statement = ' GROUP BY courses.course_id HAVING COUNT (*) = ?' 
            else:
                group_by_statement = ' GROUP BY sections.section_id HAVING COUNT (*) = ?' 

 
        filter_list.append(map_input_to_operation[key])


    where_statement = ' WHERE ' + " AND ".join(filter_list)

    if "terms" in dic_input:
        where_statement = where_statement + group_by_statement
        
    
    return where_statement

'''  
    map_output_to_table = {'
    dept': 'courses', 'courses.course_num': 'courses', 'sections.section_id': 'sections', 
                   'meeting_patterns.day': 'meeting_patterns', 'meeting_patterns.time_start': 'meeting_patterns', 
                   'meeting_patterns.time_end': 'meeting_patterns', 'gps.building': 'gps', 'walking_time': 'gps', 
                'sections.enrollment': 'sections', 'courses.title': 'sections'}
'''

def find_tuple_of_arguments(dic_input, sorted_input_keys):
    arguments = ()
    
    for key in sorted_input_keys:
        


        if key == 'terms':
            terms_split = dic_input[key].split()
            required_count = len(terms_split)
            query_words = "('" + "','".join(terms_split) + "')"
            arguments = arguments + (query_words,)

        elif key == 'day':
            query_days = "('" + "','".join(dic_input[key]) + "')"
            arguments = arguments + (query_days,)

def order_input(dic_input):
    order_dict_key = {'dept': 1, 'course_num': 2, 'section_num': 3, 'day': 4, 
                'time_start': 5, 'time_end': 6, 'building': 7, 'walking_time': 8, 
                'enroll_lower': 9, 'enroll_upper': 10 'title': 11}

    ordered_input = sorted(dic_input.key(), key=lambda x:order_dict_key[x])
    return ordered_input
        else:
            arguments = arguments + (dic_input[key],)


    if "terms" in sorted_input_keys:
        arguments = arguments + (required_count,)
    
    return arguments

def generate_query(dic_input):
    """
    selection part done

    """
    input_order = {'terms': 1, 'dept': 2, 'day': 3, 'time_start': 4, 
                'time_end': 5, 'walking_time': 6, 'building': 7, 'enroll_lower': 8, 
                'enroll_upper': 9}

   

    map_output_to_table = {'courses.dept': 'courses', 'courses.course_num': 'courses', 'sections.section_id': 'sections', 
                   'meeting_patterns.day': 'meeting_patterns', 'meeting_patterns.time_start': 'meeting_patterns', 
                   'meeting_patterns.time_end': 'meeting_patterns', 'gps.building': 'gps', 'walking_time': 'gps', 
                'sections.enrollment': 'sections', 'courses.title': 'sections'}
    sorted_input_keys = sorted(dic_input.keys(), key=lambda x:input_order[x])

    map_input_to_tables_needed = {'terms': ['catalog_index'], 
                            'dept':[],
                            'day' : ['sections', 'meeting_patterns'], 
                            'time_start': ['sections', 'meeting_patterns'],
                            'time_end': ['sections', 'meeting_patterns'],
                            'building': ['sections', 'meeting_patterns', 'gps'],
                            'enroll_lower': ['sections', 'meeting_patterns'],
                            'enroll_upper': ['sections', 'meeting_patterns']}
    

    map_primary_foreign_keys = {'sections': "courses.course_id = sections.course_id",
                                'meeting_patterns': "sections.meeting_pattern_id = meeting_patterns.meeting_pattern_id",
                                'gps': 'sections.building_code = gps.building_code',
                                'catalog_index': 'courses.course_id = catalog_index.course_id'}

    
    ordered_input = ordered_input(dic_input)
        
    arguments = find_tuple_of_arguments(dic_input, sorted_input_keys)

    tables_to_access = set()
    for key in dic_input:
        tables_to_access.update(map_input_to_tables_needed[key])

    selection_statement = determine_output_attributes(dic_input)   
    where_statement = determine_where_statement(dic_input, tables_to_access, sorted_input_keys)    
    from_statement = ' FROM courses '

    

    if tables_to_access:
        
        for table in tables_to_access:
        
        #from_join_statement = ' FROM courses JOIN ' + " JOIN ".join(list(tables_to_access))

            
            if table == 'gps':
                from_statement = from_statement + ' JOIN ' + table + ' AS A ON ' + map_primary_foreign_keys[table]
                from_statement = from_statement + ' JOIN ' + table + ' AS B ON ' + map_primary_foreign_keys[table]

            else:
                from_statement = from_statement + ' JOIN ' + table + ' ON ' + map_primary_foreign_keys[table]

        #on_list = []
        
        #for table in tables_to_access:
        #    #on_list.append(map_primary_foreign_keys[table])
        #    if table = 'gps':
        #        on_list.append(map_primary_foreign_keys[table])

        #on_statement = ' ON ' + ' AND '.join(on_list) 

        #final_query = selection + from_join_statement + on_statement + where_statement + ";"

    final_query = selection_statement + from_statement + where_statement + ";"


    return final_query, arguments






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


"""
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
