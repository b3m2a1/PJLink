import os, sys
from PJLink import MathLinkEnvironment as Env

lib_root = Env.get_NativeLibrary_root()
math_link_key = os.environ["MATH_LINK_KEYS"]
download_root = os.path.join(lib_root, "src", "MathLinkBinaries")
target_arch = Env.system_name()+("-x86-64" if Env.get_is_64_bit() else "")
target_bin_path = os.path.join(download_root, target_arch)

if not os.path.exists(target_bin_path):
    from io import BytesIO
    from zipfile import ZipFile
    from urllib.request import urlopen
    import ssl

    url_root = "https://www.wolframcloud.com/objects/b3m2a1/MathLinkBinaries"
    url_targ = url_root+"/"+target_arch+".zip"+"?_key="+math_link_key

    context = ssl._create_unverified_context()
    resp = urlopen(url_targ, context=context)
    zipfile = ZipFile(BytesIO(resp.read()))
    zipfile.extractall(download_root)

from PJLink.PJLinkNativeLibrary.load_lib import _get_lib_dir_loc, _NATIVE_LIBRARY_SHARED_OBJECT

try:
    _get_lib_dir_loc() # just to set _NATIVE_LIBRARY_SHARED_OBJECT
    so_file = _NATIVE_LIBRARY_SHARED_OBJECT
    new_dir = os.path.join(lib_root, target_arch)
    if not os.path.exists(new_dir):
        os.mkdir(new_dir)
    new_so = os.path.join(new_dir, os.path.basename(so_file))
    print(so_file, new_so)
    os.rename(so_file, new_so)
except:
    import traceback as tb
    tb.print_exception()
    sys.exit(1)
else:
    sys.exit(0)