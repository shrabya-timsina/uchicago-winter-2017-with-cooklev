# CS122: Auto-completing keyboard
# Sample solution: using lists in place of tries
#
# Matthew Wachs
# Autumn 2014
#
# Revised: August 2015, AMR
#
# usage: python trie_list.py <dictionary filename>


import os
import sys
import tty
import termios
import fcntl
import string

import trie_shell

def create_trie_node():
    return []

def add_word(w, t):
    t.append(w)

def is_word(w, t):
    return w in t

def num_completions(p, t):
    # IMPORTANT: When you write the trie-based
    # version of this function, do NOT compute
    # the number of completions simply as
    #
    #    len(get_completions(p, t))
    #
    # See PA writeup for more details.
    return len(get_completions(p, t))

def get_completions(p, t):
    return [w[len(p):] for w in t if w.startswith(p)]

if __name__ == "__main__":
    trie_shell.go("trie_list")
