# Row-Level Security (RLS) — Market-level Access

> **Status:** Implemented in the semantic model and **verified zero-leakage in v2 Phase 5** (View-as `MarketManager` / `europe_mgr@company.com` → only Europe visible). `DIM_MARKET` and `SEC_USER_MARKET` are real model tables (not Gold CSVs); see [`08_star_schema.md`](08_star_schema.md). Unchanged by the v2 commercial measures — RLS propagates through `DIM_CHANNEL`, so the new CTS/DIFOT/rebate measures inherit market scoping automatically.

## Objective

Enforce **Market-scoped visibility** with an unrestricted executive role.

## Roles

### Executive

- Full access (no filters)

### MarketManager

- Restricted to the Market(s) mapped to the signed-in user

Role rule (applied to `SEC_USER_MARKET`):

```DAX
SEC_USER_MARKET[UserEmail] = USERPRINCIPALNAME()
```

### Tables

- **DIM_MARKET**: unique list of Markets (1 row per Market)
- **SEC_USER_MARKET**: user-to-market mapping table
  - Columns: `UserEmail`, `MARKET`

### Relationships (required)

- `DIM_MARKET[MARKET]` (1) → `DIM_CHANNEL[MARKET]` (\*)
  - Cross-filter: **Single** | Active: ✅
- `DIM_MARKET[MARKET]` (1) ↔ `SEC_USER_MARKET[MARKET]` (\*)
  - Cross-filter: **Both** | Active: ✅
  - Purpose: propagate the **MarketManager** RLS filter from the mapping table into the model

### Report wiring requirement

- Market slicers/filters must use: **`DIM_MARKET[MARKET]`** (not `DIM_CHANNEL[MARKET]`)

### Validation (Desktop)

- Modeling → **View as** → `MarketManager`
- Test identity: `europe_mgr@company.com`
- Expected:
  - Only **Europe** available in Market slicer
  - All visuals restricted to Europe data
  - `Executive` role shows all markets
