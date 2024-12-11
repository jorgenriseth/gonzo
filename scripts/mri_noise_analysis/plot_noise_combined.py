"""
Predicted concentration vs estimated concentrations
for the Look Locker and Mixed sequences with a given SNR
"""

import matplotlib.pyplot as plt
import click
from plot_noise_look_locker import plot_estimated_versus_actual as plot_look_locker
from plot_noise_mixed import plot_estimated_versus_actual as plot_mixed

@click.command()
@click.option("--snr", default=25, help="Signal to noise ratio")
@click.option("--samples", default=200, help="Number of samples")
@click.option("--sequence_duration", default=2.6, help="Sequence duration in seconds")
def main(snr, samples, sequence_duration=2.6):
    superfig = plt.figure(constrained_layout=True, figsize=(8, 5))
    figs = superfig.subfigures(nrows=2, ncols=1)

    figs[0].suptitle(f'concentration and T1 from Look-Locker sequence')
    ax = figs[0].subplots(1, 2)
    plot_look_locker(ax_c=ax[0], ax_t1=ax[1], snr=snr, samples=samples, sequence_duration=sequence_duration)

    figs[1].suptitle(f'concentration and T1 from Mixed sequence')
    ax = figs[1].subplots(1, 2)
    plot_mixed(ax_c=ax[0], ax_t1=ax[1], snr=snr, samples=samples)
    superfig.savefig("mri_noise_ll_mixed.png", dpi=600)
    superfig.savefig("mri_noise_ll_mixed_small.png", dpi=72)

    plt.show()


if __name__ == "__main__":
    main()
