import click
from gonzo._cli import mri
from brainmeshing._cli import brainmeshing


@click.group()
def gmri2fem():
    pass


gmri2fem.add_command(mri)
gmri2fem.add_command(brainmeshing)
