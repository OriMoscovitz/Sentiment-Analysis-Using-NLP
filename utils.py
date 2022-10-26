import os
import threading
import time
from imdb import Cinemagoer
from nltk.corpus import stopwords
from selenium import webdriver
from selenium.common import ElementNotInteractableException, NoSuchElementException, InvalidArgumentException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from predict_sentiment import get_model_utils, predict_sentiment
import string
import re

subject_pronouns = {
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "you",
    "they",
    "me",
    "us",
    "him",
    "her",
    "them",
    "mine",
    "ours",
    "his",
    "hers",
    "yours",
    "theirs",
    "my",
    "our",
    "your",
    "their",
    "myself",
    "yourself",
    "herself",
    "himself",
    "itself",
    "ourselves",
    "yourselves",
    "themselves",
    "all",
    "another",
    "any",
    "anybody",
    "anyone",
    "anything",
    "both",
    "each",
    "either",
    "everybody",
    "everyone",
    "everything",
    "few",
    "many",
    "most",
    "neither",
    "nobody",
    "none",
    "nothing",
    "one",
    "other",
    "others",
    "several",
    "some",
    "someone",
    "something",
    "such",
    "that",
    "these",
    "this",
    "those",
    "what",
    "whatever",
    "which",
    "whichever",
    "who",
    "whoever",
    "whom",
    "whomever",
    "whose",
    "as",
    "thou",
    "thee",
    "thy",
    "thine",
    "ye",
    "whereby",
    "whence",
    "where",
    "whether",
    "yon"
}


# turn a doc into clean tokens
def clean_doc(doc):
    # split into tokens by white space
    tokens = doc.split()
    tokens = [w.lower() for w in tokens]
    # prepare regex for char filtering
    re_punc = re.compile('[%s]' % re.escape(string.punctuation))
    # remove punctuation from each word
    tokens = [re_punc.sub('', w) for w in tokens]
    # remove remaining tokens that are not alphabetic
    tokens = [word for word in tokens if word.isalpha()]
    # filter out stop words
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    # filter out pronouns
    tokens = [word for word in tokens if word not in subject_pronouns]
    # filter out short tokens
    tokens = [word for word in tokens if len(word) > 1]
    return tokens


# returns url page to a certain movie by name
def get_reviews_url(movie_name):
    ia = Cinemagoer()
    movie = ia.search_movie(movie_name)
    if len(movie) != 0:
        movie_id = movie[0].getID()
        url = f"https://www.imdb.com/title/tt" + str(movie_id) + f"/reviews"
        return url
    return None


# returns browser set on a given url
def load_browser(url):
    s = Service(executable_path=GeckoDriverManager().install())
    browser = webdriver.Firefox(service=s)
    browser.get(url)
    return browser


def load_all_reviews(browser):
    load_btn = browser.find_element(By.ID, "load-more-trigger")
    # loads all reviews in the page
    while True:
        try:
            load_btn.click()
            time.sleep(2)
        except ElementNotInteractableException:
            break


# collects NONE EMPTY reviews into a list
def reviews_to_list(browser):
    reviews = []
    while True:
        try:
            review = browser.find_element(By.CLASS_NAME, "text")
            if review.text != "":
                reviews.append(review.text)
            browser.execute_script("""var review = arguments[0];""")
            browser.execute_script("arguments[0].remove();", review)
        except NoSuchElementException:
            break
    return reviews


def create_folder_for_reviews(movie_name):
    # Directory
    directory = f"review_{movie_name}"
    # Path string
    path = os.path.join(os.getcwd(), directory)
    # if path exists del dir and recreate a new one
    if os.path.exists(path):
        for file in os.listdir(path):
            os.remove(os.path.join(path, file))
        # os.chmod("/tmp/test_file", 0664)
        os.rmdir(directory)
        # os.remove(path)
    # Create the directory
    os.mkdir(path)
    return path


def reviews_list_to_docs(reviews, path):
    i = 1
    for r in reviews:
        # doc_mapping[r] =
        # clean review
        tokens = clean_doc(r)
        save_to_file(tokens, path, i)
        i += 1


# save the TOKENS OF A CLEAN REVIEW
def save_to_file(tokens, path, i):
    # create a new file for each review containing the content of that review tokens
    filename = f"review_{i}" + ".txt"
    file_path = os.path.join(path, filename)
    f = open(file_path, "w", encoding="utf-8")
    f.write('\n'.join(tokens))
    f.close()


def predict_review_sentiment(text, tokenizer, length, model):
    acc, sentiment = predict_sentiment(text, tokenizer, length, model)
    return acc, sentiment


# load doc into memory
def load_doc(filename):
    # open the file as read only
    file = open(filename, 'r')
    try:
        # read all text
        text = file.read()
    except UnicodeDecodeError:
        return None
    # close the file
    file.close()
    return text


# returns list with all reviews path names
def get_reviews_files_names(path):
    for root, dirs, documents in os.walk(path):
        # open each documents
        documents_list = []
        for doc in documents:
            documents_list.append(os.path.join(root, doc))
        return documents_list


# returns amount of positive review, negative reviews and total reviews
def count_pos_neg_reviews(documents_list):
    tokenizer, length, model = get_model_utils()
    pos_count = 0
    neg_count = 0
    total_rev = 0
    doc_sentiments = {}

    for doc in documents_list:
        text = load_doc(doc)
        if text:
            text = text.split('\n')
            text = ' '.join(text)
            total_rev += 1
            _, sentiment = predict_review_sentiment(text, tokenizer, length, model)

            if sentiment == 'NEGATIVE':
                doc_sentiments[doc] = 0
                neg_count += 1
            else:
                doc_sentiments[doc] = 1
                pos_count += 1

    res.append(doc_sentiments)
    res.append(pos_count)
    res.append(neg_count)
    res.append(total_rev)


# returns percentage of positive rev, neg rev, and total reviews checks
def get_results(movie_name):
    url = get_reviews_url(movie_name)
    if url is None:
        return None
    path = create_folder_for_reviews(movie_name)
    browser = load_browser(url)
    load_all_reviews(browser)
    reviews = reviews_to_list(browser)

    reviews_list_to_docs(reviews, path)
    documents_list = get_reviews_files_names(path)

    th = threading.Thread(target=count_pos_neg_reviews, args=(documents_list,))
    th.start()
    th.join()

    doc_sentiments = res[0]
    pos_count = res[1]
    neg_count = res[2]
    total_rev = res[3]

    pos_per = round((pos_count / total_rev * 100), 2)
    neg_per = round((neg_count / total_rev * 100), 2)
    return doc_sentiments, pos_per, neg_per, total_rev


def predict_given_review(r):
    tokenizer, length, model = get_model_utils()
    return predict_review_sentiment(r, tokenizer, length, model)


res = []

# # FOR CHECKUP PURPOSES
# movie_name = 'steven universe'
#
# doc_sentiments, pos_per, neg_per, total_rev = get_results(movie_name)
#
# print(f"The movie {movie_name} results are:\n"
#       f"{neg_per}% of reviews are negative\n"
#       f"{pos_per}% of reviews are positive\n"
#       f"out of {total_rev} reviews in total.")
