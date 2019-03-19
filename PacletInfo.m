(* ::Package:: *)

Paclet[
  Name -> "PJLink",
  Version -> "1.1.1",
  Creator -> "b3m2a1@gmail.com",
  Description -> "A JLink-like interface for python",
  Extensions -> {
    	{
     		"Kernel",
     		"Root" -> "Mathematica",
     		"Context" -> {"PJLink`"}
     	},
    {
      "PacletServer",
      "Description" -> "A J/Link-like interface to python that provides a mechanism to evaluate code in python\
from Mathematica and in Mathematica from python. Memory is used efficiently allowing transfer of large data.",
      "License" -> "MIT",
      "Tags" -> {"python", "MathLink"},
      "Categories" -> {"Development"}
    }
    }
 ]
