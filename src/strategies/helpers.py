import pandas as pd

def gt(a, b):
    # cả 2 là Series
    if hasattr(a, "notna") and hasattr(b, "notna"):
        return (a > b) & a.notna() & b.notna()

    # a là Series, b là scalar
    if hasattr(a, "notna"):
        return (a > b) & a.notna()

    # fallback (scalar vs scalar)
    return a > b
def lt(a, b):
    return a.notna() & b.notna() & (a < b)

def crossover(a, b):
    return (
        a.notna() & b.notna() &
        (a > b) &
        (a.shift(1) <= b.shift(1))
    )
