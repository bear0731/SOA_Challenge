import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

# Set plot style
plt.style.use('ggplot')
plt.rcParams['figure.figsize'] = (12, 6)

FILE_PATH = '/Users/BF/Development/SOA/data/ilec-mort-appendices.xlsx'
OUTPUT_DIR = '/Users/BF/Development/SOA/data/plots'
REPORT_FILE = '/Users/BF/Development/SOA/data/appendices_analysis.md'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_header_row(df, keywords):
    """
    Finds the index of the row that contains at least one of the keywords
    AND has at least 3 non-NaN values (to avoid title rows).
    """
    for idx, row in df.iterrows():
        # Check for sufficient non-null values
        if row.count() < 3:
            continue
            
        # Convert row to string and check for keywords
        row_str = ' '.join(row.astype(str).values).lower()
        for kw in keywords:
            if kw.lower() in row_str:
                return idx
    return None

def deduplicate_columns(columns):
    """
    Renames duplicate columns by appending context (e.g. Count vs Amount) if possible, 
    or just numbering them.
    """
    new_cols = []
    seen = {}
    
    # First pass: identify duplicates
    counts = {}
    for col in columns:
        col = str(col).strip()
        counts[col] = counts.get(col, 0) + 1
        
    # Second pass: rename
    current_counts = {}
    for i, col in enumerate(columns):
        col = str(col).strip()
        if counts[col] > 1:
            # Try to infer context from previous columns
            prev_col = str(columns[i-1]).strip() if i > 0 else ""
            
            if 'Death' in prev_col or 'Count' in prev_col:
                new_col = f"{col} (Count)"
            elif 'Amount' in prev_col:
                new_col = f"{col} (Amount)"
            else:
                current_counts[col] = current_counts.get(col, 0) + 1
                new_col = f"{col}.{current_counts[col]}"
        else:
            new_col = col
        new_cols.append(new_col)
    return new_cols

