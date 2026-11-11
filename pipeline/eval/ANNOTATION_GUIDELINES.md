# Annotation guidelines for the golden set (DRAFT)

These rules define how the ground-truth amount `expected_10kW` in `golden_set.csv` is determined.
They exist so that every row is labelled the same way. Rules marked **(open)** still need to be
discussed, partly with OK Climat.

## 1. What one row is

- One row = one subsidy (`subv_id`) from one contributor (a municipality, a canton or a utility).
- The amount is **only that contributor's subsidy**. Subsidies from other levels are not added,
  e.g. a city subsidy that comes "on top of" the cantonal one or of Pronovo.

## 2. The standard case

- One installation of **10 kW**: 10 kWp for PV, 10 kWth for solar thermal (PV-EauCd).
- PV: a standard roof-mounted installation (attached, "angebaut" / "isolée"). Rates for
  integrated or facade installations are not used. Example: Aarau PV, 2218: 500 + 10 × 100 = 1500.
- **(open)** Type of building and installation, e.g. single-family house, new installation on an
  existing building. Needed when a subsidy differs by building type (e.g. Crans: individual vs.
  collective buildings; Aarau thermal, 2041: max. 10 m² for a single-family house, 12 m² for a
  two-family house).
- New installation on an **existing building** (not part of a new build). Several subsidies
  require this, e.g. canton Aargau thermal, 2939.
- **(open)** Is 10 kW realistic for solar thermal? 10 kWth is 14–20 m² of collectors, more than
  a typical single-family house has.

## 3. What counts in the amount

- Fixed amounts (Grundbeitrag, Pauschal, montant de base) are included.
- Per-kW amounts are multiplied by 10.
- Components that are **mandatory** to get the subsidy are included,
  e.g. monitoring if it is required (Luzern, 118).
- **(open)** Optional bonuses (steep tilt, facade, green roof, optional monitoring) are excluded.
- Caps (Maximalbeitrag, plafond) and minimums are applied.
- Only **one-time** payments count. Payments per kWh of electricity fed into the grid
  (feed-in remuneration, e.g. Ticino "rimunerazione minima FER", 4.0 cts/kWh) are not included.
- **(open)** Caps relative to the investment cost (e.g. "max. 40 % of the investment costs",
  Basel thermal, 84) are ignored, since the cost is unknown.

## 4. Eligibility

- **(open)** If a 10 kW installation does not qualify (e.g. the subsidy is only for > 90 kWp),
  the amount is 0. Example: Neuchâtel, 4605.
- **(open)** Conditions every installation could meet in principle (tilt angle, anti-glare
  modules, date of commissioning) are assumed to be met.
  - This also applies when the whole subsidy is for a special type of installation, e.g. steep
    "winter electricity" PV (Nesslau, 2290: ≥ 75°, 300 × 10 = 3000, which is also the cap).
    The `exemples` labels already follow this (also 1171, 3669, 2828).
  - Proposed distinction: a condition on the **size** contradicts the standard case of 10 kW,
    so the amount is 0 (Neuchâtel, 4605). A condition on **other properties** (tilt, modules,
    inverter) is assumed met.

- **(open)** A subsidy that is only paid **in combination with another major measure** (e.g. an
  energy renovation of the roof or facade) does not count, and the amount is 0. Example: Basel
  "Aktion Solarkraftwerk", 5138 (`subsidy_exist = no`). Same logic as for optional bonuses,
  e.g. Vaud thermal 398, where the amount is doubled with a simultaneous renovation.

## 5. Conversions

- Pronovo one-time subsidy (EIV / RU / PRU): **360 CHF per kW**. A subsidy of X % of Pronovo
  is X % × 360 × 10. Example: Luzern PV, 522: 20 % × 3600 = 720.
  - Basis: a 10 kW installation of the type "attached / isolated" (angebaut / isolée), checked
    with the Pronovo calculator. Federal bonuses (Zuschläge, e.g. for steep tilt) are not included.
  - **(open)** Pronovo rates change over time. Record the date the 360 CHF/kW was checked.
- Amounts per m² are converted with the factors from the `general` sheet of `PV examples.xlsx`:
  - solar thermal (PV-EauCd): 0.5 kW/m², so 10 kW = 20 m²
  - PV: 0.2 kW/m², so 10 kW = 50 m²
  - Note: the LLM prompt in `analyze_subsidies.py` currently uses these two factors the other
    way round.
- **(open)** "Per additional kW" above a minimum size: count only the kW above the minimum,
  or all 10? Example: Uri PV, 1171 (3000 vs. 3500).

## 6. No subsidy

- If the contributor offers no subsidy of this type: `subsidy_exist = no`, `expected_10kW = 0`.

## 7. Recording changes

- `golden_set.csv` (version 0) is never edited by hand.
- Each proposed change goes into `corrections.csv` with the old value, new value, a reason
  and a status (`proposed`, `confirmed`, `rejected`).
- **(open)** Record the date each row was checked, since websites change over time.

## Open questions for OK Climat

- Optional bonuses: include or exclude? (§3)
- Installations that are not eligible at 10 kW: 0 or the nominal amount? (§4)
- Subsidies that exist **only for steep installations** (winter electricity, facades): should
  they count for the standard case, or be 0? (§4) Rows concerned so far:
  - 2290 Nesslau: ≥ 75°, 300 CHF/kWp, max. 3000 (current label 3000)
  - 1171 Uri: 60°–90°, 1000 + 250 CHF per additional kWp (current label 3500)
  - 3669 Glarus: ≥ 75°, tilt bonus 250 CHF/kWp (current label 2500)
  - 2828 Graubünden: 60°–90°, 300 CHF/kWp, min. 900 (current label 3000)
- "Per additional kW": how to count? (§5)
- Which building type is the standard case? (§2) Rows where it changes the amount:
  - 2041 Aarau thermal: max. 10 m² (single-family) or 12 m² (two-family) → 2000 / 2400 instead of 4000
  - 398 Vaud thermal: hot water in a single-family house is a flat 4000 instead of
    2500 + 500 × 10 = 7500 (current label 7500)
- The two Crans (VD) rows: they have no ID in the database.

## Excluded rows

- Luzern Solar-Impuls (page 76930, `subv_id` 5097): a free PV consultation, type `PV-Cnsl` in
  the database, so the pipeline does not process it. Removed from `manual_ids.csv`.
  Possible hard negative for later.
- Crans (VD), PV and PV-EauCd: no `subv_id` in the database.
