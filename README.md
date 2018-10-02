<a id="pjlink" style="width:0;height:0;margin:0;padding:0;">&zwnj;</a>

# PJLink

[![version](http://img.shields.io/badge/version-1.0.6-orange.svg)](https://github.com/b3m2a1/PJLink/master/PJLink/PacletInfo.m)  [![license](http://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

PJLink is a package developed to link python and Mathematica.  *It is currently python 3.3+ only* as it turns out to be more challenging to support legacy python2.7 as well in the C-interface than I would currently like, although it will likely be less difficult to do so in the python codebase.

---

<a id="installation" style="width:0;height:0;margin:0;padding:0;">&zwnj;</a>

# Installation

The easiest way to install PJLink is using a paclet server installation:

```mathematica
PacletInstall[
  "PJLink",
  "Site"->
    "http://www.wolframcloud.com/objects/b3m2a1.paclets/PacletServer"
  ]
```

If you've already installed it you can update using:

```mathematica
PacletUpdate[
  "PJLink",
  "Site"->
    "http://www.wolframcloud.com/objects/b3m2a1.paclets/PacletServer"
  ]
```

Alternately you can download this repo as a ZIP file and put extract it in  ```$UserBaseDirectory/Applications```

---

<a id="usage" style="width:0;height:0;margin:0;padding:0;">&zwnj;</a>

# Usage

Before anything else, we'll load the package:

```mathematica
<<PJLink`
```

To start you need to call  ```InstallPython``` to load a python runtime (the first time this is done it may be slow as it compiles the library PJLink uses for communication):

```mathematica
ker=InstallPython[];
```

After that you can evaluate python code as a string

```mathematica
PyEvaluateString["import numpy as np"];
PyEvaluateString["np.random.rand(5, 5, 5)"]~Short~3
```

    (*Out:*)
    
    {{{0.19340495587982665`,0.04333471882108819`,0.0793674077113492`,0.6746465215828963`,0.9128377509416972`},<<3>>,{0.36109338142334146`,0.44378058193673864`,<<19>>,<<21>>,0.5244287636275622`}},<<3>>,{<<1>>}}

You can also using the PJLink symbolic processing system to evaluate python code directly from Mathematica code. This is the best way to pass data into python:

```mathematica
With[{arr=RandomReal[{-1, 1}, {100, 100,100}]}, PyEvaluate[test=arr,  TimeConstraint->1]]//AbsoluteTiming//First
```

    (*Out:*)
    
    0.102152`

```mathematica
PyEvaluate[test]//Dimensions//AbsoluteTiming
```

    (*Out:*)
    
    {0.020897`,{100,100,100}}

Errors will be returned wrapped in  ```PythonTraceback``` :

```mathematica
PyEvaluate[nosym]
```

    (*Out:*)
    
    PythonTraceback["Traceback (most recent call last):\n  File \"~/Documents/Python/IDEA/PJLink/PJLink/KernelLink.py\", line 654, in __handleCallPacket\n    self.__callPython()\n  File \"/Users/Mark/Documents/Python/IDEA/PJLink/PJLink/KernelLink.py\", line 1003, in __callPython\n    res = self.__do_call_recursive(pkt)\n  File \"~/Documents/Python/IDEA/PJLink/PJLink/KernelLink.py\", line 959, in __do_call_recursive\n    res = eval(arg, self.__EXEC_ENV, self.__EXEC_ENV)\n  File \"<string>\", line 1, in <module>\nNameError: name 'nosym' is not defined\n"]

When done, call  ```ClosePython``` to clean up the runtime and close the link:

```mathematica
ClosePython[]
```

You can also use this package to communicate with Mathematica from Python as I detailed  [here](https://www.wolframcloud.com/objects/b3m2a1/home/pjlink-hooking-up-mathematica-and-python.html#main-content) .