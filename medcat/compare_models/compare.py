from typing import List, Tuple, Dict, Set, Optional, Union, Iterator
from functools import partial
import glob

from medcat.cat import CAT

import pandas as pd
import tqdm
import tempfile
import os

from compare_cdb import compare as compare_cdbs, CDBCompareResults
from compare_annotations import ResultsTally, PerAnnotationDifferences
from output import parse_and_show
from cmp_utils import SaveOptions
from validation import validate_input



def load_documents(file_name: str) -> Iterator[Tuple[str, str]]:
    with open(file_name) as f:
        df = pd.read_csv(f, names=["id", "text"])
    if df.iloc[0].id == "id" and df.iloc[0].text == "text":
        # removes the header
        # but also messes up the index a little
        df = df.iloc[1:, :]
    yield from df.itertuples(index=False)


def do_counting(cat1: CAT, cat2: CAT,
                ann_diffs: PerAnnotationDifferences) -> ResultsTally:
    def cui2name(cat, cui):
        if cui in cat.cdb.cui2preferred_name:
            return cat.cdb.cui2preferred_name[cui]
        all_names = cat.cdb.cui2names[cui]
        # longest anme
        return sorted(all_names, key=lambda name: len(name), reverse=True)[0]
    res1 = ResultsTally(pt2ch=_get_pt2ch(cat1), cat_data=cat1.cdb.make_stats(),
                        cui2name=partial(cui2name, cat1))
    res2 = ResultsTally(pt2ch=_get_pt2ch(cat2), cat_data=cat2.cdb.make_stats(),
                        cui2name=partial(cui2name, cat2))
    for per_doc in tqdm.tqdm(ann_diffs.per_doc_results.values()):
        res1.count(per_doc.raw1)
        res2.count(per_doc.raw2)
    return res1, res2


def _get_pt2ch(cat: CAT) -> Optional[Dict]:
    return cat.cdb.addl_info.get("pt2ch", None)


def get_per_annotation_diffs(cat1: CAT, cat2: CAT, documents: Iterator[Tuple[str, str]],
                             show_progress: bool = True,
                             keep_raw: bool = True,
                             ) -> PerAnnotationDifferences:
    pt2ch1: Optional[Dict] = _get_pt2ch(cat1)
    pt2ch2: Optional[Dict] = _get_pt2ch(cat2)
    temp_file = tempfile.NamedTemporaryFile()
    save_opts = SaveOptions(use_db=True, db_file_name=temp_file.name,
                            clean_callback=temp_file.close)
    pad = PerAnnotationDifferences(pt2ch1=pt2ch1, pt2ch2=pt2ch2,
                                   model1_cuis=set(cat1.cdb.cui2names),
                                   model2_cuis=set(cat2.cdb.cui2names),
                                   keep_raw=keep_raw,
                                   save_options=save_opts)
    for doc_id, doc in tqdm.tqdm(documents, disable=not show_progress):
        pad.look_at_doc(cat1.get_entities(doc), cat2.get_entities(doc), doc_id, doc)
    pad.finalise()
    return pad


def load_cui_filter(filter_file: str) -> Set[str]:
    with open(filter_file) as f:
        str_list = f.read().split(',')
    return set(item.strip() for item in str_list)


def _add_all_children(cat: CAT, cui_filter: Set[str], include_children: int) -> None:
    if include_children <= 0:
        return
    if "pt2ch" not in cat.cdb.addl_info:
        return
    pt2ch = cat.cdb.addl_info["pt2ch"]
    children = set(ch for cui in cui_filter for ch in pt2ch.get(cui, []))
    if include_children > 1:
        _add_all_children(cat, children, include_children=include_children-1)
    cui_filter.update(children)


def load_and_train(model_pack_path: str, mct_export_path: str) -> CAT:
    cat = CAT.load_model_pack(model_pack_path)
    # NOTE: Allowing mct_export_path to contain wildcat ("*").
    #       And in such a case, iterating over all matching files
    if "*" not in mct_export_path:
        cat.train_supervised_from_json(mct_export_path)
    else:
        for file in glob.glob(mct_export_path):
            cat.train_supervised_from_json(file)
    return cat


def get_diffs_for(model_pack_path_1: str,
                  model_pack_path_2: str,
                  documents_file: str,
                  cui_filter: Optional[Union[Set[str], str]] = None,
                  show_progress: bool = True,
                  include_children_in_filter: Optional[int] = None,
                  supervised_train_comparison_model: bool = False,
                  keep_raw: bool = True,
                  ) -> Tuple[CDBCompareResults, ResultsTally, ResultsTally, PerAnnotationDifferences]:
    validate_input(model_pack_path_1, model_pack_path_2, documents_file, cui_filter, supervised_train_comparison_model)
    documents = load_documents(documents_file)
    if show_progress:
        print("Loading [1]", model_pack_path_1)
    cat1 = CAT.load_model_pack(model_pack_path_1)
    if show_progress:
        print("Loading [2]", model_pack_path_2)
    if not supervised_train_comparison_model:
        cat2 = CAT.load_model_pack(model_pack_path_2)
    else:
        if show_progress:
            print("Reloading model pack 1", model_pack_path_1)
            print("And subsequently training on", model_pack_path_2)
            print("This may take a while, depending on the amount of "
                  "data is being trained on")
        cat2 = load_and_train(model_pack_path_1, model_pack_path_2)
    if show_progress:
        print("Per annotations diff finding")
    if cui_filter:
        if isinstance(cui_filter, str):
            cui_filter = load_cui_filter(cui_filter)
        if show_progress:
            print("Applying filter to CATs:", len(cui_filter), 'CUIs')
        if include_children_in_filter:
            if show_progress:
                print("Adding all children of", include_children_in_filter,
                      "or lower level from first model")
            _add_all_children(cat1, cui_filter, include_children_in_filter)
            if show_progress:
                print("After adding children from 1st model have a total of",
                      len(cui_filter), "CUIs")
            _add_all_children(cat2, cui_filter, include_children_in_filter)
            if show_progress:
                print("After adding children from 2nd model have a total of",
                      len(cui_filter), "CUIs")
        cat1.config.linking.filters.cuis = cui_filter
        cat2.config.linking.filters.cuis = cui_filter
    ann_diffs = get_per_annotation_diffs(cat1, cat2, documents, keep_raw=keep_raw)
    if show_progress:
        print("Counting [1&2]")
    res1, res2 = do_counting(cat1, cat2, ann_diffs)
    if show_progress:
        print("CDB compare")
    cdb_diff = compare_cdbs(cat1.cdb, cat2.cdb)
    return cdb_diff, res1, res2, ann_diffs


def main(mpn1: str, mpn2: str, documents_file: str):
    cdb_diff, res1, res2, ann_diffs = get_diffs_for(mpn1, mpn2, documents_file, show_progress=False)
    print("Results:")
    parse_and_show(cdb_diff, res1, res2, ann_diffs)


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])