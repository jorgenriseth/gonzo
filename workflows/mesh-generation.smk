rule convert_fs_surface_to_stl:
  input:
    expand(
      "mri_processed_data/fastsurfer/{{subject}}/surf/{surf}",
      surf=["lh.pial", "rh.pial", "lh.white", "rh.white"]
    )
  output:
    expand(
        "mri_processed_data/{{subject}}/modeling/surfaces/{surf}.stl",
        surf=["lh_pial", "rh_pial", "lh_white", "rh_white"],
    )
  params: fs_license = "docker/license.txt"
  container: None
  shell:
    "python scripts/convert_surfaces.py"
    " -s $(dirname {input[0]})"
    " -o $(dirname {output[0]})"
    " -l {params.fs_license}"

rule preprocess_surfaces:
  input:
    "mri_processed_data/fastsurfer/{subject}/mri/aseg.mgz",
    expand(
        "mri_processed_data/{{subject}}/modeling/surfaces/{surf}.stl",
        surf=["lh_pial", "rh_pial", "lh_white", "rh_white"],
    )
  output:
    "mri_processed_data/{subject}/modeling/surfaces/lh_pial_refined.stl",
    "mri_processed_data/{subject}/modeling/surfaces/rh_pial_refined.stl",
    "mri_processed_data/{subject}/modeling/surfaces/subcortical_gm.stl",
    "mri_processed_data/{subject}/modeling/surfaces/white.stl",
  threads: 6
  shell:
    "gmri2fem brainmeshing process-surfaces"
    " --fs_dir $(dirname $(dirname {input[0]}))"
    " --surface_dir $(dirname {output[0]})"

rule extract_ventricles:
  input:
    "mri_processed_data/fastsurfer/{subject}/mri/aseg.mgz",
  output:
    "mri_processed_data/{subject}/modeling/surfaces/ventricles.stl",
  threads: 6
  shell:
    "gmri2fem brainmeshing extract-ventricles"
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
  threads: 6
  shell:
    "gmri2fem brainmeshing meshgen"
    " --surface_dir $(dirname {input[0]})"
    " --resolution {wildcards.res}"
    " --output {output.hdf}"


rule mesh_segmentation:
  input:
    seg="mri_processed_data/fastsurfer/{subject}/mri/{seg}.mgz",
    mesh="mri_processed_data/{subject}/modeling/resolution{res}/mesh.hdf",
  output:
    "mri_processed_data/{subject}/modeling/resolution{res}/mesh_{seg}.hdf"
  shell:
    "gmri2fem i2m subdomains"
    " {input} {output}"

