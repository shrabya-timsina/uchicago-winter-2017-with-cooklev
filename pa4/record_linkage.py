# CS122: Linking restaurant records in Zagat and Fodor's list
#Names: Shrabya Timsina and Steven Cooklev


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import jellyfish
import util
import re

#identify the first suffix
street_suffixes = ['Blvd\.','St\.','Ave\.','Dr\.','Rd\.','Pkwy\.','Sq\.',
                   'Hwy\.','Ln\.','Pl\.', 'Way', 'PCH', 'fl\.', 
                   'Broadway', 'Promenade']


def find_matches(mu, lambda_, outfile='./matches.csv', block_on=None):
    
    zagat_file = 'zagat.txt'
    fodor_file = 'fodors.txt'
    pairs_file = 'known_pairs.txt'

    zagat = create_df(zagat_file)
    fodors = create_df(fodor_file)
    matches = create_matches_df(zagat, fodors, pairs_file)
    unmatches = create_unmatches_df(zagat, fodors)
    m_score_vector_cat = score_vectors(matches, zagat, fodors)[1]
    u_score_vector_cat = score_vectors(unmatches, zagat, fodors)[1]
    m_vector_dict = calc_relative_freq(m_score_vector_cat)
    u_vector_dict = calc_relative_freq(u_score_vector_cat)
    histogram(matches, unmatches, zagat, fodors)
    (match_vectors, unmatch_vectors, possible_vectors) = partition_vectors(m_vector_dict, u_vector_dict, mu, lambda_)
    (match_count, possible_match_count, unmatch_count) = count_matches(zagat, fodors, match_vectors, unmatch_vectors, outfile, block_on)
    
    return (match_count, possible_match_count, unmatch_count)
  

