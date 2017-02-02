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

#used in determine_select_statement to match required output order
ouput_order = {'courses.dept': 1, 'courses.course_num': 2, 
               'sections.section_num': 3, 'meeting_patterns.day': 4,
               'meeting_patterns.time_start': 5,'meeting_patterns.time_end': 6,
               'building': 7, 'walking_time': 8,'sections.enrollment': 9, 
               'courses.title': 10}

#used in determine_select_statement to access necessary columns
#based on different user inputs
map_input_to_output_attributes = {'terms': ['courses.title'], 
                        'dept':['courses.title'],
                        'day' : ['sections.section_num', 
                                'meeting_patterns.day', 
                                'meeting_patterns.time_start', 
                                'meeting_patterns.time_end'], 
                        'time_start': ['sections.section_num', 
                                       'meeting_patterns.day', 
                                      'meeting_patterns.time_start', 
                                      'meeting_patterns.time_end'],
                        'time_end': ['sections.section_num', 
                                     'meeting_patterns.day', 
                                     'meeting_patterns.time_start', 
                                     'meeting_patterns.time_end'],
                        'walking_time': ['sections.section_num', 
                                         'meeting_patterns.day', 
                                         'meeting_patterns.time_start', 
                                         'meeting_patterns.time_end', 
                                         'building', 'walking_time'],
                        'enroll_lower': ['sections.section_num', 
                                         'meeting_patterns.day', 
                                        'meeting_patterns.time_start', 
                                        'meeting_patterns.time_end', 
                                        'sections.enrollment'],
                        'enroll_upper': ['sections.section_num', 
                                        'meeting_patterns.day', 
                                        'meeting_patterns.time_start', 
                                        'meeting_patterns.time_end', 
                                        'sections.enrollment']}

#used in determine_where_statement to access operations
#based on different inputs provided
map_input_to_filter_operation = {'terms': 'catalog_index.word IN',
                        'dept': 'courses.dept = ?',
                        'day' : 'meeting_patterns.day IN',
                        'time_start': 'meeting_patterns.time_start >= ?',
                        'walking_time': 'walking_time <= ?',
                        'time_end': 'meeting_patterns.time_end <= ?', 
                        'enroll_lower': 'sections.enrollment >= ?',
                        'enroll_upper': 'sections.enrollment <= ?'}

#following dictionary allows up to match ?s in the where staments
#to the tuple of arguments in the correct order - used in generate query
input_order = {'building': 1, 'terms': 2, 'dept': 3, 'day': 4, 'time_start': 5, 
            'time_end': 6, 'walking_time': 7,  'enroll_lower': 8, 
            'enroll_upper': 9}

#following dictionary allows us access only necessary tables
#based on given inputs - used in generate query
map_input_to_tables_needed = {'terms': ['catalog_index'], 
                        'dept':[],
                        'day' : ['sections', 'meeting_patterns'], 
                        'time_start': ['sections', 'meeting_patterns'],
                        'time_end': ['sections', 'meeting_patterns'],
                        'walking_time': ['sections', 'meeting_patterns', 'gps'],
                        'enroll_lower': ['sections', 'meeting_patterns'],
                        'enroll_upper': ['sections', 'meeting_patterns']}

#maps to columns that allow us to join tables - - used in generate query
map_primary_foreign_keys = {'sections': ' ON courses.course_id = sections.course_id',
                            'meeting_patterns': ' ON sections.meeting_pattern_id = meeting_patterns.meeting_pattern_id',
                            'gps': ' ON sections.building_code = building',
                            'catalog_index': ' ON courses.course_id = catalog_index.course_id'}

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
    
    if not args_from_ui: #no input given by user
        return ([],[])

    connection = sqlite3.connect(DATABASE_FILENAME)
    connection.create_function("time_between", 4, compute_time_between)
    cursor = connection.cursor()

    (query_string, arguments) = generate_query(args_from_ui)
    resulting_table = cursor.execute(query_string, arguments)
    resulting_table_as_list = resulting_table.fetchall()
    connection.close()

    if not resulting_table_as_list: #no matching courses found
        header = []
    else:
        header = get_header(cursor)
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
             "day":["MWF"],
             "building": "RY"
             , "walking_time":3}

example_1 = {"building":"RY",
             "walking_time": 10,
             "dept":"CMSC",
             "day":["MWF", "TR"],
             "time_start":1030,
             "time_end":1500,
             "enroll_lower":20,
             "enroll_upper":70,
             "terms":"computer science"}

example_2 = {"dept":"BIOS",
             "day":["MWF", "TR"],
             "time_start":1030,
             "time_end":1500,
             "enroll_upper":100,
             "terms":"animal"}

eg = {"terms":"biodiversity"}
###################################################

def determine_select_statement(dic_input):
    '''
    Given a dictionary of user inputs,
    returns the attributes to be included in output
    for find_courses functions i.e to keep in SELECT statement

    Input: dic_input: a dictionary

    Output: selection: a string containing the SELECT statement
    '''
    
    #this set will always have dept and num because all combinations
    #of input require them
    output_attributes = set(['courses.dept', 'courses.course_num'])
    
    for key in dic_input:
        if key == 'building': #since always given with walking_time
            continue
        output_attributes.update(map_input_to_output_attributes[key])

    attribute_list = sorted(list(output_attributes), key=lambda x:ouput_order[x])
    selection = 'SELECT ' + ", ".join(attribute_list)

    return selection  

