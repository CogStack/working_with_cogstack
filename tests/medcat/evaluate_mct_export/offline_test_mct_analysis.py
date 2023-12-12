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
from .test_mct_analysis import MEDCAT_EVAL_MCT_EXPORT_FOLDER, RESOURCE_DIR
sys.path.append(MEDCAT_EVAL_MCT_EXPORT_FOLDER)
# and now we can import from mct_analysis
from mct_analysis import MedcatTrainer_export

import unittest

MCT_EXPORT_JSON_PATH = os.path.join(RESOURCE_DIR, "offline", "MCT_Export_Anthony_v1.5.json")

MODEL_PACK_PATH = os.path.join(RESOURCE_DIR, "offline",
                            #    "trained_model_KCH_cn_only_23_11_27.zip")
                            #    "mc_modelpack_snomed_int_16_mar_2022_new.zip")
                            #    "20230227__kch_gstt_trained_model_494c3717f637bb89.zip")
                               "anthony_v1.5_model")


class MCTExportBasicTests(unittest.TestCase):
    report_path = 'mct_report.xlsx'

    @classmethod
    def setUpClass(cls) -> None:
        cls.export = MedcatTrainer_export([MCT_EXPORT_JSON_PATH, ], MODEL_PACK_PATH)

    def test_generate_report(self):
        self.export.generate_report(path=self.report_path)
        self.assertTrue(os.path.exists(self.report_path))
