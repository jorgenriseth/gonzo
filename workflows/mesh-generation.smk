rule extract_ventricles:
  input:
    "mri_processed_data/freesurfer/{subject}/mri/aseg.mgz"
  output:
    "mri_processed_data/{subject}/modeling/surfaces/ventricles.stl"
  shell:
    "gmri2fem brainmeshing ventricle-surf"
    " -i {input}"
    " -o {output}"
    " --min_radius 2"
    " --initial_smoothing 1"
    " --surface_smoothing 1"
    " --taubin_iter 20"

rule separate_white_and_gray:
  input:
    lh_pial="mri_processed_data/freesurfer/{subject}/surf/lh.pial",
    lh_white="mri_processed_data/freesurfer/{subject}/surf/lh.white",
    rh_pial="mri_processed_data/freesurfer/{subject}/surf/rh.pial",
    rh_white="mri_processed_data/freesurfer/{subject}/surf/rh.white",
  output:
    lh_pial="mri_processed_data/{subject}/modeling/surfaces/lh_pial.stl",
    lh_white="mri_processed_data/{subject}/modeling/surfaces/lh_white.stl",
    rh_pial="mri_processed_data/{subject}/modeling/surfaces/rh_pial.stl",
    rh_white="mri_processed_data/{subject}/modeling/surfaces/rh_white.stl",
  shell:
    "gmri2fem brainmeshing separate-surfaces"
    " --fs_dir $(dirname {input.lh_pial})/.."
    " --outputdir $(dirname {output[0]})"

rule preprocess_white_surface:
  input:
    seg="mri_processed_data/freesurfer/{subject}/mri/aseg.mgz",
    lh_white="mri_processed_data/{subject}/modeling/surfaces/lh_white.stl",
    rh_white="mri_processed_data/{subject}/modeling/surfaces/rh_white.stl",
    ventricles="mri_processed_data/{subject}/modeling/surfaces/ventricles.stl"
  output:
    "mri_processed_data/{subject}/modeling/surfaces/white.stl"
  shell:
    "gmri2fem brainmeshing wm-surfaces"
    " --inputdir $(dirname {input.lh_white})"
    " --seg {input.seg}"
    " --ventricles {input.ventricles}"
    " --output {output}"
    " --tmpdir mri_processed_data/{wildcards.subject}/modeling/surfaces/"


rule preprocess_gray_matter_surface:
  input:
    seg="mri_processed_data/freesurfer/{subject}/mri/aseg.mgz",
    ventricles="mri_processed_data/{subject}/modeling/surfaces/ventricles.stl",
    lh_pial="mri_processed_data/{subject}/modeling/surfaces/lh_pial.stl",
    rh_pial="mri_processed_data/{subject}/modeling/surfaces/rh_pial.stl",
  output:
    lh="mri_processed_data/{subject}/modeling/surfaces/lh_pial_novent.stl",
    rh="mri_processed_data/{subject}/modeling/surfaces/rh_pial_novent.stl",
    subcort="mri_processed_data/{subject}/modeling/surfaces/subcortical_gm.stl"
  shell:
    "gmri2fem brainmeshing gm-surfaces"
    " --inputdir $(dirname {input.lh_pial})"
    " --seg {input.seg}"
    " --ventricles {input.ventricles}"
    " --outputdir $(dirname {output[0]})"

rule generate_mesh:
  input:
    expand(
      "mri_processed_data/{{subject}}/modeling/surfaces/{surf}.stl",
      surf=["lh_pial_novent", "rh_pial_novent", "subcortical_gm", "white"]
    )
  output:
    hdf="mri_processed_data/{subject}/modeling/resolution{res}/mesh.hdf",
    xdmf="mri_processed_data/{subject}/modeling/resolution{res}/mesh_xdmfs/subdomains.xdmf"
  shell:
    "gmri2fem brainmeshing meshgen"
    " --surfacedir $(dirname {input[0]})"
    " --resolution {wildcards.res}"
    " --output {output.hdf}"


rule mesh_segmentation:
  input:
    seg="mri_processed_data/freesurfer/{subject}/mri/aparc+aseg.mgz",
    mesh="mri_processed_data/{subject}/modeling/resolution{res}/mesh.hdf",
  output:
    "mri_processed_data/{subject}/modeling/resolution{res}/mesh_aparc.hdf"
  shell:
    "gmri2fem brainmeshing subdomains"
    " {input} {output}"
