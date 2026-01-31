# Catalog Workbook Contract (Authoritative)

This document defines the required Excel workbook structure for catalog import/export.
The export endpoint (`/api/v1/laboratory/export/`) **must** match this contract exactly.
The import endpoint validates against this contract when `strict=true`.

## General Rules
- File format: `.xlsx` only.
- Sheet names: **exactly** as listed below.
- Header row: required on row 1.
- Empty rows are ignored.
- Import mode: `mode=upsert` (idempotent).
- Deterministic: row order and column order must be stable.

## Sheet Order (exported)
1. Tests
2. Parameters
3. Mapping
4. Panels
5. PanelTests
6. ReferenceRanges

---

## 1) Tests
Primary key: `test_id`

| Column | Required | Type | Notes |
|---|---|---|---|
| test_id | Yes | Integer | Stable internal ID |
| test_code | Yes | String | Unique code |
| legacy_test_code | No | String | Optional legacy code |
| test_name | Yes | String | Display name |
| category | Yes | String | Category name |
| sample_type | No* | String | Default: `Serum` if `allow_defaults=true` |
| sample_volume | No | String | Optional |
| price | No* | Decimal | Default: `0` if `allow_defaults=true` |
| turnaround_time | No* | Integer | Default: `24` if `allow_defaults=true` |
| loinc_code | No | String | Optional |
| instructions | No | String | Optional |
| is_active | No | Boolean | Default: `true` if `allow_defaults=true` |

**Strict mode**: if `allow_defaults=false`, missing `sample_type`, `price`, or `turnaround_time` is an error because the database requires values.

---

## 2) Parameters
Primary key: `parameter_id`

| Column | Required | Type | Notes |
|---|---|---|---|
| parameter_id | Yes | String | Format: `p<number>` (e.g., `p1`) |
| parameter_name | Yes | String | Display name |
| unit | No | String | Optional |
| data_type | No | String | Default: `Numeric` if `allow_defaults=true` |
| editor_type | No | String | Default: `Plain` if `allow_defaults=true` |
| decimal_places | No | Integer | Default: `2` if `allow_defaults=true` |
| allowed_values | No | String | Optional |
| flag_direction | No | String | Default: `Both` if `allow_defaults=true` |
| has_quick_text | No | Boolean | Default: `false` if `allow_defaults=true` |
| active | No | Boolean | Default: `true` if `allow_defaults=true` |

---

## 3) Mapping
Primary key: (`test_id`, `parameter_id`)

| Column | Required | Type | Notes |
|---|---|---|---|
| test_id | Yes | Integer | Must exist in Tests |
| parameter_id | Yes | String | Must exist in Parameters |
| display_order | No | Integer | Default: `0` if `allow_defaults=true` |
| reportable | No | Boolean | Default: `true` if `allow_defaults=true` |

---

## 4) Panels
Primary key: `panel_code`

| Column | Required | Type | Notes |
|---|---|---|---|
| panel_code | Yes | String | Unique code |
| panel_name | Yes | String | Display name |
| category | Yes | String | Category name |
| sample_type | No* | String | Default: `Serum` if `allow_defaults=true` |
| sample_volume | No | String | Optional |
| price | No* | Decimal | Default: `0` if `allow_defaults=true` |
| turnaround_time | No* | Integer | Default: `24` if `allow_defaults=true` |
| description | No | String | Optional |
| is_active | No | Boolean | Default: `true` if `allow_defaults=true` |

---

## 5) PanelTests
Primary key: (`panel_code`, `test_id`)

| Column | Required | Type | Notes |
|---|---|---|---|
| panel_code | Yes | String | Must exist in Panels |
| test_id | Yes | Integer | Must exist in Tests |

---

## 6) ReferenceRanges
Primary key: (`test_id`, `parameter_id`, `gender`, `age_min`, `age_max`, `version`)

| Column | Required | Type | Notes |
|---|---|---|---|
| test_id | Yes | Integer | Must exist in Tests |
| parameter_id | Yes | String | Must exist in Parameters |
| gender | No | String | `Male`, `Female`, `Both` (default: `Both` if `allow_defaults=true`) |
| age_min | No | Integer | Years; null allowed |
| age_max | No | Integer | Years; null allowed |
| reference_min | No | Decimal | Optional |
| reference_max | No | Decimal | Optional |
| critical_low | No | Decimal | Optional |
| critical_high | No | Decimal | Optional |
| is_active | No | Boolean | Default: `true` if `allow_defaults=true` |
| version | No* | Integer | Default: `1` if `allow_defaults=true` |
| notes | No | String | Optional |

---

## Upsert Keys (Deterministic)
- Tests: `test_id`
- Parameters: `parameter_id`
- Mapping: (`test_id`, `parameter_id`)
- Panels: `panel_code`
- PanelTests: (`panel_code`, `test_id`)
- ReferenceRanges: (`test_id`, `parameter_id`, `gender`, `age_min`, `age_max`, `version`)

---

## Strict Mode Rules (`strict=true`, default)
- Missing required **columns** or **values** are errors.
- Invalid types (e.g., non-integer IDs) are errors.
- Invalid `parameter_id` format is an error.
- Orphaned mappings/ranges are errors.

## Defaults (`allow_defaults=true`)
When enabled, defaults are applied **and a warning is emitted** for each defaulted value.
When disabled, missing defaultable fields are errors under strict mode.
