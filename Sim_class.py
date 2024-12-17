#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 10:25:24 2024

@author: jortiz
"""


import ast
import numpy as np
import os
import copy
import time

class Simulate:
    def __init__(self, model):
        self.model = model
        self.current_time = 0
        self.current_moist = 0
        self.current_load = 0
        
        
        if not model.sys_var["has_moist"] and not model.sys_var["has_load"]:
            self.moist_sequence, self.load_sequence, self.time_sequence = self.create_sim_sequence(model.sys_var["cycles_pre_load"], model.sys_var["cycles_loaded"], model.sys_var["cycles_unload"], model.sys_var["period"])
        else:
            self.moist_sequence, self.load_sequence, self.time_sequence = self.get_from_data_file(model.sys_var["moisture_df"],model.sys_var["load_df"])
            
        self.load_sequence = list(np.array(self.load_sequence)[:]*1)
        self.time_sequence = list(np.array(self.time_sequence)[:]*1)
        
        self.History = {
                        "Total_strain": [],
                        "Slip_strain": [],
                        "Time": [],
                        "Avalanche_plus": [],
                        "Avalanche_minus": [],
                        "Slip_load": [],
                        "Slip_moist": [],
                        "Slip_creep": [],
                        "Creep": [],
                        "Elastic": [],
                        "Number_of_fibers": [],
                        "Load": [],
                        "Moisture": []
                        }
        
    def update_history(self):
    # Create a dictionary with the subarrays to be updated
        self.History["Total_strain"].append(self.model.total_strain)
        self.History["Slip_strain"].append(self.model.total_slip)
        # print("current time",self.current_time)
        self.History["Time"].append(self.current_time)
        self.History["Load"].append(self.current_load)
        self.History["Moisture"].append(self.current_moist)
        # self.History["Avalanche_plus"].append(self.total_strain)
        # self.History["Avalanche_minus"].append(self.total_strain)
        # self.History["Slip_load"].append(self.total_strain)
        # self.History["Slip_moist"].append(self.total_strain)
        # self.History["Slip_creep"].append(self.total_strain)
        # self.History["Creep"].append(self.total_strain)
        # self.History["Elastic"].append(self.total_strain)
        # self.History["Number_of_fibers"].append(self.total_strain)

        return
        
    def create_sim_sequence(self,cycles_pre_load, cycles_loaded, cycles_unload, period):
        sequence_moist = []
        sequence_load = []
        sequence_time = []
        
        sequence_moist.extend([0])
        sequence_load.extend([0])
        sequence_time.extend([0])
        
        for _ in range(cycles_pre_load):
            sequence_moist.extend([0, 0, 1, 0])
            sequence_load.extend([0, 0, 0, 0])
            
            last_time=sequence_time[-1]
            sequence_time.extend([last_time, last_time + period, last_time + 2*period, last_time + 3*period])
    
        # Loading:
            
        sequence_moist.append(0)
        sequence_load.append(1)
        sequence_time.append(sequence_time[-1])
    
        for _ in range(cycles_loaded):
            sequence_moist.extend([0, 0, 1, 0])
            sequence_load.extend([1, 1, 1, 1])
            last_time=sequence_time[-1]
            sequence_time.extend([last_time, last_time + period, last_time + 2*period, last_time + 3*period])
            
        # Unloading:
        sequence_moist.append(0)  
        sequence_load.append(0)
        sequence_time.append(sequence_time[-1])
    
        for _ in range(cycles_unload):
            sequence_moist.extend([0, 0, 1, 0])
            sequence_load.extend([0, 0, 0, 0])
            last_time=sequence_time[-1]
            sequence_time.extend([last_time, last_time + period, last_time + 2*period, last_time + 3*period])
    
        return sequence_moist, sequence_load, sequence_time
    
    def get_from_data_file(self,moisture_file_path,load_file_path):
        # Read moisture data file
        moisture_data_1 = np.loadtxt(moisture_file_path+".csv", delimiter=',', skiprows=1)
        moisture_time = np.sort(moisture_data_1[:, 0])  # Assuming time is in the second column
        moisture_values = moisture_data_1[:, 1]  # Assuming moisture values are in the first column
            # Read load data file
        load_data = np.loadtxt(load_file_path+".csv", delimiter=',', skiprows=1)
        load_time = load_data[:, 0]  # Assuming time is in the second column
        load_values = load_data[:, 1]  # Assuming load values are in the first column
        # Merge time arrays
        total_time = np.sort(np.concatenate((moisture_time, load_time)))
        moisture_array = []
        load_array = []
        for time_entry in total_time:
               # Find the index of the current time entry in moisture_time
               moisture_index = np.where(moisture_time == time_entry)[0]
               if moisture_index.size > 0:
                   # If the time entry is in moisture_time, use the corresponding value
                   moisture_array.append(moisture_values[moisture_index[0]])
               else:
                   # If the time entry is missing, repeat the previous entry
                   moisture_array.append(moisture_array[-1] if moisture_array else 0)

               # Find the index of the current time entry in load_time
               load_index = np.where(load_time == time_entry)[0]

               if load_index.size > 0:
                   # If the time entry is in load_time, use the corresponding value
                   load_array.append(load_values[load_index[0]])
               else:
                   # If the time entry is missing, repeat the previous entry
                   load_array.append(load_array[-1] if load_array else 0)
        return moisture_array, load_array, total_time
    
    def run(self):
        # print(self.time_sequence)
        for time_index, time_value in enumerate(self.time_sequence):
            self.current_time = time_value            
            self.current_load = self.load_sequence[time_index]
            self.current_moist = self.moist_sequence[time_index]
            prev_moist = self.moist_sequence[time_index-1]
            next_moist = self.moist_sequence[time_index]
            prev_load = self.load_sequence[time_index-1]
            next_load = self.load_sequence[time_index]
            
            # print(prev_moist,next_moist,prev_load,next_load)
            try:
                d_moisture = next_moist - prev_moist
                d_load = next_load - prev_load
            except:
                continue
            # print(time_index, time_value, self.load_sequence)
            if d_moisture:
                # print("moist",self.model.total_strain)
                # Moisture is changing, optimize the variable accordingly
                self.complete_interval(
                    prev_load,
                    prev_moist,
                    next_moist,  # Adjust the interval as needed
                    0
                )

            if d_load:
                # print("load",self.model.total_strain,prev_load,next_load)
                # Load is changing, optimize the variable accordingly
                self.complete_interval(
                    prev_moist,
                    prev_load,
                    next_load,  # Adjust the interval as needed                    
                    1
                )
            else:
                # print("time")
                self.evolve_time([self.time_sequence[time_index-1], time_value], 100)
            
            # print(next_load)
            # # Run the optimize_fibers function after each iteration
            # self.optimize_fibers(self.model, self.local_thresholds, self.fail_limit)
            self.update_history()
            if not np.sum(self.model.local_intact):
                break
        return
    
    
    def complete_interval(self, fixed, initial, final, flag):
        current_interval = [initial, final]
        tot_fin = final
        direction = np.sign(final-initial)
        # print(current_interval)
        count=0
        while direction*current_interval[0] != direction*final and count<1000:
            # if count > 50:
                # print(whole.total_slip - halves.total_slip,whole.total_slip,current_interval,direction)
            # Check if the whole interval has an acceptable slip strain
            whole, halves = self.is_acceptable_interval(current_interval, fixed, flag)
            # print(whole.total_slip)
            # print(whole.total_slip,halves.total_slip)
            if np.abs(whole.total_slip) - np.abs(halves.total_slip) <= np.abs(1*whole.total_slip) :
                # Move to the next interval
                print("Im here")
                current_interval = [current_interval[1],final]
                self.model = copy.deepcopy(whole)
            else:
                # If not, halve the interval
                print("Im there")
                current_interval = [current_interval[0], current_interval[1] - (current_interval[1]-current_interval[0]) / 2]
            if count==999:
                print("stuck here")
                self.model = copy.deepcopy(whole)
                break
            count += 1
        # print(final,tot_fin)
        # print(self.model)
        return 
    
    def is_acceptable_interval(self, interval, fixed, flag):
        initial, final = interval
        # print(interval)
        whole_model = copy.deepcopy(self.model)
        halves_model = copy.deepcopy(self.model)
        # print(whole_model,halves_model)
        
        # flag = 0 if load change, flag = 1 if moisture change
        if not flag:
            load = fixed
            load_half = fixed
            moist = final
            moist_half = final-(final - initial)/2
        else:
            moist = fixed
            moist_half = fixed
            load = final
            load_half = final-(final-initial)/2
        # print("values", moist, moist_half, load, load_half)    
        # Complete interval in one step
        # print(load,load_half,moist,moist_half)
        whole_model = self.run_interval(whole_model,moist, load)
        
        # Complete interval in two steps
        halves_model = self.run_interval(halves_model, moist_half, load_half)
        halves_model = self.run_interval(halves_model, moist, load)
    
        # Calculate the slip strain from two halves
        
        
        return whole_model, halves_model


    def run_interval(self, aux_model, moist_value, load_value):
        
        aux_model.normalized_moisture = (moist_value)
        
        aux_model.load = load_value
        

        aux_model.update_total_strain()
        
        aux_model.slip_avalanche()
        
        aux_model.update_slip_strain()
        
        aux_model.update_total_strain()
           
        return aux_model
    
    
    def evolve_time(self, interval,steps):
        # print(interval)
        dt = (interval[1]-interval[0])/steps
        self.model.update_total_strain()
        self.model.normalized_moisture = (self.current_moist)
        self.current_time = interval[0]
        current_J = (self.model.J_min +self.model.J_lin_coeff*(self.current_moist))
        current_D = (self.model.D_min +self.model.D_lin_coeff*(self.current_moist))
        # print("computing strain", current_J,current_D,self.current_moist)
        # print(interval)
        if dt*steps < 0.005:
            return
        else:
            for i in np.arange(steps):
                
                # print(self.model.local_creep)
                forces = (self.model.total_strain - self.model.local_slip - self.model.local_creep - self.model.sys_var.get("alpha")*(self.current_moist))/current_D
               
                self.model.local_creep += (forces*current_J - self.model.local_creep)*(1-np.exp(-dt/self.model.sys_var.get("tau")))
                self.model.slip_avalanche()
                self.model.update_slip_strain()
                self.model.update_total_strain()
                self.update_history()
                self.current_time += dt
            return
    
    def run_strength(self):
        self.model.load = 0
        while np.sum(self.model.local_intact) != 0:
            self.model.load += 0.001
            self.model.update_total_strain()
            self.model.slip_avalanche()
            self.model.update_slip_strain()
            self.model.update_total_strain()
            self.update_history()
        
        
        return self.model.load, self.model.total_strain
        
        
        
        
        
    
            
            
