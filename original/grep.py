"""COMP0015 grep - a simple search engine
   Author: Ahmad Eblagh
   An automated testing algorithm for this source code can be found in this folder in the file titled "test_grep.py"
"""

import os, string

def common_elements(lis1, lis2):
    """Find the common elements in two lists.

    Args:
        lis1 (list): one of the lists to compare
        lis2 (list): the other list to compare

    Returns:
        list : contains the elements common to both lists.
    """
    lis1_set = set(lis1) #Converting the list into a set to eliminate duplicates
    lis2_set = set(lis2) #Converting the list into a set to eliminate duplicates
    common = lis1_set.intersection(lis2_set) #Finding the union of the two sets
    
    return list(common) #Returning the intersection and converting back to a list


def clean_words(words_list):
    """
    Cleanses the words by removing punctuations,
     and converting to lower case letters

    Args:
        words_list: A list of all the words in a given textfile

    Returns:
        list: returns a cleaned version of the input list

    """
    clean_words = set() #An empty set to be filled 
    for word in words_list: #Filters the list removing punctions and uncapitalizing capital letters
        clean_word = word.strip(string.punctuation).lower()
        if clean_word:
            clean_words.add(clean_word)

    return list(clean_words)


def build_index(file_list, index, title_index):
    """Build a word index and a title index for all the files in a file list.

    Args:
        file_list (list): List containing file names
        index (dictionary): Index mapping words to filenames
        title_index (dictionary): Index mapping filenames to the title of the article.
    """
    for file_name in file_list:
        title, content = get_content(file_name)
        #print(title)
        #print(content)

        all_content = title + content #Collecting all the words in the given file 

        words_list = all_content.split() #Converting the string into a list 

        words_list = clean_words(words_list) # Calling on the clean_words function to cleans the words in the list

        for word in words_list: #Filling in the index, mapping words to corresponding files
            if word not in index:
                index[word] = []
            index[word].append(file_name)
        title_index[file_name] = title


def get_content(file_name):
    """Return the title and contents of the file.

    Args:
        file_name (str): String containing file name

    Returns:
        title (str): String containing the file title
        content (str): String containing the remaining words in the file
    """    
    with open(file_name) as file:
        title = file.readline().strip() # get the title
        contents = file.read()          # read the rest
        return title, contents


def search(index, query):
    """Search the index for the words in the query string.

    Args:
        index (dictionary): dictionary containing word to filename mapping.
        query (string): string containing words in the query. String is lowercase.

    Returns:
        list: list of file in which all the words in the query appear.
    """
    query_list = query.split() #Convert the input string into a list of query words
    query_words = clean_words(query_list) #Calling upon the clean_words function to cleanse the query words

    if (len(query_words) == 0) or (query_words[0] not in index): #Return an empty list if no query word is inputed or if the query word cannot be found
        return []
    
    last_file_list = index[query_words[0]] #Storying the first query word 
   
    for i in range(1, len(query_words)): #Searching for the query word in the index 
        if query_words[i] in index:
            current_file_list = index[query_words[i]]
        else:
            return []
        common = common_elements(current_file_list, last_file_list)
        last_file_list = common
    
    return last_file_list


def pretty_print(index, title_index):
    """Print the dictionaries passed as parameters

    Args:
        index (dictionary): Index mapping words to filenames
        title_index (dictionary): Index mapping filenames to the title of the article.
    """    
    print("\nIndex:")
    print(index)
    print("\nFile names and titles:")
    print(title_index)


def get_filenames(directory_name):
    """Return list of the files in the given directory.

    Args:
        directory_name (directory): Name of the directory

    Returns:
        list: list of filenames in the directory
    """    
    file_list = []

    for filename in os.listdir(directory_name):
        if filename.endswith('.txt'):
            file_list.append(os.path.join(directory_name, filename))

    return file_list


def menu(index, titles):
    """Menu for the application

    Args:
        index (dictionary): Index mapping words to filenames
        title_index (dictionary): Index mapping filenames to the title of the article.
    """    
    print('='*17 + "Greetings" + '='*17)
    print("Welcome to a state-of-the-art search engine")
    search_query = input("Enter a search query, (empty to finish): ")    

    while search_query != '':
        filename_list = search(index, search_query)
        print("Results: ", search_query)
        if len(filename_list) == 0:
            print("No results")
        else:
            for file in filename_list:
                title = titles[file]
                print("File: ", file, "Title: ", title)
        search_query = input('Enter a search query, (empty to finish): ')


def main():

    # Test 1: test common_elements
    # print(common_elements(['a', 'b', 'c'], ['a', 'p', 'c']))
    # print(common_elements(['a', 'b', 'c'],['x', 'y', 'z']))
    # print(common_elements(['a', 'b', 'a'],['a', 'a', 'a']))  

    # Test 2: test with small files
    # index = {}
    # titles = {}
    # build_index(['sentimental_1.txt', 'sentimental_2.txt', 'sentimental_3.txt'], index, titles)
    # pretty_print(index, titles)

    # Test 3: test with bbc sport news files
    # index = {}
    # titles = {}    
    # build_index(get_filenames('bbc_football'), index, titles)
    # pretty_print(index, titles)
 

    # Test 4: test with small files
    # index = {}
    # titles = {}
    # build_index(['sentimental_1.txt', 'sentimental_2.txt', 'sentimental_3.txt'], index, titles)
    # print(index)
    # print("\nsentimental: ", search(index, 'sentimental'))
    # print("\ncoltrane: ", search(index, 'coltrane'))
    # print('\nellington: ', search(index, 'ellington'))
    # print('\nsentimental journey: ', search(index, 'sentimental journey'))
    # print('\nnot_in_files', search(index, 'not_in_files'))
    # print('\nlong journey ', search(index, 'long journey'))

    # Test 5:test all
    index = {}
    titles = {} 
    build_index(get_filenames('bbc_football'), index, titles)
    menu(index, titles)
    



if __name__ == '__main__':
    main()
