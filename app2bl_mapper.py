import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt

class App2BaselineMapper():
    """
    Reads-in baseline data (residing on a RDHPCS) filenames required for the Regression Test framework & map them to
    their corresponding UFS Application-to-Physics Suite combination. 
    
    """
    def __init__(self, appsphys2test_dir, baseline_df_dir, input_df_dir):
        self.appsphys2test_dir = appsphys2test_dir
        self.baseline_df_dir = baseline_df_dir
        self.input_df_dir = input_df_dir

    
    def save2pickle(self, data2save, fn):
        """
        Save data to pickle file.
        
        Args:
            data2save (dict, str, tuple, list, pd.DataFrame): Data to save.
            fn (str): Filename for pickle file. 
        
        Return : None
        
        """
        with open(fn + '.pkl', 'wb') as file:
            pickle.dump(data2save, file)
            
        return
    
    def read_pickle(self, fn):
        """
        Read data from pickle file.
        
        Args:
            fn (str): Filename of pickle file. 
        
        Return (dict, str, tuple, list, pd.DataFrame): Pickle file's data. 
        
        """
        with open(fn + '.pkl', 'rb') as file:
            data = pickle.load(file)
            
        return data
    
    def write_pickle(self, fn):
        """
        Write data to pickle file.
        
        Args:
            fn (str): Filename of pickle file. 
        
        Return (dict, str, tuple, list, pd.DataFrame): Pickle file's data. 
        
        """
        with open(fn + '.pkl', 'rb') as file:
            data = pickle.load(file)
            
        return data
    
    def get_bl_storage_size(self, merged_bl2test):
        """
        Get storage size by UFS application.
        
        Args:
            merged_bl2test (pd.DataFrame): Merged dataframes of the UFS application information derived from rt.conf to 
            the latest baseline data files found w/in RDHPC Orion on-prem disk.
        
        Return: None
        """
        
        # Extract data storage size reserved by each UFS component.
        baseline_sz_perapp2phys = pd.DataFrame(merged_bl2test.groupby(['UFS_App'])['Size (GB)'].sum())

        # Variation in storage size per input dataset per component.
        fig, ax = plt.subplots(figsize=(15,15))
        baseline_sz_perapp2phys.plot(kind='barh', legend = False, color= (0, 0.6, 0, 0), ax=ax, alpha=0.7, linewidth=6)

        # Set label style.
        ax.tick_params(axis='both', labelsize=14)
        ax.set_title('UFS Application vs Total Size of Latest Baseline Dataset Files (GB)\n', fontsize=16, fontweight='black', color = '#333F4B')
        ax.set_xlabel('\nSize (GB)', fontsize=16, fontweight='black', color='#333F4B')
        ax.set_ylabel(f'UFS Application\n', fontsize=16, fontweight='black', color='#333F4B')
        plt.tight_layout()
        
        return baseline_sz_perapp2phys

    