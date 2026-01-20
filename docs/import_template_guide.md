# LIMS Import Template Guide

This guide details the expected structure for the Excel import file used to populate the laboratory test catalog. The file must contain the following sheets with the specified columns.

## General Rules
1. **File Format**: `.xlsx` (Excel Workbook).
2. **Sheet Names**: Must match exactly (`Parameters`, `Tests`, `Mapping`, `ReferenceRanges`).
3. **IDs**: `test_id` (integer) and `parameter_id` (string) are authoritative. Do not duplicate them.
4. **Order**: Ensure `Parameters` and `Tests` sheets are populated before `Mapping` or `ReferenceRanges`.

---

## Sheet 1: `Parameters`
Defines the global list of analytes/parameters available in the system.

| Column | Header Name | Type | Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| A | `parameter_id` | String | **Yes** | Unique code for the parameter (e.g., `p1`, `HGB`). Primary Key. |
| B | `parameter_name` | String | **Yes** | Human-readable name (e.g., "Hemoglobin"). |
| C | `unit` | String | No | Unit of measurement (e.g., "g/dL", "%"). |

**Example:**
| parameter_id | parameter_name | unit |
| :--- | :--- | :--- |
| p1 | Hemoglobin | g/dL |
| p2 | Glucose | mg/dL |

---

## Sheet 2: `Tests`
Defines the orderable tests.

| Column | Header Name | Type | Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| A | `test_id` | Integer | **Yes** | Unique system ID (e.g., `1`, `100`). Primary Key. |
| B | `test_code` | String | **Yes** | Display code (e.g., `CBC`, `GLU`). Unique. |
| C | `legacy_test_code` | String | No | Old code for reference (e.g., `L-500`). |
| D | `test_name` | String | **Yes** | Full name of the test. |
| E | `category` | String | **Yes** | Category name (e.g., "Hematology"). Created if missing. |
| F | `sample_type` | String | No | Default: "Serum". |
| G | `price` | Decimal | No | Test price. |
| H | `turnaround_time` | Integer | No | TAT in hours. Default: 24. |

**Example:**
| test_id | test_code | legacy_test_code | test_name | category | sample_type | price | turnaround_time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | CBC | OLD-CBC | Complete Blood Count | Hematology | EDTA Blood | 500.00 | 24 |

---

## Sheet 3: `Mapping`
Links global Parameters to Tests.

| Column | Header Name | Type | Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| A | `test_id` | Integer | **Yes** | Must match a `test_id` in the `Tests` sheet. |
| B | `parameter_id` | String | **Yes** | Must match a `parameter_id` in the `Parameters` sheet. |
| C | `display_order` | Integer | No | Order of appearance on reports (1, 2, 3...). |
| D | `reportable` | Boolean | No | `TRUE`/`1` to show on reports, `FALSE`/`0` to hide. Default: `TRUE`. |

**Example:**
| test_id | parameter_id | display_order | reportable |
| :--- | :--- | :--- | :--- |
| 1 | p1 | 1 | 1 |
| 1 | p2 | 2 | 1 |

---

## Sheet 4: `ReferenceRanges`
Defines age/gender-specific ranges for the Test-Parameter pairs.

| Column | Header Name | Type | Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| A | `test_id` | Integer | **Yes** | ID of the test. |
| B | `parameter_id` | String | **Yes** | ID of the parameter. |
| C | `gender` | String | No | `Male`, `Female`, or `Both`. Default: `Both`. |
| D | `age_min` | Integer | No | Min age in years. |
| E | `age_max` | Integer | No | Max age in years. |
| F | `reference_min` | Decimal | No | Lower limit of normal range. |
| G | `reference_max` | Decimal | No | Upper limit of normal range. |
| H | `critical_low` | Decimal | No | Critical low value. |
| I | `critical_high` | Decimal | No | Critical high value. |

**Example:**
| test_id | parameter_id | gender | age_min | age_max | reference_min | reference_max | critical_low | critical_high |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | p1 | Male | 18 | 99 | 13.5 | 17.5 | 7.0 | 20.0 |
