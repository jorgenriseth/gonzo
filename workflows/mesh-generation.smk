rule preprocess_surfaces:
  input:
    "mri_processed_data/fastsurfer/{subject}/mri/aseg.mgz",
    expand(
      "mri_processed_data/fastsurfer/{{subject}}/surf/{surf}",
      surf=["lh.pial", "rh.pial", "lh.white", "rh.white"]
    )
  output:
    "mri_processed_data/{subject}/modeling/surfaces/lh_pial_refined.stl",
    "mri_processed_data/{subject}/modeling/surfaces/rh_pial_refined.stl",
    "mri_processed_data/{subject}/modeling/surfaces/subcortical_gm.stl",
    "mri_processed_data/{subject}/modeling/surfaces/ventricles.stl",
    "mri_processed_data/{subject}/modeling/surfaces/white.stl",
  shell:
    "gmri2fem brainmeshing process-surfaces"
    " --fs_dir $(dirname $(dirname {input[0]}))"
    " --surface_dir $(dirname {output[0]})"


rule generate_mesh:
  input:
    "mri_processed_data/{subject}/modeling/surfaces/lh_pial_refined.stl",
    "mri_processed_data/{subject}/modeling/surfaces/rh_pial_refined.stl",
    "mri_processed_data/{subject}/modeling/surfaces/subcortical_gm.stl",
    "mri_processed_data/{subject}/modeling/surfaces/ventricles.stl",
    "mri_processed_data/{subject}/modeling/surfaces/white.stl",
  output:
    hdf="mri_processed_data/{subject}/modeling/resolution{res}/mesh.hdf",
    xdmf="mri_processed_data/{subject}/modeling/resolution{res}/mesh_xdmfs/subdomains.xdmf"
  shell:
    "gmri2fem brainmeshing mesh-generation"
    " --surface_dir $(dirname {input[0]})"
    " --resolution {wildcards.res}"
    " --output {output.hdf}"


rule mesh_segmentation:
  input:
    seg="mri_processed_data/fastsurfer/{subject}/mri/aparc+aseg.mgz",
    mesh="mri_processed_data/{subject}/modeling/resolution{res}/mesh.hdf",
  output:
    "mri_processed_data/{subject}/modeling/resolution{res}/mesh_aparc.hdf"
  shell:
    "gmri2fem i2m subdomains"
    " {input} {output}"
