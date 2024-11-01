from pathlib import Path
import dolfin as df
import pantarei as p


def collect_mesh_data(
    domain_data: Path,
    dti_data: Path,
    concentration_data: Path,
    parcellation_data: Path,
    output: Path,
):
    hdf = df.HDF5File(df.MPI.comm_world, str(output), "w")

    domain_hdf = df.HDF5File(df.MPI.comm_world, str(domain_data), "r")
    domain = pr.read_domain(domain_hdf)
    pr.write_domain(hdf, domain)
    pr.close(domain_hdf)

    concentration_hdf = df.HDF5File(df.MPI.comm_world, str(concentration_data), "r")
    for funcname in ["concentration", "boundary_concentration"]:
        func = pr.read_function(concentration_hdf, funcname, domain)
        time = pr.read_timevector(concentration_hdf, funcname)
        pr.write_function(hdf, func, funcname)
        for idx, ti in enumerate(time[1:], start=1):
            pr.read_checkpoint(concentration_hdf, func, funcname, idx)
            pr.write_checkpoint(hdf, func, funcname, ti)
    pr.close(concentration_hdf)

    dti_hdf = df.HDF5File(df.MPI.comm_world, str(dti_data), "r")
    for funcname in ["DTI", "FA", "MD"]:
        func = pr.read_function(dti_hdf, funcname, domain)
        pr.write_function(hdf, func, funcname)
    pr.close(dti_hdf)

    parcellation_hdf = df.HDF5File(df.MPI.comm_world, str(parcellation_data), "r")
    subdomains = df.MeshFunction("size_t", domain, domain.topology().dim())
    parcellation_hdf.read(subdomains, "parcellations")
    hdf.write(subdomains, "parcellations")
