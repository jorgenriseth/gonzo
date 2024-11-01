import click
from pathlib import Path
import pyvista as pv
import numpy as np
import dolfin as df
import pantarei as pr

from i2m.collect_mesh_data import collect_mesh_data


@click.command()
@click.option("--domain", "domain_data", type=Path)
@click.option("--dti_data", type=Path)
@click.option("--concentration_data", type=Path)
@click.option("--parcellation_data", type=Path)
@click.option("--output", type=Path)
def main(*args, **kwargs):
    print("args:", args)
    print("kwargs:", kwargs)
    collect_mesh_data(*args, **kwargs)


if __name__ == "__main__":
    main()
