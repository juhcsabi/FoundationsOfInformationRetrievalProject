import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, words
from nltk.stem import PorterStemmer
from elasticsearch_dsl import Q
from elasticsearch_dsl import Search
import string

# Initialize NLTK components
stop_words = set(stopwords.words('english'))
english_word_set = set(words.words())


# Function for text preprocessing
def preprocess_text(text):
    tokens = word_tokenize(text)
    
    tokens = [token for token in tokens if token not in string.punctuation]
    tokens = [token for token in tokens if token.lower() not in stop_words]
    tokens = [token for token in tokens if token.lower() in english_word_set]

    return tokens




def pseudo_rel(query, retrieved_docs, q_index):
    if q_index==0:
        print(query, "\n\n")
        
        for doc in retrieved_docs:
            # Use the Title ('TI') and the Abstract ('AB') to search for words
            text = doc['TI'] + doc['AB']
            
            # Return the tokenized text
            text_terms = preprocess_text(text)

            feedback_term_freq = {}
            for term in text_terms:
                if term in feedback_term_freq:
                    feedback_term_freq[term] += 1
                else:
                    feedback_term_freq[term] = 1

            # Sort the feedback terms by their frequency
            sorted_feedback_terms = sorted(feedback_term_freq.items(), key=lambda x: x[1], reverse=True)

            print(sorted_feedback_terms, "\n")

    
    return response