from flask import Flask
from flask import request, Response
from flask_restful import Api, Resource, reqparse
import pymongo


# prepare flask
app = Flask(__name__)
api = Api(app)
my_client = pymongo.MongoClient("mongodb://localhost:27017/")
my_db = my_client["my_database"]
my_col = my_db["non-lexical-words"]


# function takes in a database collection and populates that collection
def init_db(collection):
    # initial loading of db
    # clear db if there exists any data in it
    # otherwise the data will keep building up
    # this would not be how it is done in normal release code
    my_col.delete_many({})
    # pre_set_list is the words in the appendix separated by a space
    pre_set_list = ("to got is have and although or that when while a "
                    "either more much neither my that the as no nor not "
                    "at between in of without I you he she it we they "
                    "anybody one")
    # for each word in pre_set_list
    for word in pre_set_list.split(' '):
        # create dictionary entry
        my_dict = {'entry': word}
        # add dictionary to the database collection
        collection.insert_one(my_dict)


init_db(my_col)


# function is called upon a post call to url/complexity
# takes non-formated/string based post data
# returns a http response
# router for '/complexity specifically for post methods
@app.route('/complexity', methods=['POST'])
def complexity():
    # double check that it is a post call
    if request.method == 'POST':
        # extract request user_input
        user_input = request.data.decode()
        # check to see if user_input is valid
        # check if user_input has over 1000 characters
        # up to 1000 characters not including
        if len(user_input) >= 1000:
            # abort with error code 413
            return Response(status=413)
        # check if user_input has over 100 words
        # up to 100 words not including
        if len(user_input.split(' ')) >= 100:
            # abort with error code 413
            return  Response(status=413)
        try:
            argument = request.args.to_dict()['mode']
            if argument == 'verbose':
                result = calc_lexical_density_verbose(user_input)
        except:
            # calculate lexical density for returning
            result = calc_lexical_density(user_input)
        return_dict = """""{ 
"data": %s
}""""" % result
        return return_dict
    return Flask.abort(413)


def remove_non_lex(user_input):
    # load in all non lexical words from database
    database = my_col.find()
    word_list = user_input.split()
    non_lex = []
    for filler in database:
        non_lex.append(filler['entry'])
    return ' '.join([i for i in word_list if i not in non_lex])


# lex_count: input: str return: num
def lex_count(user_input):
    # calculates number of lexical words in the input string
    # call remove_non_lex*user_input to remove all non lex words
    user_input = remove_non_lex(user_input)
    words = user_input.split(' ')
    if words == [""]:
        return 0
    # lex count is the count of the remaining words
    return len(words)


# calc_lexical_density: input: str return: http response formatted str
def calc_lexical_density(user_input):
    # calculates the lexical density of the input string
    result = round(float(lex_count(user_input) / len(user_input.split(' '))), 2)
    return_dict = """{
'overall_ld': %f
}""" % result
    return return_dict


# lex_density_sentence: input: str return: list of nums
def lex_density_sentence(user_input):
    # calculates lexical density of the input text by sentence
    # splits inputs based on . into a list of the sentences
    sentences = user_input.split('. ')
    return_list = []
    for sentence in sentences:
        total = len(sentence.split(' '))
        sentence.replace('.', '')
        sentence = remove_non_lex(sentence)
        # return the len of the filtered sentence over the len of the original
        return_list.append(round(len(sentence.split())/total, 2))
    return return_list


# calc_lexical_density_verbose: input: str return: http response formatted str
def calc_lexical_density_verbose(user_input):
    # computes the verbose requirements for the http response
    # computes lexical density of input
    overall_result = round(float(lex_count(user_input) / len(user_input.split(" "))), 2)
    # computes lexical density per sentence
    sentence_result = lex_density_sentence(user_input)
    return_dict = """{
'sentence_ld' : %s,
'overall_ld': %f
}""" % (sentence_result, overall_result)
    return return_dict


# function that contains and calls unit tests
def run_unit_tests():
    # unit test for function remove_non_lex(user_input)
    test_string1 = "Kim loves going to the cinema"
    test_string2 = "a Kim to the cinema"
    test_string3 = "a to the"
    test_string4 = "Kim cats dogs hello cinema"
    answer_test_string1 = "Kim loves going cinema"
    answer_test_string2 = "Kim cinema"
    answer_test_string3 = ""
    answer_test_string4 = "Kim cats dogs hello cinema"
    assert(remove_non_lex(test_string1) == answer_test_string1)
    assert (remove_non_lex(test_string2) == answer_test_string2)
    assert (remove_non_lex(test_string3) == answer_test_string3)
    assert (remove_non_lex(test_string4) == answer_test_string4)
    # unit tests for function lex_count(user_input)
    lex_count_string1 = 4
    lex_count_string2 = 2
    lex_count_string3 = 0
    lex_count_string4 = 5
    assert (lex_count(test_string1) == lex_count_string1)
    assert (lex_count(test_string2) == lex_count_string2)
    assert (lex_count(test_string3) == lex_count_string3)
    assert (lex_count(test_string4) == lex_count_string4)
    # unit tests for the function calc_lexical_density(user_input)
    lexical_density_string1 = """{
'overall_ld': 0.670000
}"""
    lexical_density_string2 = """{
'overall_ld': 0.400000
}"""
    lexical_density_string3 = """{
'overall_ld': 0.000000
}"""
    lexical_density_string4 = """{
'overall_ld': 1.000000
}"""
    assert (calc_lexical_density(test_string1) == lexical_density_string1)
    assert (calc_lexical_density(test_string2) == lexical_density_string2)
    assert (calc_lexical_density(test_string3) == lexical_density_string3)
    assert (calc_lexical_density(test_string4) == lexical_density_string4)
    # unit tests for function lex_density_sentence(user_input)
    test_sentences = test_string1 + ". " + test_string2 + ". " + test_string3 + ". " + test_string4 + "."
    assert (lex_density_sentence(test_sentences) == [0.67, 0.40,
                                                     0.0, 1.00])
    # unit test for function calc_lexical_density_verbose(user_input)
    verbose_result = """{
'sentence_ld' : [0.67, 0.4, 0.0, 1.0],
'overall_ld': 0.630000
}"""
    assert (calc_lexical_density_verbose(test_sentences) == verbose_result)
    # unit test for function complexity() error cases
    params1 = """{ 'mode' : 'large Text largeText
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text
large Text large Text large Text large Text large Text large Text' }"""
    post_response1 = Response(status=413)
    test_app = app.test_client()
    # test compares status of the response
    # this is due to the direct comparision failing despite exact same creation
    assert(test_app.post('/complexity', data=params1).status
           == post_response1.status)
    return


run_unit_tests()
app.run(debug=True)



