from typing import Optional, Union, Set
import os


def validate_input(model_path1: str, model_path2: str, documents_file: str,
                    cui_filter: Optional[Union[Set[str], str]],
                    supevised_train_comp: bool):
    if not os.path.exists(model_path1):
        raise ValueError(f"No model found at specified path (1st model): {model_path1}")
    if not os.path.exists(model_path2):
        path_type = "2nd model" if not supevised_train_comp else "MCT export"
        raise ValueError(f"No file found at specified path ({path_type}): {model_path2}")
    if supevised_train_comp:
        if not os.path.isfile(model_path2):
            raise ValueError(f"MCT export provided should be a file not a folder: {model_path2}")
        if not model_path2.lower().endswith(".json"):
            raise ValueError(f"MCT export expected in .json format, Got: {model_path2}")
    if cui_filter is not None:
        if isinstance(cui_filter, str):
            if not os.path.exists(cui_filter):
                raise ValueError(f"File passed as CUI filter does not exist: {cui_filter}")
