"""
Adjusted version of script from original MRI2FEM-book according to below license.
'''
Copyright (c) 2020 Kent-Andre Mardal, Marie E. Rognes, Travis B. Thompson, Lars Magnus Valnes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
"""

import argparse
from pathlib import Path


import numpy as np
import nibabel
import dolfin as df
from ufl import tr, sqrt, inner, dev

from nibabel.affines import apply_affine

import pantarei as pr

from simple_mri import SimpleMRI
from gonzo.clean_dti_data import extend_to_9_component_array


def mean_diffusivity(Dvector: np.ndarray) -> np.ndarray:
    return Dvector[..., ::4].sum() / 3.0


def adjusting_mean_diffusivity(Dvector: np.ndarray, subdomains, tags_with_limits):
    MD = mean_diffusivity(Dvector)
    # Reads the tag and the minimum and maximum mean diffusivity limit
    # for that tag subdomain.
    for tag, mn, mx in tags_with_limits:
        # If the minimum or maximum mean diffusivity limit is set to zero,
        # then the limit is considered void.
        usr_max = float(mx) if mx != 0 else np.inf
        usr_min = float(mn) if mn != 0 else -np.inf

        # creates a mask for all degrees of freesom that are within the
        # subdomain with the tag and is above the maximum limit or
        # below the minimum limit.
        max_mask = (subdomains.array() == tag) * (MD > usr_max)
        min_mask = (subdomains.array() == tag) * (MD < usr_min)

        # Sets values that are either above or below limits to the closest limit.
        Dvector[max_mask] = usr_max * np.divide(
            Dvector[max_mask], MD[max_mask, np.newaxis]
        )
        Dvector[min_mask] = usr_min * np.divide(
            Dvector[min_mask], MD[min_mask, np.newaxis]
        )


def dti_data_to_mesh(meshfile: Path, dti: Path, outfile: Path, label=None):
    mesh = df.Mesh()
    hdf = df.HDF5File(mesh.mpi_comm(), meshfile, "r")
    hdf.read(mesh, "domain/mesh", False)

    d = mesh.topology().dim()
    subdomains = df.MeshFunction("size_t", mesh, d)
    hdf.read(subdomains, "domain/subdomains")
    boundaries = df.MeshFunction("size_t", mesh, d - 1)
    hdf.read(boundaries, "domain/boundaries")
    hdf.close()

    dti_image = nibabel.load(dti)
    dti_data = dti_image.get_fdata().squeeze()
    dti_data = extend_to_9_component_array(dti_data)
    print(dti_data.shape)

    vox2ras = dti_image.affine
    ras2vox = np.linalg.inv(vox2ras)

    # Create a FEniCS tensor field:
    DG09 = df.TensorFunctionSpace(mesh, "DG", 0)
    D = df.Function(DG09)

    # Get the coordinates xyz of each degree of freedom
    DG0 = df.FunctionSpace(mesh, "DG", 0)
    imap = DG0.dofmap().index_map()
    num_dofs_local = imap.local_range()[1] - imap.local_range()[0]
    xyz = DG0.tabulate_dof_coordinates()
    xyz = xyz.reshape((num_dofs_local, -1))

    # Convert to voxel space and round off to find
    # voxel indices
    ijk = apply_affine(ras2vox, xyz).T
    i, j, k = np.rint(ijk).astype("int")

    D1 = dti_data[i, j, k]
    print(D1.shape)

    # Further manipulate data (described better later)
    if label:
        adjusting_mean_diffusivity(D1, subdomains, label)

    # Assign the output to the tensor function
    D.vector()[:] = D1.reshape(-1)

    # Compute other functions
    md = 1.0 / 3.0 * tr(D)
    MD = df.project(md, DG0, solver_type="cg", preconditioner_type="amg")
    fa = sqrt((3.0 / 2.0) * inner(dev(D), dev(D)) / inner(D, D))
    FA = df.project(fa, DG0)

    # Now store everything to a new file - ready for use!
    domain = pr.Domain(mesh, subdomains, boundaries)
    hdf = df.HDF5File(mesh.mpi_comm(), outfile, "w")
    pr.write_domain(hdf, domain)
    pr.write_function(hdf, D, "DTI")
    pr.write_function(hdf, MD, "MD")
    pr.write_function(hdf, FA, "FA")
    hdf.close()


if __name__ == "__main__":
    # TODO: Write about arguments or simplify in the book!
    parser = argparse.ArgumentParser()
    parser.add_argument("--dti", type=str, default="")
    parser.add_argument("--mesh", type=str)
    parser.add_argument("--out", type=str)
    parser.add_argument(
        "--label",
        type=float,
        action="append",
        nargs=3,
        help="--label TAG MIN MAX. The value of zero is considered void.",
    )
    Z = parser.parse_args()

    dti_data_to_mesh(Z.mesh, Z.dti, Z.out, Z.label)
