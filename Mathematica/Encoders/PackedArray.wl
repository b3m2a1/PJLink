(* ::Package:: *)

list_List?(Times@@Dimensions[#]>50&):>
  Module[
    { 
      expr = Developer`ToPackedArray@list
      },
    PJLink`TypeHints`PackedArrayInfo[
      Head@Extract[expr, Table[1, {ArrayDepth@expr}]],
      Dimensions@expr,
      expr
      ]/;Developer`PackedArrayQ@expr
    ]
