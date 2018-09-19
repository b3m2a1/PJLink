(* ::Package:: *)

(* ::Section:: *)
(*PJLink*)


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
PJLink::usage="Head for messages and things";
InstallPython::usage="InstallPython[] Loads and installs a python kernel link";
FindInstalledPython::usage="FindInstalledPython[] finds an installed python kernel";
ClosePython::usage="ClosePython[] closes a python kernel";
PyEvaluate::usage="PyEval[] evaluates code on the python side";
PyEvaluateString::usage="PyEval[] Evaluates a code string on the python side";
PyWrite::usage="PyWrite[] writes a command to the python stdin";
PyWriteString::usage="PyWriteString[] writes a command string to the python stdin";
PyRead::usage="PyRead[] reads from the python stdout";
PyReadErr::usage="PyRead[] reads from the python stderr";
PythonTraceback::usage="A wrapper head for traceback formatting";


(* ::Subsubsection::Closed:: *)
(* Package*)


BeginPackage["`Package`"]

$DefaultPythonKernel::usage="The default kernel for evaluations";
$PythonKernels::usage="A listing of the configured python kernels";
AddTypeHints::usage="AddTypeHints[expr] Adds type hints to expr that python can use";
PackedArrayInfo::usage="A typehint added by AddTypeHints (currently the only one)";
CallPythonPacket::usage="A packet of info for python on what to call";

EndPackage[]


(* ::Subsubsection:: *)
(*SymbolicPython*)


BeginPackage["`SymbolicPython`"]

Get@FileNameJoin@{DirectoryName@$InputFileName, "SymbolicPython.wl"};

EndPackage[]


(* ::Subsubsection::Closed:: *)
(*Exceptions*)


BeginPackage["`Exceptions`"]

Get@FileNameJoin@{DirectoryName@$InputFileName, "Exceptions.wl"};

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


pjlinkDir = FileNameJoin@{Nest[DirectoryName, $InputFileName, 2], "PJLink"};

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


(* ::Subsubsection::Closed:: *)
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
  PackageExceptionBlock["Kernel"]@
    Module[
      {
        pyExe,
        pyKer = FindInstalledPython[version],
        link = OptionValue[LinkObject],
        lname = Replace[OptionValue["LinkName"], Except[String]:>Sequence@@{}],
        proc = OptionValue[ProcessObject],
        failed = False
      },
      If[!AssociationQ@pyKer,
        pyKer=<||>;
        If[!KeyExistsQ[$PythonKernels, version],
          $PythonKernels[version] = {}
          ];
        If[linkDead[link],
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
        If[procDead[proc] || linkDead[link],
          (*Echo@ReadString[ProcessConnection[proc, "StandardError"], EndOfBuffer];*)
          failed=True,
          pyKer["Process"] = proc;
          AppendTo[$PythonKernels[version], pyKer];
          If[!AssociationQ@$DefaultPythonKernel, $DefaultPythonKernel=pyKer];
          LinkWrite[pyKer["Link"],  InputNamePacket["In[1]:="]]
          ]
        ];
      If[failed || 
          CheckAbort[
            pyEvalPacket[link, CallPacket[1, "'Initializing'"], 3]=!="Initializing",
            True
            ],
        ClosePython[version];
        PackageRaiseException[Automatic,
          "Failed to start kernel for python executable ``",
          pyExe
          ],
        pyKer
        ]
      ]


(* ::Subsubsection::Closed:: *)
(*FindInstalledPython*)


FindInstalledPython[version:_?NumberQ|_String|Automatic:Automatic]:=
    Replace[$PythonKernels[version],
      {
        {l_, ___}:>l,
        _:>None
        }
      ];


(* ::Subsubsection::Closed:: *)
(*ClosePython*)


ClosePython[version:_?NumberQ|_String|Automatic:Automatic]:=
    With[{ker = FindInstalledPython[version]},
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


(* ::Subsubsection:: *)
(*linkDead / procDead*)


linkDead[link_]:=
  link =!= None && Quiet[!OptionQ[MathLink`LinkDeviceInformation[link]]]


procDead[proc_]:=
  proc =!= None && Quiet[ProcessStatus@proc] =!= "Running"


(* ::Subsubsection::Closed:: *)
(*cleanUpEnv*)


cleanUpEnv//Clear


cleanUpEnv[pker_, version_, $Aborted]:=
  If[(linkDead[pker["Link"]]||procDead[pker["Process"]]),
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
  PackageExceptionBlock["Kernel"]@
    Module[
      {
        pker = FindInstalledPython[OptionValue[Version]],
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
        PackageRaiseException[Automatic,
          "Found kernel `` which is not a valid kernel",
          pker
          ] (* TODO: Throw a message... *)
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
  PackageExceptionBlock["Kernel"]@
    Module[
      {
        pker = FindInstalledPython[OptionValue[Version]],
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
        PackageRaiseException[Automatic,
          "Found kernel `` which is not a valid kernel",
          pker
          ]
        ]
    ]


(* ::Subsubsection::Closed:: *)
(*Write*)


Options[PyWrite]=
  {
    Version->Automatic
    };
PyWrite[expr_, ops:OptionsPattern[]]:=
  PackageExceptionBlock["Kernel"]@
    Module[
        {
          pker = FindInstalledPython[OptionValue[Version]],
          cmd
          },
        If[AssociationQ@pker,
          Block[{$ToPythonStrings=True},
            cmd = TToPython@ToSymbolicPython[pker]
            ];
          WriteLine[pker["Process"], cmd],
          PackageRaiseException[Automatic,
            "Found kernel `` which is not a valid kernel",
            pker
            ]
          ]
        ]


(* ::Subsubsection::Closed:: *)
(*WriteString*)


Options[PyWriteString]=
  {
    Version->Automatic
    };
PyWriteString[cmd_, ops:OptionsPattern[]]:=
PackageExceptionBlock["Kernel"]@
  Module[
      {
        pker = FindInstalledPython[OptionValue[Version]]
        },
      If[AssociationQ@pker,
        WriteLine[pker["Process"], cmd],
        PackageRaiseException[Automatic,
          "Found kernel `` which is not a valid kernel",
          pker
          ]
        ]
      ]


(* ::Subsubsection::Closed:: *)
(*Read*)


Options[PyRead]=
  {
    Version->Automatic
    };
PyRead[ops:OptionsPattern[]]:=
PackageExceptionBlock["Kernel"]@
  Module[
      {
        pker = FindInstalledPython[OptionValue[Version]]
        },
      If[AssociationQ@pker,
        ReadString[pker["Process"], EndOfBuffer],
        PackageRaiseException[Automatic,
          "Found kernel `` which is not a valid kernel",
          pker
          ]
        ]
      ]


(* ::Subsubsection::Closed:: *)
(*ReadErr*)


Options[PyReadErr]=
  {
    Version->Automatic
    };
PyReadErr[ops:OptionsPattern[]]:=
PackageExceptionBlock["Kernel"]@
  Module[
      {
        pker = FindInstalledPython[OptionValue[Version]]
        },
      If[AssociationQ@pker,
        ReadString[ProcessConnection[pker["Process"], "StandardError"], EndOfBuffer],
        PackageRaiseException[Automatic,
          "Found kernel `` which is not a valid kernel",
          pker
          ]
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


Format[pt:PythonTraceback[ts_], StandardForm]:=
  Interpretation[
    Style[ts, Red],
    pt
    ]


(* ::Subsubsection::Closed:: *)
(*End*)


End[] (* `Private` *)

EndPackage[]
