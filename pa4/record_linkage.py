# CS122: Linking restaurant records in Zagat and Fodor's list
#Names: Shrabya Timsina and Steven Cooklev


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import jellyfish
import util
import re

#identify the first suffix
street_suffixes = ['Blvd.','St.','Ave.','Dr.','Rd.','Pkwy.','Sq.','Hwy.','Ln.','Pl.']

##fail the first split:
#zagat: Oyster Bar lower level New York City, 21 Club 21 W. 52nd St. New York City
#Tavern on the Green Central Park West New York City, 
#Martha's 22nd Street Grill 25 22nd St. Hermosa Beach

#fodors: Gladstone's 4 Fish 17300 Pacific Coast Hwy. at Sunset Blvd. Pacific Palisades
#21 Club 21 W. 52nd St. New York, 
#20 Mott 20 Mott St.  between Bowery and Pell St. New York
#9 Jones Street 9 Jones St. New York, 
#Dante's Down the Hatch  Underground Underground Mall  Underground Atlanta Atl
#La Grotta at Ravinia Dunwoody Rd.  Holiday Inn/Crowne Plaza at Ravinia  Dunwo
#Little Szechuan C Buford Hwy.  Northwoods Plaza  Doraville Atlanta
#Mi Spia Dunwoody Rd.  Park Place  across from Perimeter Mall  Dunwoody Atlant
#Toulouse B Peachtree Rd. Atlanta
#2223 2223 Market St. San Francisco
#Garden Court Market and New Montgomery Sts. San Francisco
#Gaylord's Ghirardelli Sq. San Francisco
#Greens Bldg. A Fort Mason San Francisco
#McCormick & Kuleto's Ghirardelli Sq. San Francisco
#Splendido Embarcadero 4 San Francisco - rest_name is Slendido, add is embarcadero 4



def find_matches(mu, lambda_, outfile='./matches.csv', block_on=None):
    
    #zagat_file = './zagat.txt'
    #fodor_file = './fodor.txt'
    #pairs_file = './known_pairs.txt'

    #
    # ----------------- YOUR CODE HERE ------------------------
    #
    
    zagat = create_df('zagat.txt')
    fodors = create_df('fodors.txt')
    pairs_file = './known_pairs.txt'


    return (0, 0, 0)
  

def create_df(file_name):
    df = pd.read_fwf(file_name, header = None)[0].str.strip()
    first_split = df.str.extract(r'^([^\d]*)(\d.*)$', expand=True)
    df = pd.concat([df, first_split], axis=1)
    df.columns = ['original_string', 'restaurant_name', 'address_city']
    #second_split = df['address_city'].str.extract(r'(\d.*\.)(.*)$', expand=True)
    #re.search(r"(?=("+'|'.join(street_suffixes)+r"))",zz)
    address_city_pat = "^(.*("+'|'.join(street_suffixes)+r"))(.*)$"

    second_split = df['address_city'].str.extract(address_city_pat, expand=True)
    del second_split[1]
    del df['address_city']
    df = pd.concat([df, second_split], axis=1)
    df.columns = ['original_string', 'restaurant_name', 'address', 'city']
    df.to_csv(file_name + "_csv")
    return df
    # hard_code rows to the end of the df ?


def create_matches_df():
    '''
    Read in the known_pairs text file and generate a 
    '''
    zagat = create_df('zagat.txt')
    fodors = create_df('fodors.txt')
    with open('known_pairs.txt', "r") as f:
        array = []
        for line in f:
            array.append(line.strip('\n').strip('#').strip()) 
        array = [x for x in array if x != '']
        array = array[2:]
        print(array)
        for idx, text in enumerate(array):
            
            if text == "CDaniel 20 E. 76th St. New York City":
                array[idx] = "Daniel 20 E. 76th St. New York City"
                continue
            if text == "Caf&eacute;  Ritz-Carlton  Buckhead,3434 Peachtree":
                array[idx] = "Caf&eacute;  Ritz-Carlton  Buckhead 3434 Peachtree Rd. Atlanta"
                print(text)
                print("---")
                continue
            
            if text == "Rd. Atlanta Georgia":
                array[idx] = ''
                continue
            
            elif (len(text) < 25) or (text == 'Square Shopping Center Atlanta'):
            # I checked that this length corresponds to an addition meant to be on the previous line
                array[idx-1] += ' ' + text
                array[idx] = ''
                continue
            
        array = [x for x in array if x != '']
        #print(array)
    zag = array[0::2]
    #print(zag)
    #print("__________________________________________")
    fod = array[1::2]
    #print(fod)
    zag_index = get_index_column(zag, zagat)
    fod_index = get_index_column(fod, fodors)


    match_dict = {'zagat': zag, 'zag_index': zag_index, 'fodors': fod, 'fod_index': fod_index}
    matches = pd.DataFrame(match_dict, columns = ['zagat', 'zag_index', 'fodors', 'fod_index'])
    

    # add two columns, the index for each zagat and fodors
    # output it to a csv?
    return matches

