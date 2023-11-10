import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from elasticsearch_dsl import Q
from elasticsearch_dsl import Search
import string

# Initialize NLTK components
stop_words = set(stopwords.words('english'))
porter = PorterStemmer()

stop_words = set(stopwords.words('english'))
english_word_set = set(words.words())


# Function for text preprocessing
def preprocess_text(text):
    tokens = word_tokenize(text)
    
    tokens = [token for token in tokens if token not in string.punctuation]
    tokens = [token for token in tokens if token.lower() not in stop_words]
    tokens = [token for token in tokens if token.lower() in english_word_set]


#     tokens = [porter.stem(token) for token in tokens if token.isalpha() and token not in stop_words]
    return tokens




def pseudo_rel(query, response, q_index):
    if q_index==0:
        print(query, "\n\n")
        
        text = response[0]['AB']
        
        print(text, "\n\n")
        
        text = preprocess_text(text)
        
        print(text)

    
    return response