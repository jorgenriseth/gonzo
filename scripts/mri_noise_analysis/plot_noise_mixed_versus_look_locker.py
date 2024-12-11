"""
Plot estimated look-locker versus mixed data
"""

import click
import matplotlib.pyplot as plt
import numpy as np

from plot_noise_look_locker import generate_look_locker_data
from plot_noise_mixed import generate_mixed_data

def plot_mixed_versus_look_locker(snr, samples, sequence_duration, ax_c=None, ax_t1=None):

    ll_c, ll_c_est, ll_T1, ll_T1_est, ll_c_values, ll_T1_values, ll_c_threshold, ll_T1_threshold = generate_look_locker_data(snr, samples, sequence_duration)
    mx_c, mx_c_est, mx_T1, mx_T1_est, mx_c_values, mx_T1_values, mx_c_threshold, mx_T1_threshold = generate_mixed_data(snr, samples)

    fontsize = 12

    if ax_c is not None:
        ax_c.scatter(ll_c_est, mx_c_est, s=1, c="gray", alpha=0.5, label="simulated")
        ax_c.plot(ll_c_values, ll_c_values, "k--", lw=1, label="identity")
        ax_c.set_xlabel("Look-Locker c (mmol/l)", fontsize=fontsize)
        ax_c.set_ylabel("Mixed c (mmol/l)", fontsize=fontsize)
        ax_c.annotate(
            f'SNR={snr}',
            xy=(0.04, 0.96), xycoords='axes fraction',
            color='black', fontsize=fontsize,
            ha='left', va='top',
        )
        ax_c.axvline(ll_T1_threshold, color="black", linestyle="-.")
        leg = ax_c.legend(loc="upper right", frameon=False, markerscale=5.)
        for lh in leg.legend_handles:
            lh.set_alpha(1)


    # plot estimated T1 values over true concentration
    if ax_t1 is not None:
        ax_t1.scatter(ll_T1_est, mx_T1_est, s=1, c="gray", alpha=0.5, label="simulated")
        ax_t1.plot(ll_T1_values, ll_T1_values, "k--", lw=1, label="identity")
        ax_t1.set_xlabel("Look-Locker T1 (s)", fontsize=fontsize)
        ax_t1.set_ylabel("Mixed T1 (s)", fontsize=fontsize)
        ax_t1.annotate(
            f'SNR={snr}',
            xy=(0.04, 0.96), xycoords='axes fraction',
            color='black', fontsize=fontsize,
            ha='left', va='top',
        )
        ax_t1.axvline(ll_T1_threshold, color="black", linestyle="-.")
        ax_t1.set_xlim(np.min(ll_T1_values), np.max(ll_T1_values))
        ax_t1.invert_xaxis()
        leg = ax_t1.legend(loc="lower left", frameon=False, markerscale=5.)
        for lh in leg.legend_handles:
            lh.set_alpha(1)


@click.command()
@click.option("--snr", default=25, help="Signal to noise ratio")
@click.option("--samples", default=200, help="Number of samples")
@click.option("--sequence_duration", default=2.6, help="Sequence duration in seconds")
def main(snr, samples, sequence_duration=2.6):
    fig, ax = plt.subplots(1, 2, figsize=(8, 3))
    plot_mixed_versus_look_locker(ax_c=ax[0], ax_t1=ax[1], snr=snr, samples=samples, sequence_duration=sequence_duration)
    fig.suptitle("Mixed versus Look-Locker sequence")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()