# CS122: Linking restaurant records in Zagat and Fodor's list
#


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import jellyfish
import util

def find_matches(mu, lambda_, outfile='./matches.csv', block_on=None):
    
    zagat_file = './zagat.txt'
    fodor_file = './fodor.txt'
    pairs_file = './known_pairs.txt'

    #
    # ----------------- YOUR CODE HERE ------------------------
    #
    
    zagat = create_df(zagat_file)
    fodors = create_df(fodor_file)


    return (0, 0, 0)
  

def create_df(file_name):
    df = pandas.read_fwf(file_name, header = None)[0]
    first_split = df.str.extract(r'^([^\d]*)(\d.*)$', expand=True)
    df = pandas.concat([df, first_split], axis=1)
    df.columns = ['original_string', 'restaurant_name', 'address_city']
    second_split = df['address_city'].str.extract(r'(\d.*\.)(.*)$', expand=True)
    del df['address_city']
    df = pandas.concat([df, second_split], axis=1)
    df.columns = ['original_string', 'restaurant_name', 'address', 'city']
    return df






    
if __name__ == '__main__':

    num_m, num_p, num_u = find_matches(0.005, 0.005, './matches.csv', 
                                       block_on=None)

    print("Found {} matches, {} possible matches, and {} " 
              "unmatches with no blocking.".format(num_m, num_p, num_u))
