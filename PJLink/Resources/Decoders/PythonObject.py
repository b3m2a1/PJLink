"""Implements a decoder for data passed as a HashTable

"""

def _get_obj(name, *items):
    version = items[0]
    ht = dict(zip(items[1].args, items[2].args))
    ht["_HashTable_version_"] = version
    return ht

PyObjectDecoder = (
    "data",             #object name
    "PythonObject",    #object head
    # decoder tuples
    # they come as (key_name, (head, typename, dim_list))
    ("ref", (None, "String", None)),
    # really there are other opts but we ignore them
    _get_obj
)

_decoder = PyObjectDecoder