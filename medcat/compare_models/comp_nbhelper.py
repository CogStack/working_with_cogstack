from ipyfilechooser import FileChooser
from ipywidgets import widgets
from IPython.display import display
import os
from typing import List


from compare import get_diffs_for
from output import parse_and_show, show_dict_deep, compare_dicts


_def_path = '../../models/modelpack'
_def_path = _def_path if os.path.exists(_def_path) else '.'


class NBComparer:

    def __init__(self, model_path_1: str, model_path_2: str,
                 documents_file: str, is_mct_export_compare: bool,
                 cui_filter: str, filter_children: bool) -> None:
        self.model_path_1 = model_path_1
        self.model_path_2 = model_path_2
        self.documents_file = documents_file
        self.is_mct_export_compare = is_mct_export_compare
        self.cui_filter = cui_filter
        self.filter_children = filter_children
        self._run_comparison()

    def _run_comparison(self):
        (self.cdb_comp, self.tally1, self.tally2, self.ann_diffs) = get_diffs_for(
            self.model_path_1, self.model_path_2, self.documents_file,
            cui_filter=self.cui_filter, include_children_in_filter=self.filter_children,
            supervised_train_comparison_model=self.is_mct_export_compare)

    def show_all(self):
        parse_and_show(self.cdb_comp, self.tally1, self.tally2, self.ann_diffs)

    def show_per_document(self, limit: int = -1, print_delimiter: bool = True):
        if limit >= 0:
            keys = list(self.ann_diffs.per_doc_results.keys())[0:limit]
        else:
            keys = self.ann_diffs.per_doc_results.keys()
        for key in keys:
            if print_delimiter:
                print('='*20,f'\n{key}', f'\n{"="*20}')
            show_dict_deep(self.ann_diffs.per_doc_results[key].nr_of_comparisons)

    def diffs_to_csv(self, file_path: str) -> None:
        self.ann_diffs.to_csv(file_path)

    def compare_for_cui(self, cui: str, include_children: int = 2) -> None:
        per_cui1 = self.tally1.get_for_cui(cui, include_children=include_children)
        per_cui2 = self.tally2.get_for_cui(cui, include_children=include_children)
        compare_dicts(per_cui1, per_cui2)

    def show_docs(self, docs: List[str], show_delimiter: bool = True,
                  omit_identical: bool = True):
        for doc_name, pair in self.ann_diffs.iter_ann_pairs(docs=docs, omit_identical=omit_identical):
            if show_delimiter:
                print('='*20,f'\n{doc_name} ({pair.comparison_type})', f'\n{"="*20}')
            # NOTE: if only one of the two has an annotation, the other one will be None
            #       the following will deal with that automatically, though
            compare_dicts(pair.one, pair.two)


class NBInputter:
    models_overall_title = "Models and data"
    mc1_title = "Choose model 1"
    mc2_title = "Choose model 2 (or an MCT export)"
    docs_title = "Choose the documents file (.csv with 'text' field)"
    mct_export_title = "Is the 2nd path an MCT export (instead of a model)?"
    cui_filter_title_overall = "CUI Filter"
    cui_filter_title_file_chooser = "Choose file with comma-separated CUIs"
    cui_filter_title_text = "List comma-separated CUIs"
    cui_children_title = "How many layers of children of concepts to include?"

    def __init__(self) -> None:
        self.model1_chooser = FileChooser(_def_path)
        self.model2_chooser = FileChooser(_def_path)
        self.documents_chooser = FileChooser(".")
        self.ckbox = widgets.Checkbox(description="MCT export compare")

        self.cui_filter_chooser = FileChooser(".", description="The CUI filter file")
        self.cui_filter_box = widgets.Textarea(description="CUI list")
        self.cui_children = widgets.IntText(description="Children", value=-1)

    def show_all(self):
        model_choosers = widgets.VBox([
            widgets.HTML(f"<h2>{self.models_overall_title}</h2>"),
            widgets.VBox([widgets.Label(self.mc1_title), self.model1_chooser]),
            widgets.VBox([widgets.Label(self.mc2_title), self.model2_chooser]),
            widgets.VBox([widgets.Label(self.docs_title), self.documents_chooser]),
            widgets.VBox([widgets.Label(self.mct_export_title), self.ckbox])
        ])

        cui_filter = widgets.VBox([
            widgets.HTML(f"<h2>{self.cui_filter_title_overall}</h2>"),
            widgets.VBox([widgets.Label(self.cui_filter_title_file_chooser), self.cui_filter_chooser]),
            widgets.VBox([widgets.Label(self.cui_filter_title_text), self.cui_filter_box]),
            widgets.VBox([widgets.Label(self.cui_children_title), self.cui_children])
        ])

        # Combine all sections into a main VBox
        main_box = widgets.VBox([
            model_choosers,
            cui_filter
        ])
        display(main_box)


    def _get_params(self):
        model_path_1 = self.model1_chooser.selected
        model_path_2 = self.model2_chooser.selected
        documents_file = self.documents_chooser.selected
        is_mct_export_compare = self.ckbox.value
        if not is_mct_export_compare:
            print(f"For models, selected:\nModel1: {model_path_1}\nModel2: {model_path_2}"
                f"\nDocuments: {documents_file}")
        else:
            print(f"Selected:\nModel: {model_path_1}\nMCT export: {model_path_2}"
                f"\nDocuments: {documents_file}")
        # CUI filter
        cui_filter = None
        filter_children = None
        if self.cui_filter_chooser.selected:
            cui_filter = self.cui_filter_chooser.selected
        elif self.cui_filter_box.value:
            cui_filter = self.cui_filter_box.value
        if self.cui_children.value and self.cui_children.value > 0:
            filter_children = self.cui_children.value
        print(f"For CUI filter, selected:\nFilter: {cui_filter}\nChildren: {filter_children}")
        return (model_path_1, model_path_2, documents_file, is_mct_export_compare, cui_filter, filter_children)

    def get_comparison(self) -> NBComparer:
        return NBComparer(*self._get_params())
