# CS122: Course Search Engine Part 1
#
# Steven Cooklev and Shrabya Timsina
#

import re
import util
import bs4
import queue
import json
import sys
import csv

INDEX_IGNORE = set(['a',  'also',  'an',  'and',  'are', 'as',  'at',  'be',
                    'but',  'by',  'course',  'for',  'from',  'how', 'i',
                    'ii',  'iii',  'in',  'include',  'is',  'not',  'of',
                    'on',  'or',  's',  'sequence',  'so',  'social',  'students',
                    'such',  'that',  'the',  'their',  'this',  'through',  'to',
                    'topics',  'units', 'we', 'were', 'which', 'will', 'with', 'yet'])


def convert_to_soup(request):
    '''
    Convert a given request object to soup

    Inputs:
        request: a request object
    Outputs:
        returns soup of request object if request is read,
        returns None otherwise    
    '''

    html = util.read_request(request)
    if html is not None:
        soup = bs4.BeautifulSoup(html, 'lxml')
        return soup
    else:
        return None


def extract_url(tag, absolute_url):
    '''
    Given a tag with an attribute href=True, will return an absolute url of the tag

    Inputs:
        tag: a tag with an href attribute
        absolute_url: string, the full url address of the tag

    Outputs:
        url: string, the link provided in the tag
    '''
    
    url = tag.get('href')
    url = util.remove_fragment(url)
    url = util.convert_if_relative_url(absolute_url, url)
    return url


def get_words_from_text(text_block):
    '''
    Parse a block of text and returns a list of words from the text

    Inputs:
        text_block: string, a block of text

    Outputs:
        words: a list of words 
    '''

    text_block = text_block.lower()
    text_block = re.sub('[^a-z0-9]+', ' ', text_block) 
    words_pattern = r'[a-z][a-z0-9]*'
    words = re.findall(words_pattern, text_block)
    return words


def open_json_key(course_map_filename):
    '''
    Load the data of a json file into a dictionary

    Inputs:
        course_map_filename: a json file

    Outputs:
        course_number_data: a dictionary    
    '''

    with open(course_map_filename) as json_data:
        course_number_data = json.load(json_data)
    return course_number_data


def put_words_to_index(all_words, course_identifier, index_dictionary):
    '''
    Parse through all words in the course title and description, and
        updates a given dictionary with only the appropriate words

    Inputs:
        all_words: a list of all words from the course title and description
        course_identifier: int, the course identifier
        index_dictionary: dictionary with course identifiers mapped to words as key-value pairs 

    Outputs:
        index_dictionary: dictionary, the updated dictionary with identifiers mapped to words
            as key-value pairs
    '''

    words_to_index = all_words - INDEX_IGNORE
    for word in words_to_index:
        if word in index_dictionary:
            index_dictionary[word].append(course_identifier)
        else:
            index_dictionary[word] = [course_identifier]
    return index_dictionary


def get_course_identifier(course_code_and_title, course_code_identifier_map):
    '''
    Translate a course code into the corresponding course identifier

    Inputs:
        course_code_and_title:
        course_code_identifier_map: dictionary, with data from given course_map.json file
    Outputs:
        course_identifier: int, the given code for a course

    Examples:
        course_code_identifier_map = open_json_key('course_map.json')
        get_course_identifier('SPAN 10200', course_code_identifier_map) yields
            2263
    '''

    course_code = re.sub('[^A-Za-z0-9/s]+', ' ', course_code_and_title)
    course_code = re.match('[A-Z]{4} [0-9]+', course_code).group()
    course_identifier = course_code_identifier_map[course_code]
    return course_identifier


def build_dict(soup, index_dictionary, course_code_identifier_map):
    '''
    Pull the correct information from a soup object and update a given index_dictionary
        with the proper course identifiers mapped to words as key-pair values

    Inputs:
        soup: a soup object
        index_dictionary: dictionary with course identifiers mapped to words as key-value pairs
        course_code_identifier_map: dictionary with data from given course_map.json file

    Outputs:
        index_dictionary: dictionary, the updated dictionary with identifiers mapped to words
            as key-value pairs
    '''

    course_list = soup.find_all('div', class_='courseblock main')
        
    for course_block in course_list:
        
        course_block_title = course_block.find('p', class_='courseblocktitle')
        course_description = course_block.find('p', class_='courseblockdesc')

        if course_block_title is not None:
            
            words_in_title = get_words_from_text(course_block_title.text)

            if course_description is None:
                words_in_description = []
            else:

                words_in_description = get_words_from_text(course_description.text)

            #Check if the course is part of a sequence
            sequence = util.find_sequence(course_block)

            if not sequence: # if not a sequence, proceed normally

                course_identifier = get_course_identifier(course_block_title.text, course_code_identifier_map)          
                
                all_words = set(words_in_title + words_in_description)

                index_dictionary = put_words_to_index(all_words, course_identifier, index_dictionary)

            else:
                
                for subsequence in sequence:
                    
                    subsequence_title = subsequence.find('p', class_='courseblocktitle')
                    subsequence_description = subsequence.find('p', class_='courseblockdesc')
                                  
                    subsequence_identifier = get_course_identifier(subsequence_title.text, course_code_identifier_map)

                    words_in_subseq_title = get_words_from_text(subsequence_title.text)

                    if subsequence_description is None:
                        words_in_subseq_description = []

                    else:
                        words_in_subseq_description = get_words_from_text(subsequence_description.text)
                    
                    # Note words_in_title and words_in_description are the same objects for each 
                    # course that is part of the sequence
                    all_words = set(words_in_title + words_in_description 
                                        + words_in_subseq_title + words_in_subseq_description)

                    index_dictionary = put_words_to_index(all_words, subsequence_identifier, index_dictionary)

    return index_dictionary


