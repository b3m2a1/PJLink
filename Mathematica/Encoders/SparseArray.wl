(* ::Package:: *)

expr_SparseArray:>
  With[
    {
      nzvs = expr["NonzeroValues"],
      cis = First@Transpose@expr["ColumnIndices"],
      rps = expr["RowPointers"],
      bg = expr["Background"]
      },
    PJLink`TypeHints`SparseArrayInfo[
      Dimensions@expr,
      Head@nzvs[[1]],
      nzvs,
      Dimensions[cis],
      cis,
      Dimensions[rps],
      rps,
      bg
      ]
    ]
