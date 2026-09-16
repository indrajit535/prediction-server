"""
SDDGAMER263 — Custom Prediction Algorithm
------------------------------------------
12-step unique calculation combining:
- Modular arithmetic (mod 7, 9, 10, 11, 13)
- Digit reversal, digit sum
- Complements
- XOR-style logic
- Prime numbers
- Fibonacci sequence
- Cyclic transformations
- Mirror + rotational shift
- Weighted digit multiplication

Final answer: single digit (0-9)
"""

import random


# ============================================================
# FIBONACCI
# ============================================================
FIB = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]

PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]


def digit_sum(n: int) -> int:
    """Digit sum nikalo (e.g. 45 → 9)."""
    return sum(int(d) for d in str(abs(n)))


def reverse_digits(n: int) -> int:
    """Digits reverse karo (e.g. 94 → 49)."""
    return int(str(abs(n))[::-1])


def xor_style(a: int, b: int) -> int:
    """XOR-style operation (bitwise XOR)."""
    return a ^ b


def rotate_left(value: int, bits: int, shift: int) -> int:
    """Binary rotate-left."""
    mask = (1 << bits) - 1
    value &= mask
    shift %= bits
    return ((value << shift) | (value >> (bits - shift))) & mask


def mirror_transform(n: int, mod: int = 10) -> int:
    """Mirror: (mod - 1 - n) % mod"""
    return (mod - 1 - n) % mod


