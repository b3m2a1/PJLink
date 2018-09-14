(* ::Package:: *)

(* Mathematica Package *)
(* Created by Mathematica Plugin for IntelliJ IDEA *)

(* :Title: PJLink *)
(* :Context: PJLink` *)
(* :Date: 2018-09-13 *)

(* :Package Version: 0.1 *)
(* :Mathematica Version: *)
(* :Keywords: *)
(* :Discussion: *)

BeginPackage["PJLink`"]
(* Exported symbols added here with SymbolName::usage *)

InstallPython::usage="InstallPython[] Loads and installs a python kernel link";
FindPython::usage="FindPython[] finds an installed python kernel";
ClosePython::usage="ClosePython[] closes a python kernel";
PyEvaluate::usage"PyEval[] Evaluates code on the python side";
PyEvaluateString::usage="PyEval[] Evaluates a code string on the python side";

BeginPackage["`Package`"]

$DefaultPythonKernel::usage="The default kernel for evaluations";
$PythonKernels::usage="A listing of the configured python kernels";
AddTypeHints::usage="AddTypeHints[expr] Adds type hints to expr that python can use";
PackedArrayInfo::usage="A typehint added by AddTypeHints (currently the only one)";
CallPythonPacket::usage="A packet of info for python on what to call";

EndPackage[]

BeginPackage["`SymbolicPython`"]

Get@FileNameJoin@{DirectoryName@$InputFileName, "SymbolicPython.m"};

EndPackage[]

Begin["`Private`"]

If[Not@AssociationQ@$PythonKernels,
  $PythonKernels=<||>
]

pjlinkDir = Nest[DirectoryName, $InputFileName, 2];

startKernelPy = "start_kernel.py";

$pySessionPathExtension = (* I need this because Mathematica's $PATH isn't quit right *)
    Switch[$OperatingSystem,
      "MacOSX",
      StringRiffle[
        Append[""]@
            Join[
              {
                "/usr/local/bin"
              },
              FileNames[
                "bin",
                "/Library/Frameworks/Python.framework/Versions",
                2
              ],
              FileNames[
                "bin",
                "/System/Library/Frameworks/Python.framework/Versions",
                2
              ]
            ],
        ":"
      ],
      _,
      ""
    ]

(*
  I have plans to come back and clean this up a bunch but for now this is what it is
  It's pretty trivial and simple, but it gets the job done
*)
If[!AssociationQ@$DefaultPythonKernel,
  $DefaultPythonKernel = None
  ];
$defaultPython = "python3";
InstallPython[version:_?NumberQ|_String|Automatic:Automatic, ops:OptionsPattern[]]:=
    Module[
      {
        pyExe,
        pyKer = <||>,
        link
      },

      If[!KeyExistsQ[$PythonKernels, version],
        $PythonKernels[version] = {}
      ];
      link = LinkCreate[];
      pyExe =
        Which[
          NumberQ@version,
            "python"<>ToString[version],
          StringQ@version && FileExistsQ@version,
            version,
          StringQ@version && !StringStartsQ[version, "python"],
            "python"<>version,
          Not@StringQ@version,
            $defaultPython,
          True,
            version
          ];
      pyKer["Python"]  = pyExe;
      pyKer["Link"]    = link;
      pyKer["Name"]    = link[[1]];
      pyKer["Process"] =
          StartProcess[
            {pyExe, startKernelPy, "-b", "-linkmode", "connect", "-linkname", pyKer["Name"] },
            {
              If[$OperatingSystem =!= "Windows",
                ProcessEnvironment ->
                    <|
                      "PATH" -> $pySessionPathExtension <> Environment["PATH"]
                    |>,
                Nothing
              ],
              ProcessDirectory -> pjlinkDir
            }
          ];
      AppendTo[$PythonKernels[version], pyKer];
      If[!AssociationQ@$DefaultPythonKernel, $DefaultPythonKernel=pyKer];
      LinkWrite[pyKer["Link"],  InputNamePacket["In[1]:="]];
      pyKer
    ]

FindPython[version:_?NumberQ|_String|Automatic:Automatic]:=
    Replace[$PythonKernels[version],
      {
        {l_, ___}:>l,
        _->None
        }
      ];

ClosePython[version:_?NumberQ|_String|Automatic:Automatic]:=
    With[{ker = FindPython[version]},
      If[AssociationQ@ker, 
        $PythonKernels[version] = Most @ $PythonKernels[version];
        If[ ker == $DefaultPythonKernel, $DefaultPythonKernel = None];
        Quiet@KillProcess@ker["Process"];
        Quiet@LinkClose@ker["Link"];
        ]
      ];
      
pyEvalPacket[link_, packet_, timeout_:10]:=
    Module[{pkt = packet, start = Now, to = Quantity[timeout, "Seconds"], res},
    
      (*AbortProtect*)Identity[
        While[Now - start < to,
          If[
            SameQ[LinkWrite[link, pkt], $Failed],
            Return[$Failed]
          ];
          res = TimeConstrained[LinkRead[link, HoldComplete], timeout];
          Switch[res,
            HoldComplete @ EvaluatePacket @ _,
              pkt = ReturnPacket[CheckAbort[res[[1, 1]], $Aborted]],
            HoldComplete @ ReturnPacket @ _,
              Return[res[[1, 1]]],
            HoldComplete @ _Sequence,
              sequenceResult = res[[1]];
              Break[],
            HoldComplete @ _,
              Return[res[[1]]],
            _,
              Return[res]
            ]
          ]
        ]
      ];

Options[PyEvaluate] = 
  {
    TimeConstraint->10,
    Version->Automatic,
    "EchoSymbolicForm"->False
    };
PyEvaluate[expr_, ops:OptionsPattern[]]:=
    Module[
      {
        pker = FindPython[OptionValue[Version]],
        link,
        sym,
        cm,
        to = If[NumericQ@OptionValue[TimeConstraint], OptionValue[TimeConstraint], 10]
      },
      sym = ToPython@ToSymbolicPython[expr];
      If[OptionValue@"EchoSymbolicForm", Echo@sym];
      link = pker["Link"];
      Internal`WithLocalSettings[
        cm = Internal`$ContextMarks;
        Internal`$ContextMarks = False,
        pyEvalPacket[link, CallPacket[1, sym], to],
        Internal`$ContextMarks = cm
        ]
      ];
PyEvaluate~SetAttributes~HoldFirst;

Options[PyEvaluateString] = 
  {
    TimeConstraint->10,
    Version->Automatic
    };
PyEvaluateString[expr_, ops:OptionsPattern[]]:=
    Module[
      {
        pker = FindPython[OptionValue[Version]],
        link,
        sym,
        to = If[NumericQ@OptionValue[TimeConstraint], OptionValue[TimeConstraint], 10]
      },
      link = pker["Link"];
      pyEvalPacket[link, CallPacket[1, "Evaluate"@expr], to] (* this is a hack but ah well *)
    ]

AddTypeHints[eval_] :=
    Block[{expr = eval},
      expr = Developer`ToPackedArray[expr];
      If[Developer`PackedArrayQ[expr],
        PackedArrayInfo[Head@Extract[expr, Table[1, {ArrayDepth@expr}]], Dimensions@expr, expr],
        expr
        ]
      ]

End[] (* `Private` *)

EndPackage[]
