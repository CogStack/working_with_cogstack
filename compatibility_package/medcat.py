import sys
import os
import importlib

import medcat2
import medcat2.storage.serialisers
import medcat2.utils.legacy.convert_cdb as convert_cdb
import medcat2.utils.legacy.convert_vocab as convert_vocab

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


manual_changes = {
    "medcat.tokenizers.meta_cat_tokenizers": "medcat2.components.addons.meta_cat.mctokenizers.tokenizers",
    "medcat.cdb_maker": "medcat2.model_creation.cdb_maker",
    "medcat.utils.meta_cat": "medcat2.components.addons.meta_cat",
    "medcat.meta_cat": "medcat2.components.addons.meta_cat.meta_cat",
    "medcat.config_meta_cat": "medcat2.config.config_meta_cat",
}


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

for module_name, replacement_module_name in manual_changes.items():
    sys.modules[module_name] = SubmoduleProxy(replacement_module_name)  # type: ignore

# add automatic vocab / CDB conversion
_orig_deserialise = medcat2.storage.serialisers.deserialise


def deserialise_with_legacy_conversion(
        folder_path: str,
        ignore_folders_prefix: set[str] = set(),
        ignore_folders_suffix: set[str] = set(),
        **init_kwargs):
    if not os.path.isdir(folder_path):
        if folder_path.endswith("cdb.dat"):
            print("Trying to legacy convert CDB from", folder_path)
            return convert_cdb.get_cdb_from_old(folder_path)
        elif folder_path.endswith("vocab.dat"):
            print("Trying to legacy convert Vocab from", folder_path)
            return convert_vocab.get_vocab_from_old(folder_path)
    return _orig_deserialise(
        folder_path, ignore_folders_prefix, ignore_folders_suffix, **init_kwargs)


medcat2.storage.serialisers.deserialise = deserialise_with_legacy_conversion
