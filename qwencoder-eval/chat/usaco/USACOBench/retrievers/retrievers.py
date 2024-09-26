from abc import ABC, abstractmethod
import time
import random
import numpy as np
from tqdm import tqdm

from rank_bm25 import BM25Okapi

from .utils import AggregationType


class Retriever(ABC):

    def __init__(self, docs):
        self.docs = docs

    @abstractmethod
    def retrieve(self, query, num_docs=10):
        pass


class BM25Retriever(Retriever):

    def __init__(self, docs, referrals=None, num_referrals=30, aggregation=AggregationType.CONCAT, doc_weight=1, verbose=False):
        '''
        docs: list of document strings
        referrals: list of lists of referrals for each document, or None
        num_referrals: int >= 1, num referrals to use to augment each document representation
            (only used if referrals is not None)
        aggregation: Aggregation (only used if referrals is not None)
        doc_weight: int >= 0, weight to give to original document text, compared to referrals
            e.g. if 1, document text is weighted the same as a single referral
            if 0, document text is excluded and representation consists only of referrals
            (only applies if referrals is not None)
        '''
        if verbose:
            print('Building BM25 corpus...')
            start_time = time.time()

        self.docs = []
        self.aggregation = aggregation
        self.num_referrals = num_referrals
        corpus = []
        if referrals is None:
            if verbose:
                print('Not using referral augmentation')
            corpus = docs
            self.docs = np.array(docs)
        else:
            if verbose:
                print('Using referral augmentation, uniformly sampling {} referrals per document'.format(num_referrals))

            assert aggregation in set([AggregationType.CONCAT, AggregationType.SHORTEST_PATH])
            assert isinstance(doc_weight, int) and doc_weight >= 0
            assert isinstance(num_referrals, int) and num_referrals >= 1
            if aggregation == AggregationType.CONCAT:
                for doc, referral_list in tqdm(zip(docs, referrals), disable=not verbose):
                    # if less than num_referrals referrals, use all available
                    keys = [doc] * doc_weight + random.sample(referral_list, min(num_referrals, len(referral_list)))
                    corpus.append(' '.join(keys))
                self.docs = np.array(docs)
            elif aggregation == AggregationType.SHORTEST_PATH:
                for doc, referral_list in tqdm(zip(docs, referrals), disable=not verbose):
                    # if less than num_referrals referrals, use all available
                    referral_subset = random.sample(referral_list, min(num_referrals, len(referral_list)))
                    corpus.extend([' '.join([doc] * doc_weight + [referral]) for referral in referral_subset])
                    self.docs.extend([doc] * len(referral_subset))
                self.docs = np.array(self.docs)

        tokenized_corpus = [doc.split(' ') for doc in corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

        if verbose:
            print('Took {} seconds'.format(time.time() - start_time))

    # query: string
    # num_docs: int, number of top documents to retrieve
    def retrieve(self, query, num_docs=10):
        num_docs = min(num_docs, len(self.docs))
        tokenized_query = query.split(' ')

        if self.aggregation == AggregationType.SHORTEST_PATH:
            # since we want num_docs unique documents, we retrieve more, then filter duplicates
            num_docs_before_filter = min(num_docs * self.num_referrals, len(self.docs))
            docs_before_filter = self.bm25.get_top_n(tokenized_query, self.docs, n=num_docs_before_filter)
            return list(dict.fromkeys(docs_before_filter))[:num_docs]

        return self.bm25.get_top_n(tokenized_query, self.docs, n=num_docs)
