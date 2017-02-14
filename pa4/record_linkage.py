# CS122: Linking restaurant records in Zagat and Fodor's list
#Names: Shrabya Timsina and Steven Cooklev


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import jellyfish
import util
import re

#identify suffix first from left
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


    return (0, 0, 0)
  

def create_df(file_name):
    df = pd.read_fwf(file_name, header = None)[0]
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
    #return df





    
if __name__ == '__main__':

    num_m, num_p, num_u = find_matches(0.005, 0.005, './matches.csv', 
                                       block_on=None)

    print('Found {} matches, {} possible matches, and {} ' 
              'unmatches with no blocking.'.format(num_m, num_p, num_u))
