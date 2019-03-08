# the decoders are all made available to the encoders
# usually the decoding process is more involved than the encoding one
# so classes like ImageData will be defined there

from PIL import Image as PILImage
from ..Decoders.ImageArrayInfo import ImageData

def _get_encodeable(img, link):
    return ImageData.frompil(img)

_encoder = (
    "PILImageEncoder",
    PILImage.Image,    # type object
    _get_encodeable # method for getting encodable version of data
)