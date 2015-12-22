import sys
from _functools import reduce
import copy
import jieba
import math


class QueryIndex:
    def __init__(self, inverse_index):
        self.index = inverse_index  # dict
        self.stopwords = []
        self.stopwordsFile = 'stopword.txt'
        self.get_stopwords()
        self.indexFile = ""
        self.result = []
        self.terms =[]

    def get_params(self):
        param = sys.argv
        # self.stopwordsFile = param[1]
        self.indexFile = param[2]

    def get_stopwords(self):
        with open(self.stopwordsFile, 'r', encoding='gbk') as stopword_list:
            self.stopwords = [line.rstrip('\n') for line in stopword_list]

    def query_type(self, q):
        if '"' in q:
            return 'PQ'
        return 'FTQ'

    def get_terms(self, query):
        """ processing query ,unsolved
        :param query: query_from_web
        :return:list
        """
        query = query.split()
        terms = [x for x in query if x not in self.stopwords]
        str_terms = ''.join(map(str, terms)).encode('UTF-8')
        return jieba.lcut_for_search(str_terms)

    def get_postings(self, terms):
        return [self.index[term] for term in terms]

    def get_docs_from_postings(self, postings):
        return [doc.key() for doc in postings]

    # Free text queries
    def free_text_queries(self):
        if len(self.terms) == 0:
            self.result = []
            return
        docs = set()
        for term in self.terms:
            dict_doc = self.index.get(term)
            if dict_doc is None:
                del term
            else:
                term_docs = list(dict_doc.keys())
                docs |= set(term_docs)
        docs = list(docs)
        self.result = docs
        # print("free-text :", docs)
        return

    def intersect_postlists(self, lists):
        if len(lists) == 0:
            return []
        lists.sort(key=len)
        return list(reduce(lambda x, y: set(x) & set(y), lists))

    # Phrase Query
    def phrase_query(self):
        if len(self.terms) == 0:
            print()
        elif len(self.terms) == 1:
            self.free_text_queries(self.terms)

        for term in self.terms:
            if term not in self.index:
                return []
        postings = self.get_postings(self.terms)
        docs = self.get_docs_from_postings(postings)
        docs = self.intersect_postlists(docs)

        for i in range(len(postings)):
            for doc in postings[i].keys():
                if doc not in docs:
                    del postings[doc]
        postings = copy.deepcopy(postings)  # ?

        for i in range(len(postings)):
            for doc in postings[i].keys():
                postings[i][doc] = [x - i for x in postings[i][docs]]

        result = []
        """foreach doc intersect"""
        for doc in postings[0].keys():
            li = self.intersect_postlists(list(x[doc].value() for x in postings))
            if not li:
                continue
            else:
                result.append(doc)
        print(result)
        return result

    def log10(self,num):
        return math.log(num)/math.log(10)

    def cmpt_tf_idf(self):
        tf_idf_dict = {}
        N = 100000.0  # doc set number
        for term in self.terms:
            if term not in self.index:
                idf = self.log10(N/(N-1))
            else:
                idf = self.log10(N/len(self.index[term]))
            for doc in self.result:
                tf_idf = (1+self.log10(len(self.index[term][doc])))*idf
                if doc in tf_idf_dict:
                    tf_idf_dict[doc] += tf_idf
                else:
                    tf_idf_dict[doc] = tf_idf
        return tf_idf_dict

    def query_index(self, q):
        # q string
        if len(q) == 0:
            print([])
            return []
        qt = self.query_type(q)
        self.terms = self.get_terms(q)
        if qt == 'FTQ':
            self.free_text_queries()
        elif qt == 'PQ':
            self.phrase_query()

        tf_idf = self.cmpt_tf_idf()

        sorted(self.result, key=lambda doc: tf_idf[doc])
        # cmp=lambda x, y: operator.ge(tf_idf[x], tf_idf[y]))
        print(self.result)

    def read_index_from_disk(self):

        f = open(self.indexFile, 'r')
        for line in f:
            line = line.rstrip()
            term_id, postings = line.split('|')
            # term_id = 'term ID' ,postings ='docID1:pos1,pos2;docID2:pos1,pos2,pos3;'
            postings = postings.split(';')
            postings = [x.split(':') for x in postings]
            postings = dict((int(x[0]), map(int, x[1].split(','))) for x in postings)
            self.index[term_id] = postings
        f.close()
if __name__ == '__main__':
    print("need inverse index")
    qi = QueryIndex({})
    qi.query_index("query")
