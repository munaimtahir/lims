# Reference Ranges (Selection + Display)

This system uses a single reference-range selector to ensure **flagging** and **PDF reporting** use the same logic.

## Selection Rules
1. **ReferenceRange first**  
   - Candidates: `ReferenceRange` rows where `parameter=TestParameter` and `is_active=True`.
   - Gender match: exact gender (`Male` / `Female`) is preferred, but `Both` is allowed.
   - Age match: `age_min <= age <= age_max` (nulls are open-ended).
2. **Best match wins**  
   - Prefer exact gender over `Both`.
   - Prefer the **narrowest** age window.
   - If still tied, pick the **highest version**.
3. **Fallback**  
   - If the patient is missing DOB or gender, or no `ReferenceRange` matches,
     fallback to `TestParameter.reference_min_*` / `reference_max_*` (gender-specific
     when possible, otherwise the first available).

## Display Format
The display string is formatted consistently:
- `min` + `max` → `min - max`
- `min` only → `>= min`
- `max` only → `<= max`
- none → empty string

## Flags
Numeric results use the shared range selector and produce:
- `C` for critical breach (below critical low or above critical high)
- `L` if below the reference minimum
- `H` if above the reference maximum
- `""` if within range or no range is available

Non-numeric results do not compute flags.
