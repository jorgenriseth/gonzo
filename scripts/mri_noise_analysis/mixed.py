import numpy as np
import scipy.interpolate

# Metadata for the Mixed sequence
metadata = {"TR_ir": 8350.0, "TR_se": 11000.0, "TI": 2650.0, "TE": 700.0}


def compute_se_signal(T1, SNR=20):
    M0 = 1  # will cancel out
    TR = metadata["TR_se"] - 2 * metadata["TE"]
    se = M0 * (1.0 - np.exp(-TR / T1))
    max_se = np.max(se)
    return se + np.random.rayleigh(max_se / SNR, se.shape)


def compute_ir_signal(T1, SNR=20):
    se = compute_se_signal(T1)
    M0 = 1  # will cancel out
    TI = metadata["TI"]
    ir = M0 - (M0 + se) * np.exp(-TI / T1)
    max_ir = np.max(ir)
    return ir + np.random.normal(0, max_ir / SNR, ir.shape)


def T1_lookup_table(TRse, TI, TE, T1_low, T1_hi):
    M0 = 1  # arbitrary value because it cancels out
    T1_grid = np.linspace(T1_low, T1_hi, 10000, endpoint=True)
    TR = TRse - 2 * TE
    Sse = M0 * (1 - np.exp(-TR / T1_grid))
    Sir = M0 - (M0 + Sse) * np.exp(-TI / T1_grid)
    fractionCurve = Sir / Sse
    return fractionCurve, T1_grid


def extract_mixed_t1(IR: np.ndarray, SE: np.ndarray, lookup_table) -> np.ndarray:
    F, T1_grid = lookup_table
    F_data = IR / SE
    interpolator = scipy.interpolate.interp1d(
        F, T1_grid, kind="nearest", bounds_error=False, fill_value=np.nan
    )
    T1_volume = interpolator(F_data)
    return T1_volume


LOOKUP_TABLE = T1_lookup_table(
    metadata["TR_se"], metadata["TI"], metadata["TE"], 1, 10000
)
