import os, sys
from PJLink import MathLinkEnvironment as Env

lib_root = Env.get_NativeLibrary_root()
try:
    math_link_key = os.environ["MATH_LINK_KEYS"]
    # math_link_key = None
except:
    math_link_key = os.environ["MATH_LINK_KEY"]
download_root = os.path.join(lib_root, "src", "MathLinkBinaries")
target_arch = Env.system_name()+("-x86-64" if Env.get_is_64_bit() else "")
target_bin_path = os.path.join(download_root, target_arch)

if not os.path.exists(target_bin_path):

    url_root = "https://www.wolframcloud.com/objects/b3m2a1/MathLinkBinaries"
    url_targ = url_root+"/"+target_arch+".zip"+"?_key="+math_link_key

    print("Downloading MathLink archives from: {}".format(url_targ))
    try:
        import wget
        from zipfile import ZipFile

        tmp_ = os.path.join(lib_root, target_arch+".zip")
        wget.download(url_targ, tmp_)
        zipfile = ZipFile(tmp_)
        zipfile.extractall(download_root)
        # os.remove(tmp_) # AppVeyor doesn't like this?

    except ImportError:
        from io import BytesIO
        from zipfile import ZipFile
        from urllib.request import urlopen
        import ssl

        context = ssl._create_unverified_context()
        resp = urlopen(url_targ, context=context)
        zipfile = ZipFile(BytesIO(resp.read()))
        zipfile.extractall(download_root)

from PJLink.PJLinkNativeLibrary.load_lib import _get_lib_dir_loc, libdata

try:
    _get_lib_dir_loc() # just to set _NATIVE_LIBRARY_SHARED_OBJECT
    so_file = libdata._NATIVE_LIBRARY_SHARED_OBJECT
    if not libdata._NATIVE_LIBRARY_EXISTS:
        raise Exception("Failed to build...?")
    new_dir = os.path.join(lib_root, target_arch)
    if not os.path.exists(new_dir):
        os.mkdir(new_dir)
    new_so = os.path.join(new_dir, os.path.basename(so_file))
    print(so_file, new_so)
    os.rename(so_file, new_so)

    import PJLink.PJLinkNativeLibrary.lib as lib

except:
    import traceback as tb
    tb.print_exc()
    sys.exit(1)
else:
    sys.exit(0)