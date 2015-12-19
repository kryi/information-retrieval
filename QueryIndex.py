import sys
from _functools import reduce
import copy
import jieba


class QueryIndex:
    def __init__(self, inverse_index):
        self.index = inverse_index  # dict
        self.stopwords = []
        self.stopwordsFile = 'stopword.txt'
        self.get_stopwords()
        self.indexFile = ""
        self.result = []

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
        elif len(q.split()) > 1:
            return 'FTQ'
        else:
            return 'OWQ'

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

    # one word queries
    def one_word_query(self, q):
        terms = self.get_terms(q)
        # print(terms)
        if len(terms) == 0:  # docs = [posting[0] for posting in self.index[terms]]
            print()
            return []
        elif len(terms) > 1:
            return self.free_text_queries(q)
        if terms[0] not in self.index:
            print()
            return []
        else:
            docs = list(self.index[terms[0]].keys())
            print(docs)
            return docs

    # Free text queries
    def free_text_queries(self, q):

        terms = self.get_terms(q)
        if len(terms) == 0:
            print()
            return []
        docs = set()
        for term in terms:
            dict_doc = self.index.get(term)
            if dict_doc is None:
                term_docs = []
            else:
                term_docs = list(dict_doc.keys())
            docs &= set(term_docs)
        docs = list(docs)
        print(docs)
        return docs

    def intersect_postlists(self, lists):
        if len(lists) == 0:
            return []
        lists.sort(key=len)
        return list(reduce(lambda x, y: set(x) & set(y), lists))

    # Phrase Query
    def phrase_query(self, q):
        terms = self.get_terms(q)
        if len(terms) == 0:
            print()
        elif len(terms) == 1:
            self.one_word_query(terms)

        for term in terms:
            if term not in self.index:
                return []
        postings = self.get_postings(terms)
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

    def query_index(self, q):
        # q string
        if len(q) == 0:
            return []
        qt = self.query_type(q)
        if qt == 'OWQ':
            self.one_word_query(q)
        elif qt == 'FTQ':
            self.free_text_queries(q)
        elif qt == 'PQ':
            self.phrase_query(q)

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