def create_df(file_name):
    """
    Reads contents of a certain text file, and creates a pandas dataframe
    out of them and cleans the database contents
    Inputs - filename - a string that has the name of a text file with
                        restaurant information
    Outputs - df - a pandas dataframe created from contents of text file 
    """
    df = pd.read_table(file_name, header = None)[0].str.strip()
    #first extraction - splits into two groups as a number is found starting
    #from the left
    first_split = df.str.extract(r'^([^\d]*)(\d.*)$', expand=True)
    df = pd.concat([df, first_split], axis=1)
    df.columns = ['original_string', 'restaurant_name', 'address_city']

    if file_name == 'zagat.txt':
        street_suffixes.extend(['Walk', 'Central Park S\.', 'Circle', 'Plaza'])
        df.iloc[55,1:] = ["Martha's 22nd Street Grill", '25 22nd St. Hermosa Beach']
        df.iloc[73,1:] = ['R-23', '923 E. Third St. Los Angeles']
        df.iloc[91,1:] = ['21 Club', '21 W. 52nd St. New York City']
        df.iloc[215,1:] = ['103 West', '103 W. Paces Ferry Rd. Atlanta']

    elif file_name == 'fodors.txt':
        street_suffixes.extend(['Sts\.', 'Aves\.', 'Center', 'Alley', 'Mall', 
            'Plaza', 'Road', 'Drive', 'of the Stars', 'La\.', 'Norcross', 
            'Central Park S', 'Hotel', 'River','Condominium','Hyatt'])  
        df.iloc[31,1:] = ["Gladstone's 4 Fish", 'Pacific Coast Hwy. at Sunset Blvd. Pacific Palisades']
        df.iloc[83,1:] = ['21 Club', '21 W. 52nd St. New York']
        df.iloc[84,1:] = ['20 Mott', '20 Mott St.  between Bowery and Pell St. New York']
        df.iloc[85,1:] = ['9 Jones Street', '9 Jones St. New York']
        df.iloc[111,1:] = ['C3', '103 Waverly Pl. near Washington Sq. New York']
        df.iloc[180,1:] = ['Global 33', '93 2nd Ave.  between 5th and 6th Sts. New York']
        df.iloc[309,1:] = ['Tavern on the Green','Central Park at 67th St. New York',]
        df.iloc[396,1:] = ['Toulouse B', 'Peachtree Rd. Atlanta']
        df.iloc[435,1:] = ['2223', '2223 Market St. San Francisco']
        df.iloc[461,1:] = ['Garden Court', 'Market and New Montgomery Sts. San Francisco'] 
        df.iloc[462,1:] = ["Gaylord's", 'Ghirardelli Sq. San Francisco'] 
        df.iloc[491,1:] = ["McCormick & Kuleto's", 'Ghirardelli Sq. San Francisco'] 
    
    #second extraction - splits remainder of original string at the point of
    #the last occurence of element in street_suffixes list
    address_city_pat = "^(.*("+'|'.join(street_suffixes)+r"))(.*)$"    
    second_split = df['address_city'].str.extract(address_city_pat, expand=True)

    del second_split[1]
    del df['address_city']
    df = pd.concat([df, second_split], axis=1)
    df.columns = ['original_string', 'restaurant_name', 'address', 'city']

    if file_name == 'zagat.txt':
        df.iloc[150,1:] = ['Oyster Bar','lower level' , 'New York City',]
        df.iloc[176,1:] = ['Tavern on the Green','Central Park West' , 'New York City',]
        df.iloc[224,2:] = ['2911 S. Pharr Court', 'Atlanta']

    elif file_name == 'fodors.txt':
        df.iloc[27,2:] = ['134 N. La Cienega', 'Los Angeles']
        df.iloc[126,2:] = ['385 Broome St. at Mulberry', 'New York']
        df.iloc[281,2:] = ['126 E. 7th St. between 1st Ave. and Ave. A', 'New York']
        df.iloc[345,2:] = ['3393 Peachtree Rd. Lenox Square Mall near Neiman Marcus', 'Atlanta']
        df.iloc[356,1:] = ["Dante's Down the Hatch", 'Underground Mall', 'Atlanta']
        df.iloc[371,1:] = ["La Grotta at Ravinia Dunwoody Rd.", 'Holiday Inn/Crowne Plaza at Ravinia Dunwoody', 'Atlanta']
        df.iloc[373, 3] = 'Atlanta' 
        df.iloc[372,1:] = ['Little Szechuan', 'C Buford Hwy. Northwoods Plaza Doraville', 'Atlanta']
        df.iloc[378,1:] = ['Mi Spia', 'Dunwoody Rd. Park Place across from Perimeter Mall Dunwoody', 'Atlanta']
        df.iloc[392,2:] = ['3384 Shallowford Rd. Chamblee', 'Atlanta']
        df.iloc[398,2:] = ['3700 W. Flamingo', 'Las Vegas']
        df.iloc[454,2:] = ['804 Northpoint', 'San Francisco']
        df.iloc[464,1:] = ['Greens Bldg.', 'A Fort Mason', 'San Francisco']
        df.iloc[512,2:] = ['108 South Park', 'San Francisco']
        df.iloc[513,1:] = ["Splendido", 'Embarcadero 4', 'San Francisco'] 

    #cleaning the data
    #removing the word Restaurant from name if it starts or ends with it
    df['restaurant_name'] = df['restaurant_name'].replace(to_replace = r'^Restaurant',
                                value='', regex=True).str.strip()
    df['restaurant_name'] = df['restaurant_name'].replace(to_replace = r'Restaurant$', 
                                value='', regex=True).str.strip()
    #removing all occurences of word Caf&eacute; or Caff&egrave from name 
    df['restaurant_name'] = df['restaurant_name'].replace(to_replace = r'Caf&eacute;|Caff&egrave;', 
                                value='', regex=True).str.strip()
    #cleaning city data such that 'NE Atlanta' is changed to 'Atlanta', etc.
    df.loc[df['city'].str.contains('Atlanta', case=False), 'city'] = 'Atlanta'
    df.loc[df['city'].str.contains('New York', case=False), 'city'] = 'New York'
    df.loc[df['city'].str.contains('LA', case=False), 'city'] = 'Los Angeles'
    return df


