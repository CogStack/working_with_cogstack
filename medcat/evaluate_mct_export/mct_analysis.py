import json
import pandas as pd
import plotly.graph_objects as go
from medcat.cdb import CDB
from medcat.cat import CAT


class MedcatTrainer_export(object):
    """
    Class to analysis medcattrainer exports
    """


    def __init__(self, model_pack_path):
        """
        :param modelpack: Path to medcat modelpack
        """
        cat = CAT.load_model_pack(model_pack_path)

