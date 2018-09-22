from PJLink.HelperClasses import *

class SparseArrayData:
    """Holder class for SparseArray data

    """

    SPARSE_ARRAY_VERSION = 1

    def __init__(self, dims, nzvs, rps, cis, bg):
        self.shape = dims
        self.non_zero_values = nzvs
        self.row_pointers = rps
        self.column_indices = cis
        self.background = bg

    @staticmethod
    def _tonumpy(dims, nzvs, rps, cis, bg):
        import scipy.sparse as sp
        return sp.csr_matrix((nzvs, cis, rps), dims)

    def tonumpy(self):
        return self._tonumpy(self.shape, self.non_zero_values, self.row_pointers, self.column_indices, self.background)

    @property
    def expr(self):
        return MPackage.SparseArray(
            MPackage.Automatic,
            self.shape,
            self.background,
            [ self.SPARSE_ARRAY_VERSION,
              [
                [ self.row_pointers, [ MPackage.Transpose(self.column_indices) ] ],
                self.non_zero_values
              ]
            ]
        )

def _get_type(head, link, stack):
    otype = stack["dtype"]
    if not isinstance(otype, str):
        otype = otype.name
    return otype
def _get_ci_dims(head, link, stack):
    return stack["ci_dims"]
def _get_rp_dims(head, link, stack):
    return stack["rp_dims"]
def _get_sparse_array(name, *items, SparseArrayData=SparseArrayData):
    d = dict(items)
    return SparseArrayData(d["dims"], d["nzvs"], d["rps"], d["cis"], d["bg"])

SparseArrayDecoder = (
    "SparseArray",      #object name
    "SparseArrayInfo",  #object head
    # decoder tuples
    # they come as (key_name, head, typename, dim_list )
    ("dims",    (None, "Integer", [ 1 ])), #_getArray works by depth, not true dimension, if the list isn't [ 0 ]
    ("dtype",   (None, "Symbol", None)),
    ("nzvs",    (None, _get_type, [ 1 ])),
    ("ci_dims", (None, "Integer", [ 1 ])),
    ("cis",     (None, "Integer", _get_ci_dims)),
    ("rp_dims", (None, "Integer", [ 1 ])),
    ("rps",     (None, "Integer", _get_rp_dims)),
    ("bg",      (None, None, None)), #this means get literally anything
    _get_sparse_array
)

_decoder = SparseArrayDecoder

