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
PythonObject::usage="A little head for holding references to python objects";


(* ::Subsubsection::Closed:: *)
(* Package*)


BeginPackage["`Package`"];

$PackageDirectory::usage="The directory for the project";

$DefaultPythonKernel::usage="The default kernel for evaluations";
$PythonKernels::usage="A listing of the configured python kernels";

CallPythonPacket::usage="A packet of info for python on what to call";

EndPackage[];


(* ::Subsubsection:: *)
(*TypeHints*)


BeginPackage["`TypeHints`"];

$TypeHints::usage="The replacement rules used by AddTypeHints";
AddTypeHints::usage="AddTypeHints[expr] Adds type hints to expr that python can use";
PackedArrayInfo::usage="A typehint added by AddTypeHints";
ImageArrayInfo::usage="A typehint added by AddTypeHints";
SparseArrayInfo::usage="A typehint added by AddTypeHints";
RegisterTypeHint::usage="Registers a new typehint for the typehint framework";
LoadTypeHints::usage="Loads typehints into the typehint framework";

EndPackage[];


(* ::Subsubsection:: *)
(*Objects*)


$ObjectTable::usage="The object table for python objects";
PythonNew::usage="Makes a new python object";
PythonObjectMutate::usage="MutationHandler for python objects";


(* ::Subsubsection:: *)
(*SymbolicPython*)


Internal`WithLocalSettings[
  BeginPackage["`SymbolicPython`"];
  System`Private`NewContextPath@
    Join[
      $ContextPath,
      {
        $Context//StringReplace["SymbolicPython"->"TypeHints"],
        $Context//StringDelete["SymbolicPython`"]
        }
      ],
  Get@FileNameJoin@{DirectoryName@$InputFileName, "SymbolicPython.wl"},
  System`Private`RestoreContextPath[];
  EndPackage[];
  ];
BeginPackage["`SymbolicPython`Package`"];
EndPackage[];


(* ::Subsubsection::Closed:: *)
(*Exceptions*)


Internal`WithLocalSettings[
  BeginPackage["`Exceptions`"];
  System`Private`NewContextPath@
    Join[
      $ContextPath,
      {
        $Context//StringDelete["Exceptions`"]
        }
      ],
  Get@FileNameJoin@{DirectoryName@$InputFileName, "Exceptions.wl"},
  System`Private`RestoreContextPath[];
  EndPackage[]
  ]


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


