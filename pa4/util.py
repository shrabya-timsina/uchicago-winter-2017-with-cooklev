

def get_jw_category(j):

    categories = [0.8, 1.0]
    return sum([j >= i for i in categories])
