import hashlib
import logging
import argparse
from typing import List, Tuple, Dict

# Constants
FHSS_SEQUENCE_LEN = 256
OTA_VERSION_ID = 4

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Configs (mirroring fhss_config_t)
DOMAINS: Dict[str, Dict[str, int]] = {
    "FCC915": {
        "freq_start": 903_500_000,
        "freq_stop": 926_900_000,
        "freq_count": 40,
        "sync_center_freq": 915_000_000
    },
    "AU915": {
        "freq_start": 915_500_000,
        "freq_stop": 926_900_000,
        "freq_count": 20,
        "sync_center_freq": 921_000_000
    },
    "EU868": {
        "freq_start": 865_275_000,
        "freq_stop": 869_575_000,
        "freq_count": 13,
        "sync_center_freq": 868_000_000
    },
    "IN866": {
        "freq_start": 865_375_000,
        "freq_stop": 866_950_000,
        "freq_count": 4,
        "sync_center_freq": 866_000_000
    }
}


def generate_uid(phrase: str) -> bytes:
    """
    Generate a 6-byte UID from a comma-separated phrase.
    Falls back to a truncated MD5 hash if the input is invalid.

    Args:
        phrase (str): Comma-separated values or any string.

    Returns:
        bytes: A 6-byte UID.
    """
    try:
        uid = [int(item) if item.isdigit() else -1 for item in phrase.split(',')]
        if 4 <= len(uid) <= 6 and all(0 <= ele < 256 for ele in uid):
            padded_uid = [0] * (6 - len(uid)) + uid
            return bytes(padded_uid)
    except ValueError:
        pass
    return hashlib.md5(f'-DMY_BINDING_PHRASE="{phrase}"'.encode()).digest()[:6]

def compute_seed_from_uid(uid: bytes) -> int:
    """
    Compute a deterministic seed from a UID.

    Args:
        uid (bytes): A 6-byte UID.

    Returns:
        int: A 32-bit seed value.
    """
    return ((uid[2] << 24) |
            (uid[3] << 16) |
            (uid[4] << 8) |
            (uid[5] ^ OTA_VERSION_ID)) & 0xFFFFFFFF

class FirmwareLCG:
    """
    A firmware-compatible Linear Congruential Generator mimicking ESP32 rand().
    """

    def __init__(self, seed: int) -> None:
        """
        Initialize the generator with a seed.

        Args:
            seed (int): Initial seed value.
        """
        self.state = seed & 0xFFFFFFFF

    def rand(self) -> int:
        """
        Generate the next random integer.

        Returns:
            int: A pseudo-random integer.
        """
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return self.state

    def rand_range(self, max_val: int) -> int:
        """
        Generate a pseudo-random integer within a range.

        Args:
            max_val (int): Upper bound for the random value.

        Returns:
            int: Random number in [0, max_val).
        """
        return self.rand() % max_val

class FHSSGenerator:
    """
    Frequency-Hopping Spread Spectrum (FHSS) sequence generator.
    """

    def __init__(self, freq_count: int, seed: int) -> None:
        """
        Initialize the FHSS generator.

        Args:
            freq_count (int): Number of frequency channels.
            seed (int): Seed value for the random generator.
        """
        self.freq_count = freq_count
        self.sync_channel = freq_count // 2
        self.rng = FirmwareLCG(seed)

    def build_sequence(self) -> Tuple[int, ...]:
        """
        Build a frequency-hopping sequence.

        Returns:
            Tuple[int, ...]: Tuple of channel indices.
        """
        sequence = [0] * FHSS_SEQUENCE_LEN

        # Initial channel allocation
        for i in range(FHSS_SEQUENCE_LEN):
            if i % self.freq_count == 0:
                sequence[i] = self.sync_channel
            elif i % self.freq_count == self.sync_channel:
                sequence[i] = 0
            else:
                sequence[i] = i % self.freq_count

        # Pseudo-random shuffle within frequency blocks
        for i in range(FHSS_SEQUENCE_LEN):
            if i % self.freq_count != 0:
                block_start = (i // self.freq_count) * self.freq_count
                rand_offset = self.rng.rand_range(self.freq_count - 1) + 1
                swap_idx = block_start + rand_offset
                if swap_idx < FHSS_SEQUENCE_LEN:
                    sequence[i], sequence[swap_idx] = sequence[swap_idx], sequence[i]

        return tuple(sequence)

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generate FHSS frequency sequence.")
    parser.add_argument("--domain", type=str, default="FCC915",
                        choices=DOMAINS.keys(), help="Regulatory domain")
    parser.add_argument("--phrase", type=str, default="42,13,9,8",
                        help="Binding phrase (comma-separated integers or a string)")
    return parser.parse_args()

def main() -> None:
    """
    Main entry point for generating and printing the FHSS sequence.
    """
    args = parse_args()
    domain_config = DOMAINS[args.domain]

    uid = generate_uid(args.phrase)
    seed = compute_seed_from_uid(uid)
    generator = FHSSGenerator(freq_count=domain_config["freq_count"], seed=seed)
    sequence = generator.build_sequence()

    logging.info(f"UID: {uid.hex()}")
    logging.info(f"Seed: {seed}")
    logging.info(f"Regulatory Domain: {args.domain}")
    logging.info(f"Sync Channel: {sequence[domain_config['freq_count']]}")
    logging.info(f"Total Hops: {len(sequence)}")

    print("FHSS Sequence (indices):")
    for i, val in enumerate(sequence):
        print(f"{val:2}", end=' ')
        if (i + 1) % 10 == 0:
            print()

if __name__ == "__main__":
    main()