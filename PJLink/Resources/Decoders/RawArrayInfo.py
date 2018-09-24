"""Implements a decoder for data passed as a RawArray

"""

from collections import namedtuple

base_class = namedtuple("RawArrayData", ["internal_type", "data"])
class RawArrayData(base_class):
    @property
    def expr(self):
        return {
            "head" : "RawArray",
            "args" : (
                self.internal_type,
                self.data
            )
        }

def _get_type(head, link, stack):
    otype = stack["dtype"]
    if not isinstance(otype, str):
        otype = otype.name
    return otype
def _get_dims(head, link, stack):
    return stack["dims"]
def _get_raw_array_data(name, *items):
    return RawArrayData(items[0], items[-1])

RawArrayDecoder = (
    "RawArray",             #object name
    "RawArrayInfo",  #object head
    # decoder tuples
    # they come as (key_name, head, typename, dim_list )
    ("data_type", (None, "String",  None)),
    ("dtype",     (None, "Symbol",  None)),
    ("dims",      (None, "Integer", [ 1 ])), #_getArray works by depth, not true dimension, if the list isn't [ 0 ]
    ("data",      (None, _get_type, _get_dims)),
    _get_raw_array_data
)

_decoder = RawArrayDecoder