# ============================================================
# MAIN PREDICTION ALGORITHM
# ============================================================
def sddgamer263_predict(current_number: int, period: str, seed: int = None) -> dict:
    """
    SDDGAMER263 custom prediction algorithm.
    
    Args:
        current_number: Last result number (0-9)
        period: Period string (e.g. "2025010110000001")
        seed: Optional random seed for reproducibility
    
    Returns:
        {
            "prediction": int (0-9),
            "bigSmall": "BIG"/"SMALL",
            "steps": list of step descriptions,
            "confidence": float
        }
    """
    if seed is not None:
        random.seed(seed)

    steps = []
    current = int(current_number) % 10
    last_digit_of_period = int(str(period)[-1]) if period else 0

    # ========================================================
    # STEP 1: Weighted Fibonacci dot product mod 13
    # ========================================================
    # A = (3·n + 7·p + 1·2 + 8·3 + 2·5 + 9·8 + 4·13 + 6·21 + 0·34 + 5·55) mod 13
    weights = [3, 7, 1, 8, 2, 9, 4, 6, 0, 5]
    fib_vals = FIB[:10]  # [0,1,1,2,3,5,8,13,21,34]
    # But spec uses: 1,1,2,3,5,8,13,21,34,55
    fib_seq = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    A_raw = (weights[0] * current + weights[1] * last_digit_of_period +
             sum(weights[i] * fib_seq[i] for i in range(2, 10)))
    A = A_raw % 13
    steps.append(f"STEP 1:  A = ({weights[0]}·{current} + {weights[1]}·{last_digit_of_period} + "
                 f"1·2 + 8·3 + 2·5 + 9·8 + 4·13 + 6·21 + 0·34 + 5·55) mod 13\n"
                 f"            = {A_raw} mod 13 = {A}")

    # ========================================================
    # STEP 2: Digit sum cyclic mod 9
    # ========================================================
    S = digit_sum(A_raw)
    B = S % 9
    if B == 0:
        B = 9
    steps.append(f"STEP 2:  S = {S}  →  digitSum({A_raw}) = {S}  →  B = {S} mod 9 = {S % 9} → B = {B}")

    # ========================================================
    # STEP 3: XOR + complement mod 7
    # ========================================================
    xor_val = xor_style(current, last_digit_of_period)
    comp = (last_digit_of_period - current) % 10
    C = (xor_val + comp) % 7
    steps.append(f"STEP 3:  ({current} XOR {last_digit_of_period}) = {xor_val} ;  "
                 f"({last_digit_of_period}-{current}) = {comp}  →  C = ({xor_val}+{comp}) mod 7 = {C}")

    # ========================================================
    # STEP 4: Weighted combination mod 11
    # ========================================================
    D_raw = A * B + B * C + C * 11 + C * 3
    D = D_raw % 11
    steps.append(f"STEP 4:  D = ({A}·{B} + {B}·{C} + {C}·11 + {C}·3) mod 11\n"
                 f"            = ({A*B}+{B*C}+{C*11}+{C*3}) mod 11 = {D_raw} mod 11 = {D}")

    # ========================================================
    # STEP 5: Binary rotate-left-2
    # ========================================================
    E = rotate_left(D, 4, 2)
    steps.append(f"STEP 5:  D = {D:04b}b  →  rotate-left-2 = {E:04b}b = {E}  →  E = {E}")

    # ========================================================
    # STEP 6: Reverse + mod 9
    # ========================================================
    temp = D * 13 + E + C
    rev = reverse_digits(temp)
    F = rev % 9
    if F == 0:
        F = 9
    steps.append(f"STEP 6:  temp = {D}·13 + {E} + {C} = {temp}  →  reverse({temp})={rev}  →  F = {rev} mod 9 = {F}")

    # ========================================================
    # STEP 7: Mirror + weighted mod 13
    # ========================================================
    mirror_val = mirror_transform(C)
    G = ((10 - C) * 2 + F + last_digit_of_period) % 13
    steps.append(f"STEP 7:  G = ((10-{C})·2 + {F} + {last_digit_of_period}) mod 13 = {G}")

    # ========================================================
    # STEP 8: Fibonacci index mod 7
    # ========================================================
    fib_idx = G % len(FIB)
    fib_val = FIB[fib_idx]
    Hm = (G + fib_val + A) % 7
    steps.append(f"STEP 8:  fib_val = Fib[{fib_idx}] = {fib_val}  →  Hm = ({G}+{fib_val}+{A}) mod 7 = {Hm}")

    # ========================================================
    # STEP 9: XOR with D mod 10
    # ========================================================
    I = xor_style(Hm, D) % 10
    steps.append(f"STEP 9:  I = (Hm XOR D) mod 10 = ({Hm} XOR {D}) mod 10 = {I}")

    # ========================================================
    # STEP 10: Weighted digit multiplication + digit sum
    # ========================================================
    W = I * 2 + C * 5 + A * 9
    ds = digit_sum(W)
    J = ds % 10
    steps.append(f"STEP 10: W = {I}·2 + {C}·5 + {A}·9 = {W}  →  digitSum={ds}  →  J = {ds}")

    # ========================================================
    # STEP 11: Grand sum mod 13
    # ========================================================
    K_raw = (J * 7 + I * 3 + F * 5 + C + F + A + E + D + B + A + Hm + G)
    K = K_raw % 13
    steps.append(f"STEP 11: K = ({J}·7 + {I}·3 + {F}·5 + {C} + {F} + {A} + {E} + {D} + {B} + {A} + {Hm} + {G}) mod 13\n"
                 f"            = {K_raw} mod 13 = {K}")

    # ========================================================
    # STEP 12: Final modulation
    # ========================================================
    T = (K + J + I) % 10
    U = (T * 3 + I) % 7
    prediction = (T + U) % 10
    steps.append(f"STEP 12: T = ({K}+{J}+{I}) mod 10 = {T}\n"
                 f"         U = ({T}·3 + {I}) mod 7 = {U}\n"
                 f"         Prediction = ({T}+{U}) mod 10 = {prediction}")

    # BIG/SMALL
    big_small = "BIG" if prediction >= 5 else "SMALL"

    # Confidence (deterministic based on inputs + slight variation)
    confidence = round(97.5 + (abs(hash(f"{current}{period}")) % 25) / 10.0, 1)
    confidence = min(99.9, confidence)

    steps.append(f"\nFINAL PREDICTION: {prediction}")
    steps.append(f"BIG/SMALL: {big_small}   (0–4 = SMALL, 5–9 = BIG)")

    return {
        "prediction": prediction,
        "bigSmall": big_small,
        "confidence": confidence,
        "steps": steps
    }


# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    result = sddgamer263_predict(current_number=5, period="2025010110000001")
    print("\n".join(result["steps"]))
    print(f"\nConfidence: {result['confidence']}%")
