#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 10:03:06 2024

@author: jortiz
"""

import ast
import numpy as np
from Model_class import Model
from Sim_class import Simulate
import matplotlib.pyplot as plt
import pandas as pd
import argparse


# file_path = "input_dubois_opt1.txt"

# strength_model = Model(file_path)

# strength_model.max_slip = 1

# strength_sim = Simulate(strength_model)

# load_st , disp_st = strength_sim.run_strength()

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filename", help="Input file name")
args = parser.parse_args()
file_path=args.filename
if file_path==None:
    file_path="input_unitless.txt"

main_model = Model(file_path)

main_sim = Simulate(main_model)

main_sim.run()

main_sim.History["Time"][0]=0


df = pd.DataFrame({
    "Slip": main_sim.History["Slip_strain"],
    "Macro": main_sim.History["Total_strain"],
    "time": main_sim.History["Time"],
    })

df.to_csv("time.csv")


df_valendo=pd.read_csv("/local/home/jortiz/ownCloud - Julio OrtizAmandodeBarros (jortiz@student.ethz.ch)@polybox.ethz.ch/FBM/Results/Results/Fitting_dubois/Default Dataset.csv")

plt.figure()
plt.plot(main_sim.History["Time"],main_sim.History["Total_strain"])
plt.plot(df_valendo["x-1"],df_valendo["y-1"])
plt.savefig("result.png")

plt.figure()
plt.plot(main_sim.History["Time"],np.array(main_sim.History["Slip_strain"])/40000)

# plt.xlim(15,35)
# plt.ylim(0.000025,0.00003)
        


