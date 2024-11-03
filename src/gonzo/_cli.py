# ruff: disable=F401
import click

from gonzo.looklocker_t1map import looklocker_t1map
from gonzo.mixed_t1map import mixed_t1map
from gonzo.hybrid_t1map import hybrid_t1map
from gonzo.t1maps import T1_to_R1, looklocker_t1_postprocessing
from gonzo.t1_weighted import T1w_sigdiff, T1w_normalize
from gonzo.masking import mask_intracranial, mask_csf
from gonzo.segmentation_refinement import refine
from gonzo.orbital_refroi import orbital_refroi
from gonzo.concentration import concentration
from gonzo.reslice_4d import reslice4d


@click.group()
def mri():
    pass


mri.add_command(mixed_t1map)
mri.add_command(looklocker_t1map)
mri.add_command(looklocker_t1_postprocessing)
mri.add_command(hybrid_t1map)
mri.add_command(T1_to_R1)

mri.add_command(T1w_sigdiff)
mri.add_command(T1w_normalize)

mri.add_command(concentration)
mri.add_command(reslice4d)


@click.group()
def seg():
    pass


seg.add_command(refine)
seg.add_command(mask_intracranial)
seg.add_command(mask_csf)
seg.add_command(orbital_refroi)
