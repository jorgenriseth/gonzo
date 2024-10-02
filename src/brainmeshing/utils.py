from typing import Literal

import pyvista as pv
import SVMTK as svmtk


def print_edge_info(mesh: pv.UnstructuredGrid):
    edges = mesh.extract_all_edges()
    edge_lengths = edges.compute_cell_sizes(length=True)["Length"]  # type: ignore
    print(f"Min edge length: {edge_lengths.min()}")
    print(f"Max edge length: {edge_lengths.max()}")
    print(f"Mean edge length: {edge_lengths.mean()}")


def replace_at_index(s: str, idx: int, value: Literal["0", "1"]) -> str:
    return s[:idx] + value + s[idx + 1 :]


def expand_subdomain_string(smap_string: str) -> list[str]:
    idx = smap_string.find(".")
    if idx == -1:
        return [smap_string]
    else:
        return expand_subdomain_string(
            replace_at_index(smap_string, idx, "0")
        ) + expand_subdomain_string(replace_at_index(smap_string, idx, "1"))


def subdomain_mapper(smap: svmtk.SubdomainMap, smap_string: str, tag: int):
    for s in expand_subdomain_string(smap_string):
        smap.add(s, tag)
    return smap