$PackageDirectory = Nest[DirectoryName, $InputFileName, 2];
pjlinkDir = FileNameJoin@{$PackageDirectory, "PJLink"};
mathematicaDir = FileNameJoin@{$PackageDirectory, "Mathematica"};

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
      "DebugLevel"->0,
      "LogFile"->None
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
        lname = 
          Replace[
            OptionValue["LinkName"], 
            Except[String]:>"PJLink+"<>RandomChoice[Alphabet[], 8]
            ],
        proc = OptionValue[ProcessObject],
        failed = False,
        failed2 = True,
        errorMsg
      },
      CheckAbort[
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
                "--log=\"``\""~TemplateApply~
                  Replace[OptionValue["LogFile"],
                    {
                      File[f_]|f_String?(StringLength[#]>0&):>ExpandFileName@f,
                      _:>""
                      }
                    ],
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
            failed=True,
            pyKer["Process"] = proc;
            AppendTo[$PythonKernels[version], pyKer];
            If[!AssociationQ@$DefaultPythonKernel, $DefaultPythonKernel=pyKer];
            LinkWrite[pyKer["Link"],  InputNamePacket["In[1]:="]]
            ]
          ];
        failed2 = failed || pyEvalPacket[link, CallPacket[1, "'Initializing'"], 3]=!="Initializing";
        If[failed2,
          errorMsg = 
            Quiet[ReadString[ProcessConnection[proc, "StandardError"], EndOfBuffer]];
          ClosePython[version];
          If[StringQ@errorMsg && StringLength@errorMsg > 0,
            Block[{$MessagePrePrint=Identity},
              PackageRaiseException[Automatic,
                "Failed to start python process for python executable ``. Got message:\n\n``",
                pyExe,
                PythonTraceback[errorMsg]
                ]
              ],
            PackageRaiseException[Automatic,
              "Failed to start kernel for python executable ``",
              pyExe
              ]
            ]
          ];
        pyKer,
        If[failed2,
          errorMsg = 
            Quiet[ReadString[ProcessConnection[proc, "StandardError"], EndOfBuffer]];
          ClosePython[version];
          If[StringQ@errorMsg && StringLength@errorMsg > 0,
            Block[{$MessagePrePrint=Identity},
              PackageRaiseException[Automatic,
                "Failed to start python process for python executable ``. Got message:\n\n``",
                pyExe,
                PythonTraceback[errorMsg]
                ]
              ],
            PackageRaiseException[Automatic,
              "Failed to start kernel for python executable ``",
              pyExe
              ]
            ]
          ];
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
  Module[{pkt = packet, to = Quantity[timeout, "Seconds"], res, resRest},
    If[SameQ[LinkWrite[link, pkt], $Failed], Return[$Failed]];
    res = TimeConstrained[LinkRead[link, HoldComplete], timeout];
    resRest = Flatten@Reap[While[LinkReadyQ[link], Sow@LinkRead[link, HoldComplete]]][[2]];
    If[Length[resRest]==0,
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
      sequenceResult,

      Switch[#,
        HoldComplete @ EvaluatePacket @ _,
          pkt = ReturnPacket[CheckAbort[res[[1, 1]], $Aborted]],
        HoldComplete @ ReturnPacket @ _,
          res[[1, 1]],
        _,
          ReleaseHold[res]
        ]&/@Flatten@{res, resRest}
      ]
    ];


(* ::Subsubsection::Closed:: *)
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
    With[
      {
        es = 
          Quiet@ReadString[
            ProcessConnection[pker["Process"], "StandardError"], 
            EndOfBuffer
            ],
        os =
          Quiet@ReadString[
            ProcessConnection[pker["Process"], "StandardOutput"],
            EndOfBuffer
            ]
       },
      (*Echo[os];*)
      ClosePython[version];
      If[StringQ@es && StringLength@es>0,
        Block[{$MessagePrePrint=Identity},
          PackageRaiseException[Automatic,
            "Kernel `` for version `` has died with traceback:\n\n``",
            HoldForm@pker, (*HoldForm here is a hack because PackageRaiseException is buggy*)
            version,
            PythonTraceback[es]
            ]
          ],
        PackageRaiseException[Automatic,
          "Kernel `` for version `` has died",
          HoldForm@pker,
          version
          ]
        ]
      ],
    $Aborted
    ];
cleanUpEnv[_, _, p_]:=p


(* ::Subsubsection:: *)
(*preprocessExpr*)


registerHintingRule[hints_, expr_, head_]:=
  With[{h=Hash[expr], e=expr},
    hints[head[h]]=e;
    PyVerbatim[head[h]]
    ];
registerHintingRule~SetAttributes~HoldFirst;


preprocessExpr[expr_, head_]:=
  Module[{hints = <||>, held = Hold[expr]},
    held = held /. (Replace[Values@$TypeHints, 
      {
        (a_ :> (h:With|Module|Block)[v_,Verbatim[Condition][b_, c_]]):>(
          a:>
            h[
              v,
              With[{rule=registerHintingRule[hints, b, head]},
                Condition[rule, c]
                ]
             ]
          ),
        (a_ :> Verbatim[Condition][b_, c_]):>(
          a:>
            With[{cc=c, rule=If[c, registerHintingRule[hints, b, head]]},
              Condition[rule, cc]
              ]
          ),
        (a_ :> b_):>
          (
            a:>
              RuleCondition[registerHintingRule[hints, b, head], True]
            )
        },
      {1}
      ]);
    {hints, held}
    ];
preprocessExpr~SetAttributes~HoldFirst