def determine_where_statement(dic_input, tables_to_access, sorted_input_keys):
    ''' 
    finds the filters to be included in where statement
    and returns the where statement

    Input: dic_input: a dictionary of user inputs
           tables_to_access: a set of tables to be joined in query
                        used here only to determine the GROUP BY column
                        if 'terms' is a user input
           sorted_input_keys: a list - to maintain order of where statements
                       to properly align with arguments later in find_courses

    Output: where_statement: a string containing the Where statement
    '''

    filter_list = [] #will contain all where statement filters
    
    for key in sorted_input_keys:
        if key == 'building': #since always given with walking_time
            continue
        elif key == 'terms':
            #determining number of ?s to pass to query 
            #based on number of words provided 
            terms_split = dic_input[key].split()
            required_count = len(terms_split)
            required_placeholders = ["?"] * required_count
            query_placeholders = " (" + ", ".join(required_placeholders) + ")"
            pass_to_query = map_input_to_filter_operation[key] + query_placeholders
            filter_list.append(pass_to_query)
            
            #the ? here will be replaced by the number of words in 'terms'
            #because the course_id with that count of rows will be the one
            #whose description contains all the words in terms
            if 'sections' in tables_to_access:
                group_by_statement = ' GROUP BY sections.section_id HAVING COUNT (*) = ?'
            else:
                group_by_statement = ' GROUP BY courses.course_id HAVING COUNT (*) = ?' 
        elif key == 'day':
            #determining number of ?s to pass to query 
            #based on number of day options provided 
            required_count = len(dic_input[key])
            required_placeholders = ["?"] * required_count
            query_placeholders = " (" + ", ".join(required_placeholders) + ")"
            pass_to_query = map_input_to_filter_operation[key] + query_placeholders
            filter_list.append(pass_to_query)
        else:
            filter_list.append(map_input_to_filter_operation[key])

    where_statement = ' WHERE ' + " AND ".join(filter_list)
    if "terms" in dic_input: #terms is only input that requires a group by
        where_statement = where_statement + group_by_statement
        
    return where_statement

def find_tuple_of_arguments(dic_input, sorted_input_keys):
    ''' 
    finds the tuple to be passed as the arguments to be used in
    find_courses where they replace the ?s in the query

    Input: dic_input: a dictionary of user inputs
           sorted_input_keys: a list - to maintain order of tuple
                       to properly align with the order of ?s in query

    Output: arguments: a tuple containing the arguments
    '''
    arguments = tuple()
    
    for key in sorted_input_keys:
        if key == 'terms':
            #ontaning individual words from terms and 
            #lowering case because database is in lower case
            terms_split = dic_input[key].lower().split() 
            required_count = len(terms_split) #appended+explained outside loop
            arguments = arguments + tuple(terms_split)
        elif key == 'day': #converting list to tuple   
            arguments = arguments + tuple(dic_input[key])
        else:
            arguments = arguments + (dic_input[key],)
    
    #required count replace the ? of group by statement which is always
    # at the end of the where statement, so it is the last argument appended
    #whenever 'terms' is a user input
    if "terms" in sorted_input_keys: 
        arguments = arguments + (required_count,)
    return arguments

def generate_query(dic_input):
    ''' 
    constructs the query to be passed as a string to be used in find_courses 
    and also passes the arguments to be used in the query

    Input: dic_input: a dictionary of user inputs
           
    Output: final_query: string - containing the query 
           arguments: a tuple containing the arguments
    '''
    #this is the list to align the order of ?s and arguments
    sorted_input_keys = sorted(dic_input.keys(), key=lambda x:input_order[x])
    arguments = find_tuple_of_arguments(dic_input, sorted_input_keys)

    #needed for for join statement, will be empty if only courses table required
    tables_to_access = set() 
    for key in dic_input:
        if key == 'building': #since always given with walking_time
            continue
        tables_to_access.update(map_input_to_tables_needed[key])

    selection_statement = determine_select_statement(dic_input)   

    #all combination of user inputs always require the courses table
    from_statement = ' FROM courses ' 
    #if tables other than courses are required they must be joined
    #using corresponding primary and foreign keys
    if tables_to_access:  
        for table in tables_to_access:
            if table == "gps": 
                #uses a nested query to find walking_time from input buiding 
                gps_join_statment = ' JOIN (SELECT b.building_code as building, time_between(a.lon, a.lat, b.lon, b.lat) AS walking_time FROM gps AS a JOIN gps AS b WHERE a.building_code = ?)'
                from_statement = from_statement +  gps_join_statment + map_primary_foreign_keys[table]
            else:
                from_statement = from_statement + ' JOIN ' + table + map_primary_foreign_keys[table]

    where_statement = determine_where_statement(dic_input, 
                                         tables_to_access, sorted_input_keys)    
    final_query = selection_statement + from_statement + where_statement + ";"
    return final_query, arguments

