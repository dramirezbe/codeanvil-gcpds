# Golden Vector Manifest

Controlled artifacts. Changing any vector invalidates every evidence record that used it.
Regenerate with `PYTHONPATH=. uv run python verification/golden/build_vectors.py`.

| Vector ID | SHA-256 | File | Generation Parameters | Simulated Condition | Expected Output |
|-----------|---------|------|----------------------|---------------------|-----------------|
| GV-1 | `f4619c809af8e7be15b39e4acf7148b834a2ccbb0da0200127c469a05059111d` | `gv1.bin` (4 bytes) | uint8 bytes `[255, 0, 127, 128]` | Raw sample conversion | complex64 `[1.0 − 1.0j, −0.0039216 + 0.0039216j]` (± 1e-6) |
| GV-2 | `505c20b80a6215e7ca22337a14c52d52704623f2428ea7148c9fa210b188e2e7` | `gv2.bin` (65536 complex64) | 64 × 1024 complex64 samples, tone amplitude 1.0 at +43 bins (+100.78125 kHz), no noise | Pure tone spectrum | Maximum of P at index 469 of the 853-bin array, value 0.0 ± 0.1 dBFS |
| GV-3 | `c5c8f19b8dd54b4aee4394ac204084f38f579b342f8dc0f8797420e870dbbf89` | `gv3.bin` (65536 complex64) | 64 × 1024 complex64 samples, tone amplitude 1.0 at fc + 0.1 MHz (100 kHz), no noise | Channel power identification | Highest channel power is channel n = 5 |
| GV-4 | `a55b680507bca3c8d2e8cc470714674d53d14dbc46173265eb5a1dcf2a9cce85` | `gv4.bin` (131072 uint8) | SC-2 through Mock HAL with seed 1, one update (n1, n4, n8 at −20 dBFS) | Detection flags | Occupied flags `[false, true, false, false, true, false, false, false, true, false]` |
| GV-5 | `d7891f302c30c5717f060a4d5eba59b718b0f2b90e8d42d6d0218a19b4efe09c` | `gv5.json` | One fixed Y8 message with channels n1 and n4 occupied | WebSocket message validation | Table shows 10 rows with n1 and n4 marked occupied; a copy with `v` = 2 is rejected and logged |
