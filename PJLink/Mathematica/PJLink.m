(* ::Package:: *)

(* ::Section:: *)
(*PJLink*)


(* Mathematica Package *)
(* Created by Mathematica Plugin for IntelliJ IDEA *)

(* :Title: PJLink *)
(* :Context: PJLink` *)
(* :Date: 2018-09-13 *)

(* :Package Version: 0.1 *)
(* :Mathematica Version: *)
(* :Keywords: *)
(* :Discussion: *)


(* ::Subsection:: *)
(*PJLink*)


BeginPackage["PJLink`"]
(* Exported symbols added here with SymbolName::usage *)

InstallPython::usage="InstallPython[] Loads and installs a python kernel link";
FindPython::usage="FindPython[] finds an installed python kernel";
ClosePython::usage="ClosePython[] closes a python kernel";
PyEvaluate::usage="PyEval[] evaluates code on the python side";
PyEvaluateString::usage="PyEval[] Evaluates a code string on the python side";
PyWrite::usage="PyWrite[] writes a command to the python stdin";
PyWriteString::usage="PyWriteString[] writes a command string to the python stdin";
PyRead::usage="PyRead[] reads from the python stdout";
PyReadErr::usage="PyRead[] reads from the python stderr";


(* ::Subsubsection::Closed:: *)
(* Package*)


BeginPackage["`Package`"]

$DefaultPythonKernel::usage="The default kernel for evaluations";
$PythonKernels::usage="A listing of the configured python kernels";
AddTypeHints::usage="AddTypeHints[expr] Adds type hints to expr that python can use";
PackedArrayInfo::usage="A typehint added by AddTypeHints (currently the only one)";
CallPythonPacket::usage="A packet of info for python on what to call";

EndPackage[]


(* ::Subsubsection::Closed:: *)
(*SymbolicPython*)


BeginPackage["`SymbolicPython`"]

Get@FileNameJoin@{DirectoryName@$InputFileName, "SymbolicPython.m"};

EndPackage[]


(* ::Subsection:: *)
(*Private*)


Begin["`Private`"]


(* ::Subsubsection::Closed:: *)
(*$PythonKernels*)


If[Not@AssociationQ@$PythonKernels,
  $PythonKernels=<||>
]


(* ::Subsubsection::Closed:: *)
(*Bin Stuff*)


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


(* ::Subsubsection:: *)
(*InstallPython*)


(*
  I have plans to come back and clean this up a bunch but for now this is what it is
  It's pretty trivial and simple, but it gets the job done
*)
If[!AssociationQ@$DefaultPythonKernel,
  $DefaultPythonKernel = None
  ];
$defaultPython = "python3";
Options[InstallPython] = 
  Join[
    {
      LinkObject->Automatic,
      ProcessObject->Automatic,
      LinkProtocol->Automatic,
      "LinkName"->Automatic,
      "Blocking"->True,
      "DebugLevel"->0
      },
    Options[StartProcess]
    ];
InstallPython[version:_?NumberQ|_String|Automatic:Automatic, ops:OptionsPattern[]]:=
    Module[
      {
        pyExe,
        pyKer = FindPython[version],
        link = OptionValue[LinkObject],
        lname = Replace[OptionValue["LinkName"], Except[String]:>Sequence@@{}],
        proc = OptionValue[ProcessObject]
      },
      If[!AssociationQ@pyKer,
        pyKer=<||>;
        If[!KeyExistsQ[$PythonKernels, version],
          $PythonKernels[version] = {}
          ];
        If[Quiet[!MatchQ[MathLink`LinkDeviceInformation[link],{Rule__}]],
          link = 
            LinkCreate[
              lname,
              FilterRules[{ops}, {LinkProtocol}]
              ]
          ];
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
        If[!MatchQ[proc, None|_ProcessObject?(ProcessStatus[#]==="Running"&)],
          proc = StartProcess[
            {
              pyExe, 
              startKernelPy, 
              "--blocking="<>ToString@TrueQ@OptionValue["Blocking"],
              "--debug="<>ToString@OptionValue["DebugLevel"],
              "-linkmode", "connect",
              "-linkname", pyKer["Name"] 
              },
            FilterRules[
              {
                ops,
                If[$OperatingSystem =!= "Windows",
                  ProcessEnvironment ->
                      <|
                        "PATH" -> $pySessionPathExtension <> Environment["PATH"]
                      |>,
                  Nothing
                ],
                ProcessDirectory -> pjlinkDir
                },
              Options@StartProcess
              ]
            ]
          ];
        pyKer["Process"] = proc;
        AppendTo[$PythonKernels[version], pyKer];
        If[!AssociationQ@$DefaultPythonKernel, $DefaultPythonKernel=pyKer];
        LinkWrite[pyKer["Link"],  InputNamePacket["In[1]:="]]
        ];
      If[PyEvaluate[version, InputNamePacket["In[1]:="], TimeConstraint->10]===$Aborted,
        ClosePython[version];
        $Failed,
        pyKer
        ]
      ]


(* ::Subsubsection::Closed:: *)
(*FindPython*)


FindPython[version:_?NumberQ|_String|Automatic:Automatic]:=
    Replace[$PythonKernels[version],
      {
        {l_, ___}:>l,
        _->None
        }
      ];


(* ::Subsubsection::Closed:: *)
(*ClosePython*)


ClosePython[version:_?NumberQ|_String|Automatic:Automatic]:=
    With[{ker = FindPython[version]},
      If[AssociationQ@ker, 
        $PythonKernels[version] = Most @ $PythonKernels[version];
        If[ ker == $DefaultPythonKernel, $DefaultPythonKernel = None];
        Quiet@KillProcess@ker["Process"];
        Quiet@LinkClose@ker["Link"];
        ]
      ];
      


(* ::Subsubsection::Closed:: *)
(*pyEvalPacket*)


pyEvalPacket[link_, packet_, timeout_:10]:=
    Module[{pkt = packet, to = Quantity[timeout, "Seconds"], res},
      If[SameQ[LinkWrite[link, pkt], $Failed], Return[$Failed]];
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
        ];
      sequenceResult
      ];


(* ::Subsubsection::Closed:: *)
(*cleanUpEnv*)


cleanUpEnv//Clear


cleanUpEnv[pker_, version_, $Aborted]:=
  If[(
      Quiet[!OptionQ[MathLink`LinkDeviceInformation[pker["Link"]]]] || 
        ProcessStatus@pker["Process"]==="Finished"
      ), 
    Print@version;
    ClosePython[version],
    $Aborted
    ];
cleanUpEnv[_, _, p_]:=p


(* ::Subsubsection::Closed:: *)
(*Evaluate*)


Options[PyEvaluate] = 
  {
    TimeConstraint->5,
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
      If[AssociationQ@pker,
        sym = ToPython@ToSymbolicPython[expr];
        If[OptionValue@"EchoSymbolicForm", Echo@sym];
        link = pker["Link"];
        cleanUpEnv[
          pker, 
          OptionValue["Version"],
          pyEvalPacket[link, CallPacket[1, sym], to]
          ],
        $Failed (* TODO: Throw a message... *)
        ]
      ];
PyEvaluate~SetAttributes~HoldFirst;


(* ::Subsubsection::Closed:: *)
(*EvaluateString*)


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
      If[AssociationQ@pker,
        link = pker["Link"];
        cleanUpEnv[
            pker, 
            OptionValue["Version"],
            pyEvalPacket[link, CallPacket[1, "Evaluate"@expr], to] (* this is a hack but ah well *)
            ],
        $Failed
        ]
    ]


(* ::Subsubsection::Closed:: *)
(*Write*)


Options[PyWrite]=
  {
    Version->Automatic
    };
PyWrite[expr_, ops:OptionsPattern[]]:=
  Module[
      {
        pker = FindPython[OptionValue[Version]],
        cmd
        },
      If[AssociationQ@pker,
        Block[{$ToPythonStrings=True},
          cmd = TToPython@ToSymbolicPython[pker]
          ];
        WriteLine[pker["Process"], cmd],
        $Failed
        ]
      ]


(* ::Subsubsection::Closed:: *)
(*WriteString*)


Options[PyWriteString]=
  {
    Version->Automatic
    };
PyWriteString[cmd_, ops:OptionsPattern[]]:=
  Module[
      {
        pker = FindPython[OptionValue[Version]]
        },
      If[AssociationQ@pker,
        WriteLine[pker["Process"], cmd],
        $Failed
        ]
      ]


(* ::Subsubsection::Closed:: *)
(*Read*)


Options[PyRead]=
  {
    Version->Automatic
    };
PyRead[ops:OptionsPattern[]]:=
  Module[
      {
        pker = FindPython[OptionValue[Version]]
        },
      If[AssociationQ@pker,
        ReadString[pker["Process"], EndOfBuffer],
        $Failed
        ]
      ]


(* ::Subsubsection::Closed:: *)
(*ReadErr*)


Options[PyReadErr]=
  {
    Version->Automatic
    };
PyReadErr[ops:OptionsPattern[]]:=
  Module[
      {
        pker = FindPython[OptionValue[Version]]
        },
      If[AssociationQ@pker,
        ReadString[ProcessConnection[pker["Process"], "StandardError"], EndOfBuffer],
        $Failed
        ]
      ]


(* ::Subsubsection::Closed:: *)
(*AddTypeHints*)


AddTypeHints[eval_] :=
    Block[{expr = eval},
      expr = Developer`ToPackedArray[expr];
      If[Developer`PackedArrayQ[expr],
        PackedArrayInfo[Head@Extract[expr, Table[1, {ArrayDepth@expr}]], Dimensions@expr, expr],
        expr
        ]
      ]


(* ::Subsubsection::Closed:: *)
(*PythonTraceback*)


Format[pt:PythonTraceback[ts_]]:=
  Interpretation[
    Style[ts, Red],
    pt
    ]


(* ::Subsubsection::Closed:: *)
(*End*)


End[] (* `Private` *)

EndPackage[]
