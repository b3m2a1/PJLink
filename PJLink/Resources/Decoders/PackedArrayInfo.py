"""Implements a decoder for data passed as a PackedArray

"""

def _get_type(head, link, stack):
    otype = stack["dtype"]
    if not isinstance(otype, str):
        otype = otype.name
    return otype
def _get_dims(head, link, stack):
    return stack["dims"]
def _get_data(name, items):
    return items[-1][-1]

PackedArrayDecoder = (
    "data",             #object name
    "PackedArrayInfo",  #object head
    # decoder tuples
    # they come as (key_name, head, typename, dim_list )
    ("dtype", None, "Symbol", None),
    ("dims", None, "Integer", [ 1 ]), #_getArray works by depth, not true dimension, if the list isn't [ 0 ]
    ("data", None, _get_type, _get_dims),
    _get_data
)

_decoder = PackedArrayDecoder