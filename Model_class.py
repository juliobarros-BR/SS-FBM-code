#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 14:09:15 2024

@author: jortiz
"""

import ast
import numpy as np
import os
import time


class Model:
    def __init__(self, file_path):
        
        self.sys_var = self.initialize_variables_from_file(file_path)
        
        # Initialize global properties
        
        self.total_slip     = 0
        self.total_strain   = 0
        self.N = self.sys_var.get('N')
        self.max_slip = int(-np.log(self.sys_var.get('failure_limit'))*self.sys_var.get('decay'))
        self.normalized_moisture = 0
        self.load = 0

        # Initialize local properties (for each fiber)
        self.slip_th        = np.zeros(self.N)
        self.slip_count     = np.zeros(self.N)
        self.local_slip     = np.zeros(self.N)
        self.local_creep    = np.zeros(self.N)
        self.local_stress   = np.zeros(self.N)
        self.local_intact   = np.ones(self.N)

        
        np.random.seed(self.sys_var.get('seed'))
        self.threshold = np.random.weibull(self.sys_var.get('m_Weibull'),self.N)*self.sys_var.get('lambda_Weibull')+self.sys_var.get("init_th")
        
        
        
        
        # Linear fitting for compliances between the driest and most moist states
        
        self.D_min = self.sys_var.get('D_d')
        self.D_lin_coeff = self.sys_var.get('D_w') - self.sys_var.get('D_d')
        
        self.J_min = self.sys_var.get('J_d')
        self.J_lin_coeff = self.sys_var.get('J_w') - self.sys_var.get('J_d')
        
  
    def initialize_variables_from_file(self, file_path):
        variables = {}
        has_moisture_data = False
        has_load_data = False
        with open(file_path, 'r') as file:
            for line in file:
                # Remove leading and trailing whitespaces
                line = line.strip()

                # Skip empty lines or lines starting with '#' (comments)
                if not line or line.startswith('#'):
                    continue

                # Split the line into variable and value using '=' as delimiter
                variable, value_str = map(str.strip, line.split('=', 1))
                # print(variable,value_str)
                # Check if the line starts with "moisture_data"
                if variable == "moisture_df" and value_str:
                    has_moisture_data = True

                # Check if there's anything after the "=" sign for "load_data"
                elif variable == "load_df" and value_str:
                    has_load_data = True


                # Use ast.literal_eval to safely evaluate the value string
                try:
                    if os.path.isfile(value_str):
                        with open(value_str, 'r') as file_content:
                            value = file_content.read()
                    else:
                        # Use ast.literal_eval to safely evaluate other expressions
                        value = ast.literal_eval(value_str)
                except (SyntaxError, ValueError):
                    # If not a file path and not a literal expression, treat it as a string
                    value = value_str

                # Store the variable and its initialized value in the dictionary
                variables[variable] = value
        # print(has_moisture_data,has_load_data)
        variables["has_moist"] = has_moisture_data
        variables["has_load"] = has_load_data

        return variables    
        
    def update_slip_strain(self):
        self.total_slip     = np.sum(self.local_slip)
        return
    
    def update_total_strain(self):
        
        self.total_strain =  (self.total_slip + np.sum(self.local_creep))/(np.sum(self.local_intact)) + ((self.D_min +self.D_lin_coeff*self.normalized_moisture)*self.load )+ self.sys_var.get("alpha")*self.normalized_moisture
        # print("computing strain",self.normalized_moisture,self.load,self.sys_var.get("alpha"),self.J_min,self.J_lin_coeff,self.total_strain)
        return
    
    def get_compliance(self):
        return 

    
    
    def slip_avalanche(self):
        self.update_slip_strain()
        self.update_total_strain()
        
        idx_reverse = np.ones(self.N)
        idx_reverse[np.where(self.local_slip > self.total_strain)] = -1
        
        degrad_th = self.threshold*np.exp(-self.slip_count/self.sys_var.get('decay'))
        wet_sc = (1+(self.sys_var.get('wet_scale')-1)*self.normalized_moisture)
        reverse_sc = (1+(self.sys_var.get('reverse_scale')-1)*(1-idx_reverse)/2)
        
        idx_slip = np.where(np.abs(self.total_strain - self.local_slip)*self.local_intact > 
                            degrad_th*
                            wet_sc*
                            reverse_sc) 
        
        i = 0
        while len(idx_slip[0]) and i-100:
            
            
            
            self.local_slip[idx_slip] += (degrad_th[idx_slip]*
                                          wet_sc*
                                          reverse_sc[idx_slip]*
                                            (idx_reverse[idx_slip]))
            
            self.slip_count[idx_slip] += 1
            self.local_intact[np.where(self.slip_count > self.max_slip)] = 0
            self.update_slip_strain()
            self.update_total_strain()
            
            idx_reverse = np.ones(self.N)
            idx_reverse[np.where(self.local_slip > self.total_strain)] = -1
            
            degrad_th = self.threshold*np.exp(-self.slip_count/self.sys_var.get('decay'))
            wet_sc = (1+(self.sys_var.get('wet_scale')-1)*self.normalized_moisture)
            reverse_sc = (1+(self.sys_var.get('reverse_scale')-1)*(1-idx_reverse)/2)
            
            idx_slip = np.where(np.abs(self.total_strain - self.local_slip)*self.local_intact > 
                                degrad_th*
                                wet_sc*
                                reverse_sc) 
            
        return 
        
    # @property()
    def local_non_slip(self):
        return self.total_strain - self.local_slip
    
    # def find_slip_idx(self):
    # # For example, you might define bundle_strain as the sum of slip_th and local_creep
    # bundle_strain = my_model.slip_th + my_model.local_creep

    # # Compute the absolute difference between local_slip and bundle_strain
    # diff = np.abs(my_model.local_slip - bundle_strain)

    # # Identify indices where the difference is higher than local_thresholds
    # high_threshold_indices = np.where(diff > local_thresholds)[0]

    # # Categorize the differences into two cases based on local_slip
    # higher_than_bundle = np.where(my_model.local_slip > bundle_strain)
    # lower_than_bundle = np.where(my_model.local_slip < bundle_strain)

    # return high_threshold_indices, higher_than_bundle, lower_than_bundle

