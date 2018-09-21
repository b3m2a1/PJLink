(* ::Package:: *)

ra_RawArray:>
  With[{expr=Normal@ra, itype=Developer`RawArrayType@ra},
    PJLink`TypeHints`RawArrayInfo[
      itype,
      Head@Extract[expr, Table[1, {ArrayDepth@expr}]],
      Dimensions@expr,
      expr
      ]
    ]
