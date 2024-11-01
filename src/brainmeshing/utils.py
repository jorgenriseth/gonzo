from pathlib import Path
from typing import Literal

import pyvista as pv
import SVMTK as svmtk
import dolfin as df
import numpy as np


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


def map_subdomains_to_boundaries(mesh, subdomains):
    mesh.init()
    d = mesh.topology().dim()
    boundaries = df.MeshFunction("size_t", mesh, d - 1, 2)
    facet_labels = np.zeros_like(boundaries.array())
    for facet in df.facets(mesh):
        ent = facet.entities(d)
        if len(ent) == 1:
            facet_labels[facet.index()] = subdomains.array()[ent[0]]
    boundaries.array()[:] = facet_labels
    return boundaries


def map_boundaries_to_subdomains(mesh, boundaries):
    mesh.init()
    d = mesh.topology().dim()
    subdomains = df.MeshFunction("size_t", mesh, d, 0)
    cell_labels = np.zeros_like(subdomains.array())
    boundary_facets = [
        facet.index() for facet in df.facets(mesh) if len(facet.entities(d)) == 1
    ]
    for cell in df.cells(mesh):
        cell_facets = cell.entities(d - 1)
        cell_boundary_facets = cell_facets[np.isin(cell_facets, boundary_facets)]
        if len(cell_boundary_facets) > 0:
            cell_boundary_tags = boundaries.array()[:][cell_boundary_facets]
            values, counts = np.unique(cell_boundary_tags, return_counts=True)
            cell_labels[cell.index()] = values[counts.argmax()]
    subdomains.array()[:] = cell_labels
    return subdomains


def tagged_facet_extraction(input: Path, output):
    # Load the tetrahedral mesh
    mesh = pv.read(input)  # Or create mesh here
    if mesh is None:
        raise ValueError(f"Can't load mesh from {input}")

    # Assuming cell tags are stored in 'cell_tags'
    cell_tags = mesh.cell_data["subdomains"]

    # Check if all cells are tetrahedra
    from vtk import VTK_TETRA

    if not np.all(mesh.celltypes == VTK_TETRA):
        raise ValueError("The mesh must contain only tetrahedral cells.")

    # Extract cell connectivity
    cells = mesh.cells.reshape(-1, 5)
    assert np.all(cells[:, 0] == 4)  # Ensure all cells have 4 points
    cell_point_ids = cells[:, 1:]

    # Build face-cell mapping
    face_dict = {}
    for cell_id, cell_points in enumerate(cell_point_ids):
        faces = [
            tuple(sorted([cell_points[0], cell_points[1], cell_points[2]])),
            tuple(sorted([cell_points[0], cell_points[1], cell_points[3]])),
            tuple(sorted([cell_points[0], cell_points[2], cell_points[3]])),
            tuple(sorted([cell_points[1], cell_points[2], cell_points[3]])),
        ]
        for face in faces:
            if face in face_dict:
                face_dict[face]["cells"].append(cell_id)
            else:
                face_dict[face] = {"cells": [cell_id]}

    # Assign tags to faces
    subdomain_pair_to_id = {}
    current_id = cell_tags.max() + 1  # Start from 1 since 0 is reserved
    face_data = []

    for face, data in face_dict.items():
        cells_adjacent = data["cells"]
        if len(cells_adjacent) == 1:
            # Boundary face
            cell_id = cells_adjacent[0]
            face_tag = cell_tags[cell_id]
        elif len(cells_adjacent) == 2:
            # Internal face
            cell_id1, cell_id2 = cells_adjacent
            tag1 = cell_tags[cell_id1]
            tag2 = cell_tags[cell_id2]
            if tag1 == tag2:
                face_tag = 0
            else:
                subdomain_pair = tuple(sorted((tag1, tag2)))
                if subdomain_pair not in subdomain_pair_to_id:
                    subdomain_pair_to_id[subdomain_pair] = current_id
                    current_id += 1
                face_tag = subdomain_pair_to_id[subdomain_pair]
        else:
            raise ValueError(
                "A face is adjacent to more than two cells, which should not happen."
            )
        face_data.append({"face": face, "tag": face_tag})

    # Prepare faces and tags for PolyData
    faces_list = []
    face_tags = []
    for face_info in face_data:
        face = face_info["face"]
        face_tag = face_info["tag"]
        faces_list.extend([3, face[0], face[1], face[2]])
        face_tags.append(face_tag)

    faces_array = np.array(faces_list)
    face_tags = np.array(face_tags)

    # Create the face mesh
    face_mesh = pv.PolyData(mesh.points, faces_array)
    face_mesh.cell_data["face_tags"] = face_tags

    # Save the result
    face_mesh.save(output)
