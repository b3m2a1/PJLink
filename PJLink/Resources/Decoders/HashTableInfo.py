"""Implements a decoder for data passed as a HashTable

"""

def _get_data(name, *items):
    version = items[0][1]
    ht = dict(zip(items[1][1].args, items[2][1].args))
    ht["_HashTable_version_"] = version
    return ht

HashTableDecoder = (
    "data",             #object name
    "HashTableInfo",    #object head
    # decoder tuples
    # they come as (key_name, (head, typename, dim_list))
    ("version", (None, "Integer", None)),
    ("keys",    (None, None,      [ 1 ])),
    ("values",  (None, None,      [ 1 ])),
    _get_data
)

_decoder = HashTableDecoder