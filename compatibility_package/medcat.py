import sys
import importlib
import medcat2

# Copy all attributes from medcat2 to this module
for attr in dir(medcat2):
    if not attr.startswith('__'):
        globals()[attr] = getattr(medcat2, attr)


# Set up submodule redirections
class SubmoduleProxy:
    def __init__(self, target_module_name):
        self.target_module_name = target_module_name

    def __getattr__(self, name):
        return getattr(importlib.import_module(self.target_module_name), name)


# For each submodule in medcat2, create a proxy in sys.modules
for module_name in list(sys.modules.keys()):
    if (module_name.startswith('medcat2.') and
            not module_name.startswith('medcat.')):
        submodule_name = module_name.replace('medcat2.', 'medcat.', 1)
    elif module_name == 'medcat2':
        submodule_name = 'medcat'
    else:
        continue
    sys.modules[submodule_name] = SubmoduleProxy(module_name)  # type: ignore
