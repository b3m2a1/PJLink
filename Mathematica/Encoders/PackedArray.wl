(* ::Package:: *)

expr_List?(Times@@Dimensions[#]>50&):>
  With[{pa=Developer`ToPackedArray@expr},
    PJLink`TypeHints`PackedArrayInfo[
      Head@Extract[expr, Table[1, {ArrayDepth@expr}]],
      Dimensions@expr,
      expr
      ]/;Developer`PackedArrayQ@pa
    ]
