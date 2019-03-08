from PJLink.HelperClasses import *

class ImageData:
    """Holder class for Image data

    """

    def __init__(self, dims, cs, itype, data):
        self.dimensions = dims[:2]
        self.data = data
        self.color_space = cs
        self.image_type = itype
        self.channels = dims[2] if len(dims) > 2 else 1

    @staticmethod
    def _detmode(cs, itype, channels):

        mode = cs
        dtype = None
        if itype == "Bit":
            mode = "1"
            dtype = "uint8"
        elif itype == "Byte":
            dtype = "uint8"
            if cs == "Grayscale":
                mode = "L"
            elif cs == "RGB":
                mode = "RGB"
                if channels == 4:
                    mode = "RGBA"
            if cs == "HSB":
                mode = "HSV"
        elif itype == "Bit16":
            dtype = "int32"
            mode = "I"
        elif itype == "Real" or itype == "Real32":
            mode = "F"
            dtype = "float32"

        return mode, dtype

    _mode_cs_map = {
        "1" : "Grayscale",
        "L" : "Grayscale",
        "RGB" : "RGB",
        "RGBA" : "RGB",
        "HSV"  : "HSB",
        "CMYK" : "CMYK",
        "LAB"  : "LAB",
        "F"    : "RGB",
        "I"    : "RGB"
    }

    _mode_it_map = {
        "1" : "Bit",
        "L" : "Byte",
        "RGB" : "Byte",
        "RGBA" : "Byte",
        "HSV"  : "Byte",
        "CMYK" : "Byte",
        "LAB"  : "Byte",
        "F"    : "Real32",
        "I"    : "Bit16"
    }

    @classmethod
    def _invmode(cls, mode):
        cs = cls._mode_cs_map[mode]
        itype = cls._mode_it_map[mode]

        return cs, itype

    @classmethod
    def _topil(cls, dims, cs, itype, data, channels):
        from PIL import Image
        mode, dtype = cls._detmode(cs, itype, channels)

        try:
            cast = data.astype(dtype)
        except AttributeError:
            cast = data

        try:
            dbuf = cast.data.tobytes()
        except AttributeError:
            try:
                dbuf = cast.tobytes()
            except AttributeError:
                dbuf = cast.data

        return Image.frombuffer(mode, dims, dbuf, "raw", mode, 0, 1)

    @property
    def pil_mode(self):
        return self._detmode(self.color_space, self.image_type, self.channels)

    @classmethod
    def frompil(cls, img):
        """frompil constructs a ImageData object from a PIL image

        :param img:
        :return:
        """

        cs, itype = cls._invmode(img.mode)

        if Env.HAS_NUMPY:
            import numpy as np
            dats = np.asarray(img)
        else:
            import array

            array_data = img.__array_interface__
            # to_type_code = array_data["typestr"]
            # bom = to_type_code[0]
            # form = to_type_code[1]
            # num_bits = to_type_code[2]
            if itype == "Bit" or itype == "Byte":
                tc = "B"
            elif itype == "Bit16":
                tc = "h"
            elif itype == "Real32":
                tc = "f"
            dbuf = array.array(tc, array_data["data"])
            dats = BufferedNDArray(dbuf, array_data["shape"])

        return cls(dats.shape, cs, itype, dats)

    def topil(self):
        return self._topil(tuple(self.dimensions), self.color_space, self.image_type, self.data, self.channels)

    @property
    def expr(self):
        return MPackage.Image(
            self.data,
            self.image_type,
            ColorSpace_ = self.color_space
        )

def _get_type(head, link, stack):
    return stack["dtype"]
def _get_dims(head, link, stack):
    return stack["dims"]
def _get_image(name, *items, ImageData=ImageData):
    odict = dict(items)
    return ImageData(odict["dims"], odict["color_space"], odict["bit_size"], odict["data"])

ImageArrayInfoDecoder = (
    "image",             #object name
    "ImageArrayInfo",  #object head
    # decoder tuples
    # they come as (key_name, head, typename, dim_list )
    ("dims",        (None, "Integer", [ 1 ])), #_getArray works by depth, not true dimension, if the list isn't [ 0 ]
    ("color_space", (None, "String", None)),
    ("bit_size",    (None, "String", None)),
    ("dtype",       (None, "String", None)),
    ("data",        (None, _get_type, _get_dims)),
    _get_image
)

_decoder = ImageArrayInfoDecoder