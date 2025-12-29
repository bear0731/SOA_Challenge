# -*- coding: utf-8 -*-
"""
Deep inspection of all sheets to understand their structure for better visualization.
"""
import pandas as pd

FILE_PATH = '/Users/BF/Development/SOA/data/ilec-mort-appendices.xlsx'

xl = pd.ExcelFile(FILE_PATH)

for sheet in xl.sheet_names:
    print("\n" + "="*80)
    print("SHEET: {}".format(sheet))
    print("="*80)
    
    df = xl.parse(sheet, nrows=15)
    
    # Print first 15 rows to understand structure
    for i, row in df.iterrows():
        # Show row index and non-null values
        vals = [str(v) for v in row.values if pd.notna(v)]
        if vals:
            print("Row {}: {}".format(i, ' | '.join(vals[:5])))  # First 5 non-null values