def create_matches_df(zagat, fodors, pairs_file):
    '''
    Read in the known_pairs text file and generate a dataframe of 
    known matches. The dataframe contains four 
    columns: zagat original string, zagat index, fodors original string, 
    and fodors index. The indexes are foreign keys that reference the 
    original dataframe.

    Inputs:
        zagat: the zagat dataframe created by the auxillary 
               create_df() function
        fodors: the fodors dataframe created by the auxillary
               create_df() function
        pairs_file: the known_pairs.txt file
    Output:
        matches: the matches dataframe with each row containing known matches
    '''
    with open(pairs_file, "r") as f:
        array = []
        for line in f:
            array.append(line.strip('\n').strip('#').strip()) 
        array = [x for x in array if x != '']

        # the first two lines of the file need to be removed,
        # due to the header of the txt file 
        array = array[2:]

        for idx, text in enumerate(array):          
            if text == "CDaniel 20 E. 76th St. New York City":
                array[idx] = "Daniel 20 E. 76th St. New York City"
                continue
            if text == "Caf&eacute;  Ritz-Carlton  Buckhead,3434 Peachtree":
                array[idx] = "Caf&eacute;  Ritz-Carlton  Buckhead 3434 Peachtree Rd. Atlanta"
                continue        
            if text == "Rd. Atlanta Georgia":
                array[idx] = ''
                continue         
            # short lines in the txt file should be part of the previous line
            elif (len(text) < 25) or (text == 'Square Shopping Center Atlanta'):
                array[idx-1] += ' ' + text
                array[idx] = ''
                continue
            
        array = [x for x in array if x != '']

    # every even-indexed element in the array is a string belonging to zagat
    # every odd-indexed element in the array is a string belonging to fodors
    zag = array[0::2]
    fod = array[1::2]

    zag_index = get_index_column(zag, zagat)
    fod_index = get_index_column(fod, fodors)

    match_dict = {'zagat': zag, 'zag_index': zag_index, 
                'fodors': fod, 'fod_index': fod_index}
    matches = pd.DataFrame(match_dict, 
                columns = ['zagat', 'zag_index', 'fodors', 'fod_index'])

    return matches

def get_index_column(original_string_list, restaurant_df):
    '''
    Inputs  
        original_string_list: full string list of restaurants whose index in 
                              zagat.fodors dataframes need to be obtained
        restaurant_df: either of the zagat/fodors dataframes
    Returns:
         index_column: a panda series with index values for corresponging 
                       restaurants 
    '''

    index_column = pd.Series()
    for idx, restaurant in enumerate(original_string_list):
        index_value = restaurant_df[restaurant_df['original_string'] == restaurant].index.tolist()
        index_column = index_column.append(pd.Series(index_value[0], index = [idx]))
    return index_column


def create_unmatches_df(zagat, fodors):
    '''
    Randomly samples from the zagat and fodors dataframes and 
        generates a dataframe of unmatches.
    The unmatches dataframe contains four columns: zagat original string,
    zagat index, fodors original string, and fodors index. The indexes are
    foreign keys that reference the original dataframe.

    Inputs:
        zagat: the zagat dataframe created by the auxillary create_df() function
        fodors: the fodors dataframe created by the auxillary create_df() function
    Output:
        unmatches: the unmatches dataframe with each row containing 
            a random pair from zagat and fodors
    '''
    zag = zagat.sample(1000, replace = True)['original_string'].tolist() 
    fod = fodors.sample(1000, replace = True)['original_string'].tolist() 
    zag_index = get_index_column(zag, zagat)
    fod_index = get_index_column(fod, fodors)
    
    unmatch_dict = {'zagat': zag, 'zag_index': zag_index, 
                    'fodors': fod, 'fod_index': fod_index}
    unmatches = pd.DataFrame(unmatch_dict, 
                columns = ['zagat', 'zag_index', 'fodors', 'fod_index'])

    return unmatches

