import pandas as pd

FILE_PATH = '/Users/BF/Development/SOA/data/ilec-mort-appendices.xlsx'

xl = pd.ExcelFile(FILE_PATH)
df = xl.parse('A', nrows=20)
print(df)
print("\nPossible header row candidates:")
for i, row in df.iterrows():
    print(f"Row {i}: {row.tolist()}")