def analyze_sheet(sheet_name, df_raw):
    print(f"Analyzing {sheet_name}...")
    
    # 1. Identify Header
    keywords = ['Attained Age', 'Issue Age', 'Duration', 'Observation Year', 
                'Face Amount', 'Plan', 'Smoker', 'Gender', 'Risk Class',
                'Insurance Plan', 'Calendar Year']
    
    header_idx = find_header_row(df_raw, keywords)
    
    if header_idx is None:
        print(f"  Warning: Could not find header row for {sheet_name}")
        return None
    
    # 2. Extract Data
    df = df_raw.iloc[header_idx+1:].copy()
    
    # Set and clean headers
    raw_headers = df_raw.iloc[header_idx].tolist()
    cleaned_headers = deduplicate_columns(raw_headers)
    df.columns = cleaned_headers
    
    # Identify Key Column (x-axis)
    key_col = None
    for col in df.columns:
        if any(kw.lower() in col.lower() for kw in keywords):
            key_col = col
            break
            
    if key_col is None:
        key_col = df.columns[0]
        
    print(f"  Identified primary key column: {key_col}")
    
    # Clean Data
    df = df[df[key_col].notna()]
    df = df[~df[key_col].astype(str).str.contains('Total', case=False, na=False)]
    df = df[~df[key_col].astype(str).str.contains('Source', case=False, na=False)]
    
    # 3. Identify Metrics
    # Prioritize Amount based metrics
    ae_cols = [c for c in df.columns if 'A/E' in c or 'Ratio' in c]
    ae_amount_col = next((c for c in ae_cols if 'Amount' in c), None)
    if not ae_amount_col and ae_cols:
        ae_amount_col = ae_cols[-1] 
        
    amount_exposed_cols = [c for c in df.columns if 'Exposure Amount' in c or ('Amount' in c and 'Exposed' in c)]
    if not amount_exposed_cols:
         amount_exposed_cols = [c for c in df.columns if 'Amount' in c and 'Face' not in c and 'A/E' not in c]

    # Convert to numeric
    cols_to_plot = []
    if ae_amount_col: cols_to_plot.append(ae_amount_col)
    if amount_exposed_cols: cols_to_plot.append(amount_exposed_cols[0])
    
    for col in cols_to_plot:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # 4. Generate Visualizations
    insights = []
    plot_files = []
    
    # Ensure x-axis is valid
    df = df.copy() # Defragment
    try:
        df['numeric_key'] = pd.to_numeric(df[key_col])
        df = df.sort_values('numeric_key')
        x_vals = df['numeric_key']
    except:
        x_vals = df[key_col].astype(str)
        # If too many categories, limit them?
        if len(x_vals) > 50:
             # Just take every nth label for clarity if strings
             pass

    # Graph 1: A/E Ratio
    if ae_amount_col and df[ae_amount_col].notna().any():
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(x_vals)), df[ae_amount_col], marker='o', linestyle='-', linewidth=2, color='#2ca7cd')
        plt.xticks(range(len(x_vals)), x_vals, rotation=45, ha='right')
        plt.title(f'{sheet_name}: {ae_amount_col} vs {key_col}')
        plt.xlabel(key_col)
        plt.ylabel(ae_amount_col)
        plt.axhline(1.0, color='gray', linestyle='--', alpha=0.5)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        filename = f"{sheet_name}_AE_Ratio.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        plt.savefig(filepath)
        plt.close()
        plot_files.append(filename)
        
        avg = df[ae_amount_col].mean()
        insights.append(f"Average {ae_amount_col}: {avg:.3f}")

    # Graph 2: Exposure Amount
    exp_col = amount_exposed_cols[0] if amount_exposed_cols else None
    if exp_col and df[exp_col].notna().any():
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(x_vals)), df[exp_col], alpha=0.6, color='#2c3e50')
        plt.xticks(range(len(x_vals)), x_vals, rotation=45, ha='right')
        plt.title(f'{sheet_name}: {exp_col} Distribution')
        plt.xlabel(key_col)
        plt.ylabel(exp_col)
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        
        filename = f"{sheet_name}_Exposure.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        plt.savefig(filepath)
        plt.close()
        plot_files.append(filename)
        
        total_exp = df[exp_col].sum()
        insights.append(f"Total {exp_col}: {total_exp:,.0f}")

    return {
        'sheet': sheet_name,
        'key_dimension': key_col,
        'plot_files': plot_files,
        'insights': insights
    }

def main():
    try:
        xl = pd.ExcelFile(FILE_PATH)
        sheet_names = xl.sheet_names
        print(f"Found sheets: {sheet_names}")
        
        report_content = "# ILEC Mortality Appendices Analysis Report\n\n"
        
        for sheet in sheet_names:
            if sheet == 'Summary':
                continue # Skip summary tab for automated uniform analysis for now
            
            try:
                # Read a chunk to find header
                # We assume header is within first 20 rows
                df_raw = xl.parse(sheet, nrows=100) 
                
                result = analyze_sheet(sheet, df_raw)
                
                if result:
                    report_content += f"## Sheet: {result['sheet']}\n"
                    report_content += f"**Key Dimension:** {result['key_dimension']}\n\n"
                    
                    if result['insights']:
                        report_content += "**Key Metrics:**\n"
                        for ins in result['insights']:
                            report_content += f"- {ins}\n"
                    
                    report_content += "\n**Visualizations:**\n"
                    for plot in result['plot_files']:
                        report_content += f"![{plot}](plots/{plot})\n"
                    report_content += "\n---\n"
                    
            except Exception as e:
                print(f"Error analyzing sheet {sheet}: {e}")
                report_content += f"## Sheet: {sheet}\n\nError analyzing content: {e}\n\n---\n"

        with open(REPORT_FILE, 'w') as f:
            f.write(report_content)
            
        print(f"Analysis complete. Report saved to {REPORT_FILE}")
        
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
