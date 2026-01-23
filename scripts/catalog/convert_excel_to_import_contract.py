import sys
print("Script start")
sys.stdout.flush()

import openpyxl
import os

def normalize_header(h):
    return str(h).strip().lower()

def safe_str(v):
    if v is None: return ""
    return str(v).strip()

def get_str_val(v):
    if v is None: return ""
    return str(v).strip()

def main(input_file, output_file):
    print(f"Reading {input_file}...")
    sys.stdout.flush()
    try:
        wb_in = openpyxl.load_workbook(input_file, data_only=True)
    except Exception as e:
        print(f"Error loading workbook: {e}")
        sys.exit(1)

    wb_out = openpyxl.Workbook()
    if 'Sheet' in wb_out.sheetnames:
        del wb_out['Sheet']

    print("Workbook loaded.")
    sys.stdout.flush()

    # --- 1. Tests Sheet ---
    if 'Tests' not in wb_in.sheetnames:
        print("FAIL: 'Tests' sheet missing")
        sys.exit(1)
    
    ws_tests_in = wb_in['Tests']
    ws_tests_out = wb_out.create_sheet("Tests")
    tests_headers = ["test_id", "test_code", "legacy_test_code", "test_name", "category", "sample_type", "price", "turnaround_time"]
    ws_tests_out.append(tests_headers)
    
    in_headers = [normalize_header(c.value) for c in ws_tests_in[1]]
    
    def get_col_idx(name, optional=False, headers=in_headers):
        try:
            return headers.index(name)
        except ValueError:
            if optional: return -1
            print(f"FAIL: Sheet missing column '{name}'")
            sys.exit(1)
            
    idx_tid = get_col_idx("test_id")
    idx_tcode = get_col_idx("test_code")
    idx_leg = get_col_idx("legacy_test_code", True)
    idx_name = get_col_idx("test_name")
    idx_cat = get_col_idx("category")
    idx_samp = get_col_idx("sample_type", True)
    idx_price = get_col_idx("price")
    idx_tat = get_col_idx("tat_hours")
    if idx_tat == -1: idx_tat = get_col_idx("turnaround_time", True)

    valid_test_ids = set()

    for row in ws_tests_in.iter_rows(min_row=2, values_only=True):
        if not row[idx_tid]: continue
        
        test_id = safe_str(row[idx_tid])
        valid_test_ids.add(test_id)
        
        test_code = row[idx_tcode]
        test_name = row[idx_name]
        category = row[idx_cat] if idx_cat != -1 and row[idx_cat] else "General"
        legacy = row[idx_leg] if idx_leg != -1 and row[idx_leg] else ""
        sample = row[idx_samp] if idx_samp != -1 and row[idx_samp] else "Serum"
        price = row[idx_price] if row[idx_price] is not None else 0
        tat = row[idx_tat] if idx_tat != -1 and row[idx_tat] else 24
        
        ws_tests_out.append([test_id, test_code, legacy, test_name, category, sample, price, tat])
    
    print(f"Processed {len(valid_test_ids)} tests.")

    # --- 2. Parameters Sheet (from ParameterMaster) ---
    ws_params_out = wb_out.create_sheet("Parameters")
    ws_params_out.append(["parameter_id", "parameter_name", "unit"])
    
    valid_param_ids = set()

    if 'ParameterMaster' in wb_in.sheetnames:
        ws_pm_in = wb_in['ParameterMaster']
        pm_headers = [normalize_header(c.value) for c in ws_pm_in[1]]
        
        p_idx_pid = get_col_idx("parameter_id", headers=pm_headers)
        p_idx_name = get_col_idx("parameter_name", headers=pm_headers)
        p_idx_unit = get_col_idx("unit", headers=pm_headers)
        
        for row in ws_pm_in.iter_rows(min_row=2, values_only=True):
            if not row[p_idx_pid]: continue
            pid = safe_str(row[p_idx_pid]).lower()
            name = row[p_idx_name]
            unit = row[p_idx_unit] if row[p_idx_unit] else ""
            
            if pid not in valid_param_ids:
                ws_params_out.append([pid, name, unit])
                valid_param_ids.add(pid)
    
    print(f"Processed {len(valid_param_ids)} parameters.")

    # --- 3. Mapping AND ReferenceRanges (from Parameters Sheet) ---
    ws_map_out = wb_out.create_sheet("Mapping")
    ws_map_out.append(["test_id", "parameter_id", "display_order", "reportable"])

    ws_rr_out = wb_out.create_sheet("ReferenceRanges")
    rr_out_headers = ["test_id", "parameter_id", "gender", "age_min", "age_max", "reference_min", "reference_max", "critical_low", "critical_high"]
    ws_rr_out.append(rr_out_headers)
    
    # Ranges count
    rr_count = 0
    
    if 'Parameters' in wb_in.sheetnames:
        ws_map_in = wb_in['Parameters']
        map_headers = [normalize_header(c.value) for c in ws_map_in[1]]
        
        m_idx_tid = get_col_idx("test_id", headers=map_headers)
        m_idx_pid = get_col_idx("parameter_id", headers=map_headers)
        m_idx_pname = get_col_idx("parameter_name", headers=map_headers)
        m_idx_ord = get_col_idx("display_order", headers=map_headers)
        
        # Range columns
        m_idx_rmin_m = get_col_idx("ref_min_male", True, headers=map_headers)
        m_idx_rmax_m = get_col_idx("ref_max_male", True, headers=map_headers)
        m_idx_rmin_f = get_col_idx("ref_min_female", True, headers=map_headers)
        m_idx_rmax_f = get_col_idx("ref_max_female", True, headers=map_headers)
        m_idx_clow = get_col_idx("critical_low", True, headers=map_headers)
        m_idx_chigh = get_col_idx("critical_high", True, headers=map_headers)
        
        row_count = 0
        for row in ws_map_in.iter_rows(min_row=2, values_only=True):
            if not row[m_idx_tid]: continue
            
            tid = safe_str(row[m_idx_tid])
            if tid not in valid_test_ids: continue

            # Parameter ID might be missing in 'Parameters' sheet if it's purely legacy
            # But inspect showed 'p1', 'p2'.
            pid_raw = row[m_idx_pid]
            pname = get_str_val(row[m_idx_pname])
            
            if pid_raw:
                pid = safe_str(pid_raw).lower()
            else:
                # If missing parameter_id, generate one or skip?
                # User says "Parameter model MUST have parameter_id".
                # If missing, we can't reliably map.
                # Just skip or warn.
                print(f"WARNING: Mapping missing parameter_id for Test {tid}, PName {pname}")
                continue
                
            order = row[m_idx_ord] if row[m_idx_ord] else 0
            
            # Ensure p_id in Parameters list
            if pid not in valid_param_ids:
                ws_params_out.append([pid, pname, ""])
                valid_param_ids.add(pid)
            
            ws_map_out.append([tid, pid, order, True])
            row_count += 1
            
            # Extract Reference Ranges
            clow = row[m_idx_clow] if m_idx_clow != -1 else None
            chigh = row[m_idx_chigh] if m_idx_chigh != -1 else None
            
            # Male
            rmin_m = row[m_idx_rmin_m] if m_idx_rmin_m != -1 else None
            rmax_m = row[m_idx_rmax_m] if m_idx_rmax_m != -1 else None
            
            # Female
            rmin_f = row[m_idx_rmin_f] if m_idx_rmin_f != -1 else None
            rmax_f = row[m_idx_rmax_f] if m_idx_rmax_f != -1 else None
            
            # Helper to add range
            def add_range(gender, rmin, rmax):
                # 0-120 years default
                ws_rr_out.append([tid, pid, gender, 0, 120, rmin, rmax, clow, chigh])
            
            has_male = (rmin_m is not None or rmax_m is not None)
            has_female = (rmin_f is not None or rmax_f is not None)
            
            if has_male and has_female:
                # Check if values are identical
                if rmin_m == rmin_f and rmax_m == rmax_f:
                    add_range("Both", rmin_m, rmax_m)
                    rr_count += 1
                else:
                    add_range("Male", rmin_m, rmax_m)
                    add_range("Female", rmin_f, rmax_f)
                    rr_count += 2
            elif has_male:
                add_range("Male", rmin_m, rmax_m) # Or Both? Safer to say Male if only male col pop?
                # Actually if only male is populated but female is empty, usually implies male-specific or female implies same?
                # Let's stick to Male.
                rr_count += 1
            elif has_female:
                add_range("Female", rmin_f, rmax_f)
                rr_count += 1
            
        print(f"Processed {row_count} mappings. extracted {rr_count} ranges.")
        
    wb_out.save(output_file)
    print(f"Success. Saved to {output_file}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
