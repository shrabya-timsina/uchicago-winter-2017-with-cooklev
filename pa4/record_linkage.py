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

    return (0, 0, 0)
  
    
if __name__ == '__main__':

    num_m, num_p, num_u = find_matches(0.005, 0.005, './matches.csv', 
                                       block_on=None)

    print("Found {} matches, {} possible matches, and {} " 
              "unmatches with no blocking.".format(num_m, num_p, num_u))
