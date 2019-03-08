

from ...HelperClasses import ObjectDecoder
from collections import OrderedDict

def _get_encodeable(o, l):
    return OrderedDict(iter(o))

_encoder = (
    "ObjectDecoderEncoder",
    ObjectDecoder,    # type object
    _get_encodeable # method for getting encodable version of data
)