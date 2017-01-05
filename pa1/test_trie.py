# CS122: Auto-completing keyboard using Tries
#
# Tests for your trie implementation
#
# YOUR NAME HERE

from trie_dict import create_trie_node, add_word, is_word, num_completions, get_completions

t = create_trie_node()
add_word("a", t)
add_word("an", t) 
add_word("and", t)
add_word("are", t) 
add_word("bee", t)

# Write your tests here

# Example of an assertion. If "bee" was not inserted
# correctly in the trie, the following statement will
# cause the program to exit with an error message.
assert is_word("bee", t)
