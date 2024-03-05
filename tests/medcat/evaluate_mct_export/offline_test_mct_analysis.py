"""This module is meant to be tested offline (i.e not in a GitHub actions settings).
The main reason is the access to various models it requires.
"""
import os
import sys


# because this project isn't (at least of of writing this)
# set up as a python project, there are no __init__.py
# files in each folder
# as such, in order to gain access to the relevant module,
# I'll need to add the path manually
from .test_mct_analysis import (MEDCAT_EVAL_MCT_EXPORT_FOLDER, RESOURCE_DIR, MCT_EXPORT_JSON_PATH,
                                BaseMCTExportTests)
sys.path.append(MEDCAT_EVAL_MCT_EXPORT_FOLDER)
# and now we can import from mct_analysis
from mct_analysis import MedcatTrainer_export


MODEL_PACK_PATH = os.path.join(RESOURCE_DIR, "offline",
                               "medmen_wstatus_2021_oct.zip")


class MCTExportBasicTests(BaseMCTExportTests):
    report_path = 'mct_report.xlsx'

    @classmethod
    def setUpClass(cls) -> None:
        cls.export = MedcatTrainer_export([MCT_EXPORT_JSON_PATH, ], MODEL_PACK_PATH)

    # these would need a CAT instance
    def test_can_full_annotation_df(self):
        full_ann_df = self.export.full_annotation_df()
        self.assertNonEmptyDataframe(full_ann_df)

    def test_can_meta_anns_concept_summary(self):
        meta_anns_summary_df = self.export.meta_anns_concept_summary()
        # this will be empty since I don't think I have anything
        # of note regarding meta annotations
        self.assertIsNotNone(meta_anns_summary_df)

    def test_generate_report(self):
        self.export.generate_report(path=self.report_path)
        self.assertTrue(os.path.exists(self.report_path))