def score_vectors(df, zagat, fodors):
    '''
    Given a match or unmatch dataframe, generates a score_vector and returns
    two vectors: the score_vector and the score_vector_cat

    Inputs:
        df: a dataframe, either matches or unmatches
        zagat: the zagat dataframe
        fodors: the fodors dataframe

    Outputs:
        score_vector: a list of triples, (restaurant_name, address, city),
            where each value of the triple takes on a value between 0 and 1
        score_vector_cat: a list of triples, (restaurant_name, address, city),
            where each value of the triple takes on a category value 0,1, or 2. 
    '''
    score_vector = [] 
    score_vector_cat = []
    zag_key = df['zag_index'].tolist()
    fod_key = df['fod_index'].tolist()
    # zip the zagat and fodors pairs to score each row
    tup_key = zip(zag_key, fod_key) 

    # compare the names, addresses, and cities of each 
    # row to generate the triple of scores
    for zag_key, fod_key in tup_key:

        zag_name = zagat.at[zag_key, 'restaurant_name'].strip()
        fod_name = fodors.at[fod_key, 'restaurant_name'].strip()
        jelly_name = jellyfish.jaro_winkler(zag_name, fod_name)
        jw_name = util.get_jw_category(jelly_name)
        
        zag_address = zagat.at[zag_key, 'address'].strip()
        fod_address = fodors.at[fod_key, 'address'].strip()
        jelly_address = jellyfish.jaro_winkler(zag_address, fod_address)
        jw_address = util.get_jw_category(jelly_address)

        zag_city = zagat.at[zag_key, 'city'].strip()
        fod_city = fodors.at[fod_key, 'city'].strip()
        jelly_city = jellyfish.jaro_winkler(zag_city, fod_city)
        jw_city = util.get_jw_category(jelly_city)

        score_vector.append((jelly_name, jelly_address, jelly_city))
        score_vector_cat.append((jw_name, jw_address, jw_city))

    return score_vector, score_vector_cat
    

def histogram(matches, unmatches, zagat, fodors):
    '''
    Generates histograms of the jw scores for matches and unmatches 
    correspondingly and writes the histograms to a pdf file

    Inputs:
        matches: the matches dataframe
        unmatches: the unmatches dataframe
        zagat: the zagat dataframe
        fodors: the fodors dataframe
    Output:
        writes the histograms to a pdf file 
    '''

    m_score_vector = score_vectors(matches, zagat, fodors)[0]  
    m_rest_name_vector = [i[0] for i in m_score_vector]
    m_address_vector = [i[1] for i in m_score_vector]
    m_city_vector = [i[2] for i in m_score_vector]

    u_score_vector = score_vectors(unmatches, zagat, fodors)[0] 
    u_rest_name_vector = [i[0] for i in u_score_vector]
    u_address_vector = [i[1] for i in u_score_vector]
    u_city_vector = [i[2] for i in u_score_vector]

    # Drop the plot if it exists
    plt.clf()

    # Create plots
    # Names
    plt.subplot(321)
    plt.hist(m_rest_name_vector)
    plt.title("Names from Matches", fontsize = 12)
    plt.xlabel("Jaro-Winkler Score", fontsize = 8)
    plt.ylabel("Frequency", fontsize = 8)

    plt.subplot(322)
    plt.hist(u_rest_name_vector)
    plt.title("Names from Unmatches", fontsize = 12)
    plt.xlabel("Jaro-Winkler Score", fontsize = 8)
    plt.ylabel("Frequency", fontsize = 8)

    # City 
    plt.subplot(323)
    plt.hist(m_city_vector)
    plt.title("Cities from Matches", fontsize = 12)
    plt.xlabel("Jaro-Winkler Score", fontsize = 8)
    plt.ylabel("Frequency", fontsize = 8)

    plt.subplot(324)
    plt.hist(u_city_vector)
    plt.title("Cities from Unmatches", fontsize = 12)
    plt.xlabel("Jaro-Winkler Score", fontsize = 8)
    plt.ylabel("Frequency", fontsize = 8)

    # Addresses 
    plt.subplot(325)
    plt.hist(m_address_vector)
    plt.title("Addresses from Matches", fontsize = 12)
    plt.xlabel("Jaro-Winkler Score", fontsize = 8)
    plt.ylabel("Frequency", fontsize = 8)

    plt.subplot(326)
    plt.hist(u_address_vector)
    plt.title("Addresses from Unmatches", fontsize = 12)
    plt.xlabel("Jaro-Winkler Score", fontsize = 8)
    plt.ylabel("Frequency", fontsize = 8)

    plt.tight_layout()
    plt.savefig('histograms.pdf')

