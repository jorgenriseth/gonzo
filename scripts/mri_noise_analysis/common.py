r1 = r1 = 4.5e-3  # l/mmol/ms
T01 = 4500  # ms
R01 = 1.0 / T01


def compute_c(T1):
    return (1.0 / T1 - R01) / r1


def compute_T1(c):
    return 1.0 / (R01 + c * r1)
