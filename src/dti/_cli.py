import click

from dti.clean_dti_data import clean
from dti.utils import create_eddy_index_file, create_topup_params_file


@click.group()
def dti():
    pass


dti.add_command(clean)
dti.add_command(create_eddy_index_file)
dti.add_command(create_topup_params_file)