(* ::Subsubsection:: *)
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
        to = If[NumericQ@OptionValue[TimeConstraint], OptionValue[TimeConstraint], 10],
        hints,
        prexpr,
        typeHinted
      },
      If[AssociationQ@pker,
        {hints, prexpr} = preprocessExpr[expr, typeHinted];
        sym = ToPython[ToSymbolicPython@@prexpr];
        If[OptionValue@"EchoSymbolicForm", Echo@sym];
        sym = sym /. hints;
        link = pker["Link"];
        cleanUpEnv[
          pker, 
          OptionValue[Version],
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
            cmd = ToPython@ToSymbolicPython[pker]
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
(*LoadTypeHints*)


encoderDir=FileNameJoin@{mathematicaDir, "Encoders"};


LoadTypeHints[]:=
  Module[{cachedContext=$Context},
    Internal`WithLocalSettings[
      System`Private`NewContextPath@{"System`", "PJLink`", "PJLink`TypeHints`"};
      $Context="PJLink`TypeHints`Private`",
      $TypeHints=
        Merge[
          {
            $TypeHints,
            AssociationMap[
              Get@FileNameJoin@{encoderDir, #<>".wl"}&, 
              FileBaseName/@FileNames["*.wl", encoderDir]
              ]
            },
          Last
          ],
      System`Private`RestoreContextPath[];
      $Context=cachedContext;
      ]
    ]


(* ::Subsubsection::Closed:: *)
(*$TypeHints*)


(*$TypeHints//Clear*)


If[!AssociationQ@$TypeHints,
  $TypeHints = <||>;
  LoadTypeHints[]
  ]


(* ::Subsubsection::Closed:: *)
(*AddTypeHints*)


AddTypeHints[eval_, level_:{0}] :=
  Replace[eval, Values@$TypeHints, level];


(* ::Subsubsection::Closed:: *)
(*RegisterTypeHint*)


Options[RegisterTypeHint]=
  {
    "Save"->True
    };
RegisterTypeHint[name_, hint:_Rule|_RuleDelayed, ops:OptionsPattern[]]:=
  Module[{contextMarks=Internal`$ContextMarks},
    Internal`WithLocalSettings[
      Internal`$ContextMarks=False,
      $TypeHints[name]=hint;
      If[OptionValue["Save"],
        Export[FileNameJoin@{encoderDir, name<>".wl"}, hint]
        ],
      Internal`$ContextMarks = contextMarks
      ]
    ];


(* ::Subsubsection::Closed:: *)
(*PythonTraceback*)


Format[pt:PythonTraceback[ts_], StandardForm]:=
  Interpretation[
    Style[ts, Red],
    pt
    ]


(* ::Subsubsection::Closed:: *)
(*pythonAttachSymbol*)


(* ::Text:: *)
(*Currently this doesn't handle multiple runtimes so I'll need to make it do so.*)


pythonAttachSymbol[obj:PythonObject[id_Integer, class_String, addr_Integer]]:=
  With[{sym=ToExpression["PJLink`Objects`$PythonObject$"<>ToString[id]]},
    $ObjectTable[id]=Prepend[obj, sym];
    sym["$ID"]=id;
    sym
    ]


(* ::Subsubsection::Closed:: *)
(*pythonWrapSymbol*)


pythonWrapSymbol[sym_]:=
  (
    SetAttributes[sym, HoldAllComplete];
    sym[(meth:_[___])[args___]]:=
      sym[meth][args];
    sym[(meth_[args___])]:=
      Null
    )


(* ::Subsubsection::Closed:: *)
(*PythonNew*)


PythonNew[expr_, args:___]:=
  With[{obj = PyEvaluate[ObjectHandler.new[expr[args]]]},
    pythonAttachSymbol[obj]
    ]


(* ::Subsubsection::Closed:: *)
(*PythonObject*)


(* ::Text:: *)
(*Need to think a bit about how I want to handle this...*)


PythonObject~SetAttributes~HoldAllComplete


Language`SetMutationHandler[PythonObject, PythonObjectMutationHandler]


(* ::Subsubsection::Closed:: *)
(*End*)


End[] (* `Private` *)

EndPackage[]