def crawler(starting_url, limiting_domain, course_map_filename):
    '''
    Crawl the college catalog and generate a dictionary with course identifiers 
        mapped to words as key-value pairs

    Inputs:
        starting_url: string, the first url to visit, given
        limiting_domain: string, the limiting_domain of all urls
        course_map_filename: a json file
    Outputs:
        index_dictionary: dictionary, with course identifiers mapped to words as key-value pairs
    '''

    course_code_identifier_map = open_json_key(course_map_filename)

    urls_to_crawl = queue.Queue()

    # urls_crawled is a subset of urls_processed 
    urls_crawled = set() # unique set of url's already crawled
    urls_processed = set() # contains redirected urls, urls with request object = None, etc

    urls_to_crawl.put(starting_url)
    urls_crawled.add(starting_url)
    crawl_count = 0
    index_dictionary = {}

    
    while (not urls_to_crawl.empty()) and (crawl_count < 1000):
        
        next_to_crawl = urls_to_crawl.get()
        request = util.get_request(next_to_crawl)
        
        if request is not None:
            real_url = util.get_request_url(request)

            if real_url is not None:
                
                if real_url not in urls_crawled:
                    urls_crawled.add(real_url)
                    
                if real_url not in urls_processed:
                    urls_processed.add(real_url)
                    soup = convert_to_soup(request)

                    if soup is not None:

                        #update the dictionary
                        index_dictionary = build_dict(soup, index_dictionary, course_code_identifier_map)

                        #check for potential links in current page and update the queue
                        list_of_urls_in_page = soup.find_all('a', href=True)

                        for link in list_of_urls_in_page:
                            url = extract_url(link, real_url)

                            if url is not None:

                                if (url not in urls_crawled):

                                    if util.is_url_ok_to_follow(url, limiting_domain):

                                        urls_to_crawl.put(url)
                                        urls_crawled.add(url)
 

        crawl_count += 1 

    return index_dictionary 



def write_to_file(course_dict, index_filename):
    '''
    Write data that is organized as a dictionary into a csv file

    Inputs:
        course_dict: a dictionary containing the mini indexer key-value pairs
        index_filename: the desired CSV file name

    Outputs:
        CSV file
    '''

    with open(index_filename, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        for word in sorted(course_dict.keys()):
            for identifier in sorted(course_dict[word]):
                writer.writerow([identifier, word])


def go(num_pages_to_crawl, course_map_filename, index_filename):
    '''
    Crawl the college catalog and generates a CSV file with an index.

    Inputs:
        num_pages_to_crawl: the number of pages to process during the crawl
        course_map_filename: the name of a JSON file that contains the mapping
          course codes to course identifiers
        index_filename: the name for the CSV of the index.

    Outputs: 
        CSV file of the index index.
    '''

    starting_url = "http://www.classes.cs.uchicago.edu/archive/2015/winter/12200-1/new.collegecatalog.uchicago.edu/index.html"
    limiting_domain = "classes.cs.uchicago.edu"

    course_words_index = crawler(starting_url, limiting_domain, course_map_filename)

    write_to_file(course_words_index, index_filename)

    

if __name__ == "__main__":
    usage = "python3 crawl.py <number of pages to crawl>"
    args_len = len(sys.argv)
    course_map_filename = "course_map.json"
    index_filename = "catalog_index.csv"
    if args_len == 1:
        num_pages_to_crawl = 1000
    elif args_len == 2:
        try:
            num_pages_to_crawl = int(sys.argv[1])
        except ValueError:
            print(usage)
            sys.exit(0)
    else:
        print(usage)    
        sys.exit(0)


    go(num_pages_to_crawl, course_map_filename, index_filename)
