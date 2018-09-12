# -*- coding: utf-8 -*-

import os, sys

path = ''
for dir in os.listdir("build"):
    for file in os.listdir(os.path.join("build", dir)):
        if file.endswith('.so'):
            path = os.path.join("build", dir)
            break
    if path:
        break

sys.path.insert(0, os.path.abspath(path))

import PJLinkNativeLibrary as pjs

print(pjs.Open)

argv = ["-linkmode", "launch", "-linkname", "/Applications/Mathematica.app/Contents/MacOS/WolframKernel"]
errMsgOut = [ "" ]
print(
    pjs.Open(4, argv, errMsgOut)
    )
