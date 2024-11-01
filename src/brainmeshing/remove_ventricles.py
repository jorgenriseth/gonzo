import pyvista as pv
import numpy as np


mesh = pv.read_meshio("mesh.xdmf")
all_labels = np.unique(mesh.cell_data["label"])
ventricles_label = all_labels.max()
brain_labels = all_labels[all_labels != ventricles_label]
brain = mesh.extract_values(brain_labels)
pv.save_meshio("brain.xdmf", brain)
