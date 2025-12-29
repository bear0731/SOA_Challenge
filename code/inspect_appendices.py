import pandas as pd
import os

file_path = '/Users/BF/Development/SOA/data/ilec-mort-appendices.xlsx'

try:
    xl = pd.ExcelFile(file_path)
    
    # Sample a diverse set of sheets
    sample_sheets = ['Summary', 'A', 'E1', 'G', 'OA1']
    
    for sheet in sample_sheets:
        if sheet in xl.sheet_names:
            print("\n--- Reading Sheet: {} ---".format(sheet))
            # Read header area
            df_head = xl.parse(sheet, nrows=10)
            print(df_head)
            
            # Try to find where the actual table starts
            # Usually looking for a row with multiple non-NaN values
            
except Exception as e:
    print("Error reading Excel file: {}".format(e))
