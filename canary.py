"""Quilt Spreadsheet canary — same FNV-1a 64-bit canary as the polyformalism fleet."""
import sys


def fnv1a_64(s: str) -> int:
    h = 0xcbf29ce484222325
    for b in s.encode("utf-8"):
        h = h ^ b
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return h


if __name__ == "__main__":
    s = "café Δ 日本語"
    h = fnv1a_64(s)
    print(f"0x{h:016x}")
    if h == 0x024a555471370b18d:
        print("✓ Fleet canary verified: 0x024a555471370b18d")
        sys.exit(0)
    else:
        print(f"✗ FAIL: expected 0x024a555471370b18d, got 0x{h:016x}")
        sys.exit(1)
