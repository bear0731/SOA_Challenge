
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
sns.set_style('whitegrid')

file_path = '/Users/BF/Development/SOA/ilec-mort-appendices.xlsx'
output_dir = '/Users/BF/.gemini/antigravity/brain/85a2e587-29b3-481d-be0e-36b784671c33'

def load_sheet_robust(file_path, sheet_name):
    print(f"Loading {sheet_name}...")
    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=20)
    
    header_idx = None
    for idx, row in df_raw.iterrows():
        values = [str(x).strip().lower() for x in row.values if pd.notnull(x)]
        if any('issue age' == v for v in values):
             if any('duration' in v or '1-25' in str(row.values) for v in values):
                header_idx = idx
                break
    
    if header_idx is not None:
        return pd.read_excel(file_path, sheet_name=sheet_name, header=header_idx)
    return None

def main():
    # 1. Load F1
    df_f1 = load_sheet_robust(file_path, 'F1')
    if df_f1 is None:
        return
        
    df_male_amt = df_f1.iloc[:, 0:11].copy()
    df_male_amt = df_male_amt.dropna(subset=['Issue Age'])
    
    # DEBUG: Check duplicates
    if df_male_amt['Issue Age'].duplicated().any():
        print("Duplicates found in Issue Age:")
        print(df_male_amt[df_male_amt['Issue Age'].duplicated(keep=False)])
        
        # FIX: Remove 'Total' rows and duplicates
        df_male_amt = df_male_amt[~df_male_amt['Issue Age'].astype(str).str.contains('Total', case=False, na=False)]
        df_male_amt = df_male_amt.drop_duplicates(subset=['Issue Age'])
        print("Removed duplicates/Totals.")
    
    id_vars = ['Issue Age', 'Total', 'Claim Amts']
    # Filter only columns that exist
    id_vars = [c for c in id_vars if c in df_male_amt.columns]
    
    value_vars = [c for c in df_male_amt.columns if c not in id_vars]
    
    df_male_long = df_male_amt.melt(id_vars=['Issue Age'], value_vars=value_vars, 
                                    var_name='Duration_Bin', value_name='AE_Ratio')
    df_male_long['AE_Ratio'] = pd.to_numeric(df_male_long['AE_Ratio'], errors='coerce')
    
    # Plot
    plt.figure(figsize=(10, 6))
    pivot_table = df_male_long.pivot(index='Issue Age', columns='Duration_Bin', values='AE_Ratio')
    
    col_order = ['1', '2', '3', '4-5', '6-10', '11-15', '16-20', '21-25']
    col_order = [c for c in col_order if c in pivot_table.columns]
    pivot_table = pivot_table[col_order]
    
    sns.heatmap(pivot_table, annot=True, cmap='RdYlGn_r', fmt='.2f')
    plt.title('Male A/E Ratio by Issue Age and Duration (F1 Sheet)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'f1_heatmap.png'))
    print("Saved f1_heatmap.png")

if __name__ == "__main__":
    main()
