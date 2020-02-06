import argparse
import regex as re
import sys
import os
import inspect
import tabulate

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../AutoAnalysis"))
import constants as c

class Image:

    #This object represents a processed image
    
    def __init__(self, header, outputs):
        self.header = header
        self.outputs = outputs