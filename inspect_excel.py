import pandas as pd
import sys

try:
    file_path = "LIMS_TestCatalog_MVP_FINAL (1).xlsx"
    # Load the excel file
    xl = pd.ExcelFile(file_path)
    
    print(f"Sheet names: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet, nrows=0)
        print(f"\n--- Sheet: {sheet} ---")
        print(f"Columns: {list(df.columns)}")
        
except Exception as e:
    print(f"Error reading excel: {e}")
