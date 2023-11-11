import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, words
from nltk.stem import PorterStemmer
from elasticsearch_dsl import Q
from elasticsearch_dsl import Search
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from operator import itemgetter

# Initialize components
stop_words = set(stopwords.words('english'))
english_word_set = set(words.words())
vectorizer = TfidfVectorizer()



# Function for text preprocessing
def preprocess_text(text):
    tokens = word_tokenize(text)
    
    tokens = [token for token in tokens if token not in string.punctuation]
    tokens = [token for token in tokens if token.lower() not in stop_words]
    tokens = [token for token in tokens if token.lower() in english_word_set]
    
    text = ' '.join(tokens)

    return text




def get_tfidf(corpus):
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    terms = vectorizer.get_feature_names_out()
    
    tfidf_scores = []
    
    for i, doc in enumerate(corpus):
        # Get the TF-IDF scores for each term in the document
        doc_tfidf = tfidf_matrix.getrow(i)
        
        doc_tfidf_dict = {term: doc_tfidf[0, j] for j, term in enumerate(terms)}
        
        sorted_doc_tfidf = sorted(doc_tfidf_dict.items(), key=itemgetter(1), reverse=True)
        
        tfidf_scores.append(sorted_doc_tfidf)

    return tfidf_scores


    
    
def pseudo_rel(query, retrieved_docs, q_index, k_pseudo_docs=10, k_pseudo_terms=10):
    retrieved_docs_new = []
    
    if q_index==0:
        print(query, "\n\n")
        
        corpus=[]
        
        for doc in retrieved_docs[:k_pseudo_docs]:
            # Use the Title ('TI') and the Abstract ('AB') to search for words
            try:
                text = doc['TI'] + doc['AB']
            
                text = preprocess_text(text)

                corpus.append(text)
            except Exception as e:
#                 print("EXCEPTION in doc:\n", e, "\n", doc, "\n\n")
                pass
        
        best_terms = get_tfidf(corpus)[0][:k_pseudo_terms]
        print(best_terms, "\n")
        
        new_query = query
        for new_term in best_terms:
            new_query += " " + new_term[0]
        
        print(new_query, "\n")
            
    

    retrieved_docs_new = retrieved_docs
    return retrieved_docs_new













