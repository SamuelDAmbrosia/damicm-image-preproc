import argparse
import regex as re
import sys
import os
import inspect
import tabulate
import math

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../AutoAnalysis"))
import constants as c

class Image:

    #This object represents a processed image
    
    def __init__(self, header, outputs):
        """Initialize image object containing header and outputs"""
        
        self.header = header
        self.outputs = outputs
        
    def compare_noise(self):
        """Multiples noise by root(NDCMS) to compare noise of images with different skipping values"""
        
        if !(self.outputs(["skNoise"]) == -1):
            return self.outputs(["skNoise"]) * math.sqrt(self.header["NDCMS"])
        else:
            return self.outputs(["imgNoise"]) * math.sqrt(self.header["NDCMS"])