"""Synthetic PII generators — Verhoeff-valid Aadhaar and Luhn-valid card numbers.

These are the ONLY source of ID numbers permitted in tests and fixtures.
Never use real PAN, Aadhaar, or card numbers anywhere in the codebase.
"""
import random

# ── Verhoeff tables ───────────────────────────────────────────────────────────

_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def _verhoeff_check_digit(number: str) -> int:
    c = 0
    for i, ch in enumerate(reversed(number)):
        c = _D[c][_P[(i + 1) % 8][int(ch)]]
    return _INV[c]


def fake_aadhaar(rng: random.Random | None = None) -> str:
    """Return a 12-digit Verhoeff-valid synthetic Aadhaar number.

    First digit is 2–9 (per UIDAI spec — 0 and 1 are reserved).
    """
    r = rng or random.Random()
    base = str(r.randint(2, 9)) + "".join(str(r.randint(0, 9)) for _ in range(10))
    return base + str(_verhoeff_check_digit(base))


# ── Luhn ──────────────────────────────────────────────────────────────────────


def _luhn_check_digit(number: str) -> int:
    total = 0
    for i, ch in enumerate(reversed(number)):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return (10 - (total % 10)) % 10


def fake_card(length: int = 16, prefix: str = "4", rng: random.Random | None = None) -> str:
    """Return a Luhn-valid synthetic card number.

    Defaults to a 16-digit Visa-style number (prefix "4").
    """
    r = rng or random.Random()
    payload = prefix + "".join(str(r.randint(0, 9)) for _ in range(length - len(prefix) - 1))
    return payload + str(_luhn_check_digit(payload))


def fake_pan(rng: random.Random | None = None) -> str:
    """Return a syntactically valid (but fake) PAN: AAAAA9999A format."""
    import string

    r = rng or random.Random()
    letters = string.ascii_uppercase
    return (
        "".join(r.choices(letters, k=5))
        + "".join(str(r.randint(0, 9)) for _ in range(4))
        + r.choice(letters)
    )
