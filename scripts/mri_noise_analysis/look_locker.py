import warnings
from functools import wraps
from time import time

import numpy as np
from scipy.optimize import OptimizeWarning, curve_fit, direct


def time_this_function(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print("func:%r args:[%r, %r] took: %2.4f sec" % (f.__name__, args, kw, te - ts))
        return result

    return wrap


X3_CANDIDATES = [np.sqrt(1 / T1) for T1 in [1.0, 2.0, 3.0, 4.0, 0.5]]


def curve_fit_kernel(f, t, data, minimizer, **kwargs):
    def loss(p):
        return np.sum((f(t, *p) - data) ** 2)

    res = minimizer(loss, **kwargs)
    return res.x, res.fun


@np.errstate(divide="raise", invalid="raise", over="raise")
def curve_fit_wrapper(f, t, y, p0):
    with warnings.catch_warnings():
        warnings.simplefilter("error", OptimizeWarning)

        # rescale data
        ymax = np.max(y)
        y = y / ymax

        # fit
        found_solution = False
        for x3 in X3_CANDIDATES:
            p0 = np.array([1.0, 2.0, x3])
            try:
                popt, _, info, _, _ = curve_fit(
                    f, xdata=t, ydata=y, p0=p0, full_output=True
                )
            except (OptimizeWarning, RuntimeError):
                continue
            if np.linalg.norm(info["fvec"]) < 0.1:
                found_solution = True
                break

        if found_solution is False:
            popt, _ = curve_fit_kernel(
                f, t=t, data=y, minimizer=direct, bounds=[(0, 5), (0, 5), (0, 3)]
            )

        # scale back
        popt[0] *= ymax

    return popt
