# CS122: Auto-completing keyboard
# User interface implementation
#
# Matthew Wachs
# Autumn 2014
#
# Revised: August 2015, AMR
#


########################################
###                                  ###
###   DO NOT MODIFY THIS FILE        ###
###                                  ###
########################################

import os
import sys
import tty
import termios
import fcntl
import string
import importlib

trie = None

def load_trie_module(name):
    global trie
    trie = importlib.import_module(name)

def read_words(wordfile, t):
  '''
  Load the words from the specified dictionary file
  into the trie.
  '''
  for w in open(wordfile).readlines():
    trie.add_word(w.strip(), t)

def getch():
  '''
  Get a character from stdin
  '''
  fd = sys.stdin.fileno()

  oldterm = termios.tcgetattr(fd)
  newattr = termios.tcgetattr(fd)
  newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
  termios.tcsetattr(fd, termios.TCSANOW, newattr)

  oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

  try:        
    while True:            
      try:
        c = sys.stdin.read(1)
        if c != "":
          break
      except IOError: pass


  finally:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
  return c

nearby_dict = {"q":["w", "a"],
  "w":["q", "e", "s"],
  "e":["w", "r", "d"],
  "r":["e", "t", "f"],
  "t":["r", "y", "g"],
  "y":["t", "u", "h"],
  "u":["y", "i", "j"],
  "i":["u", "o", "k"],
  "o":["i", "p", "l"],
  "p":["o"],
  "a":["q", "s", "z"],
  "s":["w", "a", "d", "z", "x"],
  "d":["e", "s", "f", "x", "c"],
  "f":["r", "d", "g", "c", "v"],
  "g":["t", "f", "h", "v", "b"],
  "h":["y", "g", "j", "b", "n"],
  "j":["u", "h", "k", "n", "m"],
  "k":["i", "j", "l", "m"],
  "l":["o", "k"],
  "z":["s", "x"],
  "x":["z", "s", "d", "c"],
  "c":["x", "v", "f"],
  "v":["c", "b", "f", "g"],
  "b":["v", "n", "g", "h"],
  "n":["b", "m", "h", "j"],
  "m":["n", "j", "k"]}

def nearby_keys(c):
  '''
  Return a list of the letters near c on the keyboard
  '''
  rv = nearby_dict.get(c, [])
  rv = rv[:]
  return rv

def misspelled_prompt(message, t, word):
    print("\nThere are no words that start with '%s'" % word)
    prompt(message, word)

def prompt(message, word):
  '''
  Write the shell's prompt to stdout
  '''
  if len(message) == 0:
    pre = ""
  else:
    pre = "|%s| " % message
  sys.stdout.write(pre + "> " + word)
  sys.stdout.flush()

def process_completions(t, message, word, print_candidates):
  '''
  Process the current "word" and generate a new message and prompt,
  information about possible completions, an error message, or
  information about possible corrections to the word.
  '''
  n = trie.num_completions(word, t)
  misspelled = False

  if n == 0:
    # If there are no possible completions, this is a misspelled
    # word. We want nothing to do with it.
    
    misspelled = True
    misspelled_prompt(message, t, word)
  elif n == 1:
    # If there is only one possible completion, go ahead and add
    # the word to the message.
    word += trie.get_completions(word, t)[0]
    if len(message) > 0:
      message += " "
    message += word
    word =""
    print()
    prompt(message, word)
  else:
    if print_candidates:
      if n > 10:
        print("\n(" + str(n) + " completions)")
      else:
        print()
        for com in trie.get_completions(word, t):
          print(word + com)
      prompt(message, word)

  return message, word, misspelled

def shell(t):
  '''
  Gather characters from stdin and handle requests for auto
  completion, reset, etc.

  Type Control-C to get out of this shell.
  '''
  message = ""
  word = ""
  misspelled = False
  prompt(message, word)
  while True:
    # Get a character
    c = getch()

    # Control-D resets the message
    if ord(c) == 4:
      message = ""
      word = ""
      misspelled = False
      print()
      prompt(message, word)
      continue

    # Possible end of word
    if (c == " ") or (c == "\n"):
      if misspelled:
        misspelled_prompt(message, t, word)
      else:
        if not trie.is_word(word, t):
          print("\nWord '%s' does not exist" % word)
          prompt(message, word)
        else:
          if len(message) > 0:
            message += " "
          message += word
          word = ""
          print()
          prompt(message, word)

      continue

    # Autocomplete    
    if c == "\t":
      if word != "":
        message, word, misspelled = process_completions(t, message, word, print_candidates = True)        
      continue

    # Backspace
    if ord(c) == 127:
      if len(word) == 0:
        print("cannot change previous word once accepted")
        continue
      word = word[:len(word)-1]
      sys.stdout.write('\r')
      sys.stdout.flush()
      prompt(message, word + " ")
      sys.stdout.write('\b')
      sys.stdout.flush()
    else:
        # If the character is not a letter, we're not interested
        # in it.
        if c not in string.ascii_letters:
          continue

        # Update prompt and letter
        sys.stdout.write(c)
        sys.stdout.flush()
        word = word + c

    message, word, misspelled = process_completions(t, message, word, print_candidates = False)


def go(module_name):
  '''
  Process the arguments and fire up the shell.
  '''

  if(len(sys.argv) != 2):
    print("Usage: python trie.py WORD_FILE")
    sys.exit(1)

  wordfile = sys.argv[1]

  if not os.path.exists(wordfile):
    print("Error: %s does not exist")
    sys.exit(1)

  load_trie_module(module_name)

  print("Loading words into trie...",)
  sys.stdout.flush()
  t = trie.create_trie_node()
  if t == None:
    print("None is not a valid return value for create_trie")
    print()
    sys.exit(0)

  read_words(wordfile, t)
  print(" done")
  print()
  print("===================================================")
  print("      Welcome to the auto-completing shell!")
  print()
  print(" Start typing a word and press Tab to autocomplete")
  print()
  print("      Press Control-D to reset the message")
  print("             Press Control-C to exit")
  print("===================================================")
  print()

  try:
    shell(t)
  except KeyboardInterrupt as ki:
    print()
    sys.exit(0)

if __name__ == "__main__":
  go()

