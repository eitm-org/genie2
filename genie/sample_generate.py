import os
import glob
import argparse
from omegaconf import OmegaConf

from genie.sample_unconditional import run_unconditional
from genie.sample_scaffold import run_scaffold

def generate(config_file):

    conf = OmegaConf.load(config_file)

    if conf.genie2.model_type == 'scaffold':
        run_scaffold(config_file)
    elif conf.genie2.model_type == 'unconditional':
        # unconditional generatiom
        run_unconditional(config_file)