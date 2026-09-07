ID date parsing rules

Supported sources
- AAMVA PDF417 barcodes: fields `DBB` (DOB), `DBD` (Issue), `DBA` (Expiry) are `YYYYMMDD` and convert to `YYYY-MM-DD`.
- Passport MRZ (TD3): second line positions
  - DOB: characters 14–19 (YYMMDD)
  - Expiry: characters 22–27 (YYMMDD)
  - Two-digit year pivot: `00–29 → 2000+`, `30–99 → 1900+` with sanity check (DOB in past, expiry in future).
- OCR text labels: `DOB`, `Issue`, `EXP` labels
  - Accept `MM/DD/YYYY`, `MM/DD/YY`; convert to `YYYY-MM-DD` (two‑digit year pivot 50).
  - Accept `DD/MM/YYYY` when the first token >12; convert to `YYYY-MM-DD`.
  - Accept `YYYY-MM-DD` as is and `Month DD, YYYY`.

Validation
- All dates are validated using calendar rules and reasonable ranges (1900–2100). Invalid candidates are ignored.

Selection and precedence
- Barcode/MRZ values take precedence over OCR text.
- For `EXP`, nearby dates around its label are normalized and the latest ISO date is selected.

Backward compatibility
- US formats (`MM/DD/YY`) keep a 50‑year pivot to avoid changing historical behavior.
- New logic adds `DD/MM/YYYY` and MRZ support without altering existing AAMVA handling.