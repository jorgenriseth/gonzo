from pathlib import Path

import click
import dolfin as df
import numpy as np
import tqdm
from gonzo.concentrations_to_mesh import nearest_neighbour
from gonzo.simple_mri import load_mri
from gonzo.utils import apply_affine
from pantarei import read_domain


@click.command("subdomains")
@click.argument("segmentation", type=Path, required=True)
@click.argument("meshpath", type=Path)
@click.argument("output", type=Path)
def main(*args, **kwargs):
    segments_to_mesh(*args, **kwargs)


def segments_to_mesh(
    segmentation: Path,
    meshpath: Path,
    output: Path,
):
    hdf = df.HDF5File(df.MPI.comm_world, str(meshpath), "r")
    domain = read_domain(hdf)
    mesh, subdomains, boundaries = domain, domain.subdomains, domain.boundaries
    hdf.close()
    d = mesh.topology().dim()

    segmentation_mri = load_mri(segmentation, dtype=int)
    seg = segmentation_mri.data
    affine = segmentation_mri.affine

    cell_midpoints = np.array([cell.midpoint()[:] for cell in df.cells(mesh)])
    cell_indices = np.array([cell.index() for cell in df.cells(mesh)])
    cell_voxel_indices = np.rint(
        apply_affine(np.linalg.inv(affine), cell_midpoints)
    ).astype(int)

    i, j, k = cell_voxel_indices.T

    vox2sub = np.zeros_like(seg)
    vox2sub[i, j, k] = subdomains.array()[cell_indices]

    valid_indices = np.array(np.where(seg != 0))
    cell_seg = seg[i, j, k]
    cell_seg = nearest_neighbour(seg, cell_voxel_indices, valid_indices).astype(int)

    # Create new array for the parcellation tags:
    N = mesh.num_cells()
    regions = np.zeros(N)

    subdomain_tags = np.unique(subdomains.array())
    for tag in tqdm.tqdm(subdomain_tags):
        masked_data = (vox2sub == tag) * seg
        for c in range(N):
            if subdomains[c] == tag:
                regions[c] = adjacent_tag(masked_data, i[c], j[c], k[c])

    subdomains.array()[:] = regions

    parcellations = df.MeshFunction("size_t", mesh, d, 0)
    parcellations.array()[cell_indices] = cell_seg[i, j, k]  # type: ignore
    with df.XDMFFile(mesh.mpi_comm(), str(output.with_suffix(".xdmf"))) as xdmf:
        xdmf.write(parcellations)

    hdf = df.HDF5File(mesh.mpi_comm(), str(output.with_suffix(".hdf")), "w")
    hdf.write(parcellations, "/parcellations")
    hdf.close()


def adjacent_tag(data, i, j, k, Mmin=3, Mmax=10):
    for m in range(Mmin, Mmax):
        values = data[i - m : i + m + 1, j - m : j + m + 1, k - m : k + m + 1]
        v = values.reshape(1, -1)
        pairs, counts = np.unique(v[v > 0], return_counts=True)

        # Return the most common non-zero tag:
        success = counts.size > 0
        if success:
            return pairs[counts.argmax()]

    return 0


if __name__ == "__main__":
    main()
