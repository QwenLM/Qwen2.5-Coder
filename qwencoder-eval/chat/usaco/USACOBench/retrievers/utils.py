from enum import Enum

# referral aggregation strategy
class AggregationType(Enum):
    CONCAT        = 1
    MEAN          = 2 # note: only available for dense retrievers
    SHORTEST_PATH = 3

# for dense encoders, similarity function (often specified by encoder, e.g. in paper)
class SimilarityType(Enum):
    COSINE        = 1
    DOT           = 2
