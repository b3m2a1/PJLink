(* ::Package:: *)

expr_Image?ImageQ:>
  With[
    {
      id=Replace[Image`InternalImageData[expr], 
        {
          _Image`InternalImageData:>ImageData@expr
          }
        ],
      it=ImageType@expr
      },
    PJLink`TypeHints`ImageArrayInfo[
      Dimensions@id,
      ImageColorSpace@expr, 
      it,
      If[it == "Real" || it == "Real32",
        "Double",
        "Integer"
        ],
      If[Head@id===RawArray,
        Normal@id,
        Which[
          it=="Byte", 
            255*id,
          it=="Bit16",
            65535*id,
          True,
            id
          ]
        ]
      ]
    ]
