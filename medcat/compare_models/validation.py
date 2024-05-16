from typing import Optional, Union, Set
import os
import glob


def _is_mct_export(file_path: str) -> bool:
    if "*" in file_path:
        nr_of_matching_files = len(list(glob.iglob(file_path)))
        print("GLOB w", nr_of_matching_files,  nr_of_matching_files > 0)
        return nr_of_matching_files > 0
    print("MCT EXPORT (no-glob?", os.path.exists(file_path), file_path.endswith(".json"))
    return os.path.exists(file_path) and file_path.endswith(".json")


def validate_input(model_path1: str, model_path2: str, documents_file: str,
                    cui_filter: Optional[Union[Set[str], str]],
                    supevised_train_comp: bool):
    if not os.path.exists(model_path1):
        raise ValueError(f"No model found at specified path (1st model): {model_path1}")
    if not is_medcat_model(model_path1):
        raise ValueError(f"Not a medcat model: {model_path1}")
    if not os.path.exists(model_path2):
        if supevised_train_comp and not _is_mct_export(model_path2):
            raise ValueError(f"No matching MCT export found for: {model_path2}")
        elif not supevised_train_comp:
            raise ValueError(f"No file found at specified path (2nd model): {model_path2}")
    if supevised_train_comp:
        if not os.path.isfile(model_path2) and not _is_mct_export(model_path2):
            raise ValueError(f"MCT export provided should be a file not a folder: {model_path2}")
        if not model_path2.lower().endswith(".json"):
            raise ValueError(f"MCT export expected in .json format, Got: {model_path2}")
    elif not is_medcat_model(model_path2):
        raise ValueError(f"Not a medcat model: {model_path2}")
    if cui_filter is not None:
        if isinstance(cui_filter, str):
            if not os.path.exists(cui_filter):
                raise ValueError(f"File passed as CUI filter does not exist: {cui_filter}")
    if not os.path.exists(documents_file):
        raise ValueError(f"No documents file found: {documents_file}")
    if not documents_file.lower().endswith(".csv"):
        raise ValueError(f"Expected a .csv file for documnets, got: {documents_file}")


def _is_medcat_model_folder(model_folder: str):
    # needs to have CDB and vocab
    cdb_path = os.path.join(model_folder, 'cdb.dat')
    vocab_path = os.path.join(model_folder, "vocab.dat")
    return ((os.path.exists(cdb_path) and os.path.isfile(cdb_path)) and
            (os.path.exists(vocab_path) and os.path.isfile(vocab_path)))


def is_medcat_model(model_path: str) -> bool:
    if os.path.isdir(model_path):
        return _is_medcat_model_folder(model_path)
    model_folder = model_path[:-len(".zip")]
    if os.path.exists(model_folder):
        # NOTE: if the model folder doesn't exist, it will
        #       be extracted upon loading the model
        return _is_medcat_model_folder(model_folder)
    # NOTE: this does not actually guarantee that it's a model pack
    #       but it would be outside the scope of this method
    #       to try and extract or list the contents
    return model_path.endswith(".zip")