def get_index_column(original_string_list, restaurant_df):
    index_column = pd.Series()
    for idx, restaurant in enumerate(original_string_list):
        index_value = restaurant_df[restaurant_df['original_string'] == restaurant].index.tolist()
        #print(index_value)
        #if index_value:
        index_column = index_column.append(pd.Series(index_value[0], index = [idx]))
        #else:
        #    index_column = index_column.append(pd.Series("NaN", index = [idx]))

    return index_column



def create_unmatches_df():
    zagat = create_df('zagat.txt')
    fodors = create_df('fodors.txt')
    zag = zagat.sample(1000, replace = True, random_state = 1234)['original_string'].tolist() # remove random_states once debugged
    fod = fodors.sample(1000, replace = True, random_state = 1234)['original_string'].tolist() 
    # sometimes fod has value NaN. why?
    # add two columns: the fodors index and the zagat index
    zag_index = get_index_column(zag, zagat)
    fod_index = get_index_column(fod, fodors)
    
   
    unmatch_dict = {'zagat': zag, 'zag_index': zag_index, 'fodors': fod, 'fod_index': fod_index}
    unmatch_df = pd.DataFrame(unmatch_dict, columns = ['zagat', 'zag_index', 'fodors', 'fod_index'])
    return unmatch_df

def score_vectors(df):
    '''
    Given a match or unmatch dataframe, generates a score_vector and returns two vectors: the jw vector
    and the jw category vector
    '''
    zagat = create_df('zagat.txt')
    fodors = create_df('fodors.txt')
    '''
    zag_name = []
    zag_address = []
    zag_city = []
    fod_name = []
    fod_address = []
    fod_city
    '''

    score_vector = [] # list of triples (restaurant_name, address, city)
    score_vector_jw = []
    zag_key = df['zag_index'].tolist()
    fod_key = df['fod_index'].tolist()
    # we then need to reference the original zagat and  fodors df to get the restaurant_name, address, city
    tup_key = zip(zag_key, fod_key)
    for zag_key, fod_key in tup_key:

        zag_name = zagat.at[zag_key, 'restaurant_name']
        fod_name = fodors.at[zag_key, 'restaurant_name']
        jelly_name = jellyfish.jaro_winkler(zag_name, fod_name)
        jw_name = util.get_jw_category(jelly_name)
        
        zag_address = zagat.at[zag_key, 'address']
        fod_address = fodors.at[zag_key, 'address']
        jelly_address = jellyfish.jaro_winkler(zag_address, fod_address)
        jw_address = util.get_jw_category(jelly_address)

        zag_city = zagat.at[zag_key, 'city']
        fod_city = fodors.at[zag_key, 'city']
        jelly_city = jellyfish.jaro_winkler(zag_city, fod_city)
        jw_city = util.get_jw_category(jelly_city)

        score_vector.append((jelly_name, jelly_address, jelly_city))
        score_vector_jw.append((jw_name, jw_address, jw_city))

    return score_vector, score_vector_jw
    

def histogram():
    '''
    Generate histograms of the jw scores from the match and unmatch dataframes 
    '''

    m_score_vector = score_vectors(match_df)[0]  # list of triples (restaurant_name, address, city)
    m_rest_name_vector = [i[0] for i in m_score_vector]
    m_address_vector = [i[1] for i in m_score_vector]
    m_city_vector = [i[2] for i in m_score_vector]

    u_score_vector = score_vectors(match_df)[0]  # list of triples (restaurant_name, address, city)
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


    # Addresses 
    plt.subplot(323)
    plt.hist(m_address_vector)
    plt.title("Addresses from Matches", fontsize = 12)
    plt.xlabel("Jaro-Winkler Score", fontsize = 8)
    plt.ylabel("Frequency", fontsize = 8)

    plt.subplot(324)
    plt.hist(u_address_vector)
    plt.title("Addresses from Unmatches", fontsize = 12)
    plt.xlabel("Jaro-Winkler Score", fontsize = 8)
    plt.ylabel("Frequency", fontsize = 8)


    # City 
    plt.subplot(325)
    plt.hist(m_city_vector)
    plt.title("Cities from Matches", fontsize = 12)
    plt.xlabel("Jaro-Winkler Score", fontsize = 8)
    plt.ylabel("Frequency", fontsize = 8)

    plt.subplot(326)
    plt.hist(u_city_vector)
    plt.title("Cities from Unmatches", fontsize = 12)
    plt.xlabel("Jaro-Winkler Score", fontsize = 8)
    plt.ylabel("Frequency", fontsize = 8)


    plt.tight_layout()
    plt.savefig('histograms.pdf')



'''
if __name__ == '__main__':

    num_m, num_p, num_u = find_matches(0.005, 0.005, './matches.csv', 
                                       block_on=None)

    print('Found {} matches, {} possible matches, and {} ' 
              'unmatches with no blocking.'.format(num_m, num_p, num_u))
'''