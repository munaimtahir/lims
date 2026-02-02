import pandas as pd
import sys

file_path = sys.argv[1]

xls = pd.ExcelFile(file_path)

for sheet_name in xls.sheet_names:
    print(f"\n--- Sheet: {sheet_name} ---")
    df = pd.read_excel(xls, sheet_name)
    print(f"Number of rows: {len(df)}")
    print("Head:")
    print(df.head())
    print("Tail:")
    print(df.tail())
    print(df.info())
