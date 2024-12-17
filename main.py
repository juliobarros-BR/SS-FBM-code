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
import matplotlib.font_manager as fm

# Add the font path explicitly
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
fm.fontManager.addfont(font_path)
prop = fm.FontProperties(fname=font_path)

# Set the font properties globally
plt.rcParams['font.family'] = prop.get_name()


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


plt.figure()
plt.plot(main_sim.History["Time"],main_sim.History["Total_strain"])
plt.savefig("result.png")

plt.figure()
plt.plot(main_sim.History["Time"],np.array(main_sim.History["Slip_strain"])/main_model.sys_var.get("N"))
plt.show()

        



