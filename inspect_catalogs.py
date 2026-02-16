import pandas as pd
import os

files = [
    "lims-backend/LIMS_TestCatalog_IMPORT_READY.xlsx",
    "lims-backend/test_catalog.xlsx"
]

for file_path in files:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
        
    print(f"\n--- Inspecting {file_path} ---")
    try:
        xls = pd.ExcelFile(file_path)
        print(f"Sheets: {xls.sheet_names}")
        
        for sheet in xls.sheet_names:
            print(f"\nSheet: {sheet}")
            df = pd.read_excel(file_path, sheet_name=sheet)
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {len(df)}")
            print(df.head(3).to_string())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