def calc_relative_freq(score_vector_cat):

    '''
    Given a list of score vectors, will compute relative frequencies 
    of each type of vector.

    Inputs:
        score_vector_cat: a list of cateogorical score triples

    Output:
        vector_dic: a dictionary with key-pair values of vectors and 
        relative frequencies. Will only contain vectors with nonzero 
        relative frequency.
    '''

    vector_dic = {} 
    denom = len(score_vector_cat)
    for vector in score_vector_cat:
        vector_dic[vector] = vector_dic.get(vector, 0) + (1/denom)

    return vector_dic

all_vectors = [(1,1,1), (1,1,2), (1,1,0), (2,1,1), (2,1,2), (2,1,0), (0,1,1), (0,1,2), (0,1,0),
(1,2,1), (1,2,2), (1,2,0), (2,2,1), (2,2,2), (2,2,0), (0,2,1), (0,2,2), (0,2,0), 
(1,0,1), (1,0,2), (1,0,0), (2,0,1), (2,0,2), (2,0,0), (0,0,1), (0,0,2), (0,0,0)]

def partition_vectors(m_vector_dict, u_vector_dict, mu, lambda_): 
    '''
    Given dictionaries of nonzero relative frequencies for vectors from the
    match and unmatch dataframe, partitions the 27 possible vectors into 
    three sets: match_vectors, possible_vectors, unmatch_vectors

    Inputs:
        m_vector_dict: a dictionary generated from the matches dataframe with
                       key-pair values of vectors and relative frequencies. 
        u_vector_dict: a dictionary generated from the unmatches dataframe with
                       key-pair values of vectors and relative frequencies.
                     Will only contain vectors with nonzero relative frequency.
        mu: maximum false positive late threshold
        lambda_: maximum false negative rate threshold

    Outputs:
        match_vectors: a set of triples, the vectors that will indicate a match
        unmatch_vectors: a set of triples, the vectors that will indicate an unmatch
        possible_vectors: a set of triples, the vectors that will indicate a possible match
    '''
    
    match_vectors = set()
    possible_vectors = set()
    unmatch_vectors = set()
    mu_moving = 0
    lambda_moving = 0

    ordered_vectors = [] # will be a list of tuples (vector, m(w)/u(w))

    # loop through the 27 possible vectors 
    for vector in all_vectors:

        if (vector not in m_vector_dict) and (vector not in u_vector_dict):
            possible_vectors.add(vector)

        # if the vector is only in a single dictionary but not the other, 
        # then the vector is added to the appropriate set and the error rates are 
        # not incremented.
        elif (vector not in m_vector_dict) and (vector in u_vector_dict):
            unmatch_vectors.add(vector)

        elif (vector in m_vector_dict) and (vector not in u_vector_dict):
            match_vectors.add(vector)

        # if the vector appears in both dictionaries, then they are added to
        # ordered_vectors and sorted in decreasing order of m(w)/u(w)

        elif (vector in m_vector_dict) and (vector in u_vector_dict):
            ordered_vectors.append((vector, m_vector_dict[vector] / u_vector_dict[vector]))

    ordered_vectors = sorted(ordered_vectors, key=lambda x: x[1], reverse = True)    

    # loop through ordered_vectors twice, once from the front and once in reverse
    # note our algorithm maximizes matches. 

    for vector, ratio in ordered_vectors:
        if mu_moving <= mu:
            match_vectors.add(vector)
            mu_moving += u_vector_dict[vector]

    for vector, ratio in reversed(ordered_vectors):        
        if (lambda_moving <= lambda_) and (vector not in match_vectors):
            unmatch_vectors.add(vector)
            lambda_moving += m_vector_dict[vector]

    for vector, ratio in ordered_vectors:
        if (vector in ordered_vectors) and (vector not in match_vectors) and (vector not in unmatch_vectors):
            possible_vectors.add(vector)

    assert(len(match_vectors) + len(possible_vectors) + len(unmatch_vectors) == 27)

    return match_vectors, unmatch_vectors, possible_vectors


