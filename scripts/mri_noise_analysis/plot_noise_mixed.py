"""
Predicted concentration vs estimated concentrations
for the Mixed sequence with a given SNR
"""

import matplotlib.pyplot as plt
import numpy as np
import click

from common import compute_T1, compute_c
from mixed import compute_ir_signal, compute_se_signal, LOOKUP_TABLE, extract_mixed_t1


def generate_mixed_data(snr, samples):
    # reproducibility
    np.random.seed(0)

    # test different concentrations for a given noise level
    repeats = 50
    c_values = np.linspace(0.005, 0.3, samples)
    T1_values = compute_T1(c_values)
    c = np.vstack([c_values for _ in range(repeats)]).T
    T1 = compute_T1(c)

    # generate noisy IR and SE signals
    IR = compute_ir_signal(T1, SNR=snr)
    SE = compute_se_signal(T1, SNR=snr)

    # estimate the concentration and T1 values from the noisy signals
    T1_est = extract_mixed_t1(IR=IR, SE=SE, lookup_table=LOOKUP_TABLE)
    c_est = compute_c(T1_est)

    T1 = T1 / 1000
    T1_est = T1_est / 1000
    T1_values = T1_values / 1000

    c_threshold = 0.1
    T1_threshold = compute_T1(c_threshold) * 0.001

    return c, c_est, T1, T1_est, c_values, T1_values, c_threshold, T1_threshold


def plot_estimated_versus_actual(snr, samples, ax_c=None, ax_t1=None):

    c, c_est, T1, T1_est, c_values, T1_values, c_threshold, T1_threshold = generate_mixed_data(snr, samples)

    fontsize = 12
    if ax_c is not None:
        ax_c.scatter(c, c_est, s=0.5, color="grey", alpha=0.2, label="simulated")
        c_max, c_min = np.max(c), np.min(c)
        ax_c.plot(c_values, np.nanmean(c_est, axis=1), color="red", label="mean(sim)")
        ax_c.plot([c_min, c_max], [c_min, c_max], "--", color="black", label="identity")
        ax_c.set_xlabel("True c (mmol/l)", fontsize=fontsize)
        ax_c.set_ylabel("Estimated c (mmol/l)", fontsize=fontsize)
        ax_c.annotate(
            f'SNR={snr}',
            xy=(0.04, 0.96), xycoords='axes fraction',
            color='black', fontsize=fontsize,
            ha='left', va='top',
        )
        ax_c.axvline(c_threshold, color="black", linestyle="-.")
        leg = ax_c.legend(loc="upper right", frameon=False, markerscale=5.)
        for lh in leg.legend_handles:
            lh.set_alpha(1)

    if ax_t1 is not None:
        ax_t1.scatter(T1, T1_est, s=0.5, color="grey", alpha=0.2, label="simulated")
        T1_max, T1_min = np.max(T1), np.min(T1)
        ax_t1.plot(T1_values, np.nanmean(T1_est, axis=1), color="red", label="mean(sim)")
        ax_t1.plot([T1_min, T1_max], [T1_min, T1_max], "--", color="black", label="identity")
        ax_t1.set_xlabel("True T1 (s)", fontsize=fontsize)
        ax_t1.set_ylabel("Estimated T1 (s)", fontsize=fontsize)
        ax_t1.annotate(
            f'SNR={snr}',
            xy=(0.04, 0.96), xycoords='axes fraction',
            color='black', fontsize=fontsize,
            ha='left', va='top',
        )
        ax_t1.axvline(T1_threshold, color="black", linestyle="-.")
        ax_t1.invert_xaxis()
        leg = ax_t1.legend(loc="lower left", frameon=False, markerscale=5.)
        for lh in leg.legend_handles:
            lh.set_alpha(1)


@click.command()
@click.option("--snr", default=25, help="Signal to noise ratio")
@click.option("--samples", default=100, help="Number of samples")
def main(snr, samples):
    fig, ax = plt.subplots(1, 2, figsize=(8, 3))
    plot_estimated_versus_actual(ax_c=ax[0], ax_t1=ax[1], snr=snr, samples=samples)
    fig.suptitle("concentration and T1 from Mixed sequence")
    fig.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
