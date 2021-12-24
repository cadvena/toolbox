import toolbox, importlib, pathlib
from toolbox.file_util import ez_ftp

# module
# ##############################################################################
# print("module's package:", toolbox.__loader__.name)
print("module's name (i.e, package.module_name):", ez_ftp.__loader__.name)
print("module's short name:", ez_ftp.__loader__.name.split('.')[-1])
print("module's name:", toolbox.file_util.ez_ftp.__loader__.name)
print("module's short name:", toolbox.file_util.ez_ftp.__loader__.name.split('.')[-1])
print("module's package:", toolbox.file_util.ez_ftp.__loader__.name.split('.')[0])

def this_module_name(short_name: bool = False) -> str:
    """
    By default, module.name includes the package name, like "toolbox.file_util.ez_ftp"
    To include only the last component, e.g "ez_ftp", set short_name = True.
    :param short_name: By default, module.name includes the package name, like
                        "toolbox.file_util.ez_ftp".  To include only the last
                        component, e.g "ez_ftp", set short_name = True.
    :return: the name of this module (str)
    """
    try:
        mod_name = __loader__.name
    except:
        mod_name = pathlib.Path(__file__).stem
    short = __loader__.name.split('.')[-1]
    if __name__ == '__main__':
        result = __loader__.name
    elif __name__ == 'builtins':
        # Do I want to do something special in this case?
        result = __name__
    else:
        result = __name__
    if short_name:
        result = result.split('.')[-1]
    return result

# import package by name
print("import package by name...")
from importlib import import_module
import_module("toolbox.swiss_army", "toolbox")
# import_module("swiss_army", "toolbox")  # <-- will NOT work
# import_module("swiss_army", toolbox)  # <-- will NOT work
import_module("toolbox.swiss_army")

# current module
# ##############################################################################

print('\n' + '#'*60, '\n# Module NAME\n' +  '#'*60)
print("current module's name :", pathlib.Path(__loader__.path).stem)
print("current module's name via __file__ :", pathlib.Path(__file__).stem)
print("current module's name (alt method):", __loader__.name)  # may not be what you want if

print("current module's package:", __loader__.name.split('.')[0])
print("current module's file path:", pathlib.Path(__file__).resolve())
print("current module's  file path via __loader__.path", __loader__.path)
print("current module's  file path via __file__", __file__)
print("current module's folder:", pathlib.Path(__file__).parent.resolve())
print("current module's folder (alternate method):", pathlib.Path(__loader__.path).parent.resolve())

print("current module's __loader__ object", __loader__)


pathlib.Path(__file__).parent.resolve()