def count_matches(zagat, fodors, match_vectors, unmatch_vectors, outfile, block_on):
    '''
    Go through every pair in the zagat and fodors dataframes and determine 
    counts of matches, unmatches, and possible matches. Outputs the matches
    to a csv file 'outfile'

    Inputs:
        zagat: the zagat dataframe
        fodors: the fodors dataframe
        match_vectors: the set of match vectors
        unmatch_vectors: the set of unmatch vectors
        outfile: string with name of output csv file for matches
        block_on: a string, either 'restaurant_name', city', 'address'

    Outputs:
        match_count: an int, the number of matches
        unmatch_count: an int, the number of unmatches
        possible_match_count: an int, the number of possible matches
    '''


    match_count = 0
    unmatch_count = 0
    possible_match_count = 0
    matches_for_csv = pd.DataFrame(columns=['orignal_zagat_string','orignal_fodors_string'])

    for z_ind, zrow in zagat.iterrows():
        for f_ind, frow in fodors.iterrows():

            zrow_name, zrow_address, zrow_city = zrow[1].strip().lower(), zrow[2].strip().lower(), zrow[3].strip().lower()
            frow_name, frow_address, frow_city = frow[1].strip().lower(), frow[2].strip().lower(), frow[3].strip().lower()

            # check blocking conditions. score the pair if the condition is met
            if block_on == 'restaurant_name':
                if zrow_name != frow_name:
                    continue
            if block_on == 'city':
                if zrow_city != frow_city:
                    continue
            if block_on == 'address':
                if zrow_address != frow_address:
                    continue

            score_name = jellyfish.jaro_winkler(zrow_name, frow_name)
            jw_name = util.get_jw_category(score_name)

            score_address = jellyfish.jaro_winkler(zrow_address, frow_address)
            jw_address = util.get_jw_category(score_address)

            score_city = jellyfish.jaro_winkler(zrow_city, frow_city)
            jw_city = util.get_jw_category(score_city)

            score_vector_cat = (jw_name, jw_address, jw_city)

            if score_vector_cat in match_vectors:
                match_count += 1
                match_row = {'orignal_zagat_string': zrow[0].strip(), 'orignal_fodors_string': frow[0].strip()}
                matches_for_csv = matches_for_csv.append(match_row, ignore_index=True)

            elif score_vector_cat in unmatch_vectors:
                unmatch_count += 1

            else: 
                possible_match_count += 1
    
    matches_for_csv.to_csv(outfile)
    return match_count, possible_match_count, unmatch_count



if __name__ == '__main__':

    num_m, num_p, num_u = find_matches(0.005, 0.005, './matches.csv', 
                                       block_on=None)

    print('Found {} matches, {} possible matches, and {} ' 
              'unmatches with no blocking.'.format(num_m, num_p, num_u))


