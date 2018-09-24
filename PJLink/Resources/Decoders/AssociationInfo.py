"""Implements a decoder for data passed as a Association

"""

def _get_data(name, *items):
    from collections import OrderedDict
    print(items)
    keys = items[0][1].args #[ tuple(l) if isinstance(l, list) else l for l in items[0].args ]
    vals = items[1][1].args

    return OrderedDict(zip(keys, vals))

AssociationDecoder = (
    "data",             #object name
    "AssociationInfo",  #object head
    # decoder tuples
    # they come as (key_name, (head, typename, dim_list))
    ("keys",  (None, None, [ 1 ])),
    ("vals",  (None, None, [ 1 ])), #_getArray works by depth, not true dimension, if the list isn't [ 0 ]
    _get_data
)

_decoder = AssociationDecoder