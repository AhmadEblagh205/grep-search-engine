import unittest
import grep

"""
Utilizing the TestCase class to examine and evaluate test scenarios for grep.
"""
#Creating an index dictionary for testing
index_test = {"Ahmad":"text.001","Ridwan":"text.005","Lol":"text.002"}

class Testgrep (unittest.TestCase):
    #Testing to see if the common_elements function returns the correct output for a given input of lists   
    def testing_fuctionality_of_common_elements(self):
        self.assertEqual(grep.common_elements([2,3,4],[2,5,6]), [2])
        self.assertEqual(grep.common_elements([1,10,5],[1,10,-5]), [1,10])
        self.assertEqual(grep.common_elements([0,1,15],[0,1,15]), [0,1,15])
    #Testing to see if the common_elements function's output is of the right data type
    def test_type_common_elements(self):
        self.assertEqual(type((grep.common_elements([0,0,0],[3,5,6]))), list)
        self.assertEqual(type((grep.common_elements([2,3,4],[2,5,6]))), list)
        self.assertEqual(type((grep.common_elements([5,35,-10],[-10,5,6]))), list)
    #Testiing to see if the clean_words() function works as intended 
    def test_functionality_clean_words(self):
        self.assertEqual(grep.clean_words(["_Ahmad?"]),["ahmad"])
        self.assertEqual(grep.clean_words(["....RIDWAN?!!!"]),["ridwan"])
        self.assertEqual(grep.clean_words(["()....AMIR"]),["amir"])
        self.assertEqual(grep.clean_words(["..,.,.,IBti"]),["ibti"])
        self.assertEqual(grep.clean_words([">>>>LIFE?!!"]),["life"])
    
    #Testing to see if the clean_word() function's output is of the right data type
    def test_type_clean_words(self):
        self.assertEqual(type(grep.clean_words(["_Ahmad?"])),list)
        self.assertEqual(type(grep.clean_words(["....RIDWAN?!!!"])),list)
        self.assertEqual(type(grep.clean_words([">>>>LIFE?!!"])),list)
    
    #Testing to see if the search() function's output is of the right data type
    def test_search_type(self):
        self.assertEqual(type(grep.search(index_test,"Ahmad")),list)
        self.assertEqual(type(grep.search(index_test,"Ridwan")),list)
        self.assertEqual(type(grep.search(index_test,"Lol")),list)

        

if __name__ == '__main__':
    unittest.main()
