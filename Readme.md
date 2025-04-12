# FHSS Sequence Generator

This tool replicates the frequency-hopping sequence algorithm used in embedded systems like ExpressLRS, using the same Linear Congruential Generator (LCG) algorithm found on ESP32 firmware. It's useful for reverse-engineering, signal analysis, and debugging drone RF protocols that rely on FHSS.

## 🔧 Features

- Bit-accurate FHSS sequence generation
- Firmware-compatible RNG (ESP32-style LCG)
- UID generation from numeric phrases or binding strings
- Multiple regional domain support (FCC915, AU915, EU868, IN866)
- Human-readable logging and output
- CLI-friendly, fast, and extensible

## 🚀 Installation

Python 3.7+ required.

```bash
git clone https://github.com/wolfcybersec/fhsshop
cd fhss-sequence-generator
pip install -r requirements.txt  # Only if you add deps like numpy
```

This script currently has no external dependencies.

## 🧪 Usage

```bash
python3 fhss_gen.py --domain FCC915 --phrase 42,13,9,8
```

### Arguments

| Argument      | Description                                       | Default         |
|---------------|---------------------------------------------------|-----------------|
| `--domain`    | Regulatory domain (FCC915, AU915, EU868, IN866)   | `FCC915`        |
| `--phrase`    | Comma-separated UID phrase or a binding string     | `42,13,9,8`     |

### Example Output

```
[INFO] UID: aabbccddeeff
[INFO] Seed: 283746519
[INFO] Regulatory Domain: FCC915
[INFO] Sync Channel: 20
[INFO] Total Hops: 256
FHSS Sequence (indices):
 0 20  2  3  4  5  6  7  8  9
...
```

## ⚙️ How It Works

1. **UID Generation**: Accepts a comma-separated numeric phrase or fallback string to generate a 6-byte UID.
2. **Seed Derivation**: Converts UID into a 32-bit seed using the same logic as ExpressLRS.
3. **RNG**: Uses a firmware-accurate Linear Congruential Generator.
4. **Sequence Builder**:
    - Inserts sync channels at fixed intervals.
    - Pseudo-randomly swaps frequency positions per firmware logic.

## 📦 Structure

- `generate_uid()` – Handles UID derivation
- `compute_seed_from_uid()` – Converts UID to PRNG seed
- `FirmwareLCG` – Implements ESP32-compatible LCG
- `FHSSGenerator` – Builds the 256-hop frequency sequence
- `main()` – Parses arguments and prints the sequence

## 📘 Notes

- This tool is meant for reverse-engineering and testbench purposes.
- Output is bit-accurate to what ELRS firmware would generate using the same seed and domain.

### 🔍 Pattern Similarity Between `FHSS_SEQUENCE_LEN = 256` and `512`

- **Matching Prefix**: Out of the first 256 hops in the 512-length sequence, **243 are identical** to the 256-length sequence.  
  → That’s a **94.9% match**, showing strong alignment at the beginning.

- **Cross-Correlation**: A strong peak near the center of the correlation curve confirms significant **overlap in structure and pattern**, especially in the first half of the 512-sequence.

### 🧠 Why This Happens
- The random number generator (`FirmwareLCG`) is deterministic, and both sequences are built using the **same seed**.
- The shuffle logic is consistent up to index 256 — beyond that, the 512-sequence continues while the 256 stops.
- This means **longer sequences are supersets** of shorter ones, up to their length.



## 🛡 License

MIT
