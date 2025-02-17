rule collect:
  input:
    mesh="mri_processed_data/{subject}/modeling/resolution{res}/mesh.hdf",
    dti="mri_processed_data/{subject}/modeling/resolution{res}/dti.hdf",
    concentration="mri_processed_data/{subject}/modeling/resolution{res}/concentrations.hdf",
    parcellations="mri_processed_data/{subject}/modeling/resolution{res}/mesh_aparc.hdf"
  output:
    "mri_processed_data/{subject}/modeling/resolution{res}/data.hdf"
  shell:
    "gmri2fem i2m collect"
      " --domain {input.mesh}"
      " --dti_data {input.dti}"
      " --concentration_data {input.concentration}"
      " --parcellation_data {input.parcellations}"
      " --output {output}"

rule mri2fenics:
  input:
    mesh="mri_processed_data/{subject}/modeling/resolution{res}/mesh.hdf",
    concentrations= lambda wc: [
      f"mri_processed_data/{{subject}}/concentrations/{{subject}}_{session}_concentration.nii.gz"
      for session in SESSIONS[wc.subject]
    ],
    csfmask="mri_processed_data/{subject}/segmentations/{subject}_seg-csf_binary.nii.gz",
    timetable="mri_dataset/timetable.tsv"
  output:
    hdf="mri_processed_data/{subject}/modeling/resolution{res}/concentrations.hdf",
    visual=[
      "mri_processed_data/{subject}/modeling/resolution{res}/visual/concentrations_internal.xdmf",
      "mri_processed_data/{subject}/modeling/resolution{res}/visual/concentrations_boundary.xdmf",
    ]
  params:
    femfamily="CG",
    femdegree=1,
  shell:
    "gmri2fem i2m concentrations2mesh"
    " {input.concentrations}"
    " --meshpath {input.mesh}"
    " --csfmask_path {input.csfmask}"
    " --timetable {input.timetable}"
    " --output {output.hdf}"
    " --femfamily {params.femfamily}"
    " --femdegree {params.femdegree}"
    " --visualdir $(dirname {output.visual[0]})"


rule dti2fenics:
  input:
    meshfile="mri_processed_data/{subject}/modeling/resolution{res}/mesh.hdf",
    dti="mri_processed_data/{subject}/dwi/{subject}_ses-01_dDTI_cleaned.nii.gz",
    md = "mri_processed_data/{subject}/registered/{subject}_ses-01_dDTI_MD_registered.nii.gz",
    fa = "mri_processed_data/{subject}/registered/{subject}_ses-01_dDTI_FA_registered.nii.gz",
    mask= "mri_processed_data/{subject}/segmentations/{subject}_seg-aseg_refined.nii.gz",
  output:
    hdf="mri_processed_data/{subject}/modeling/resolution{res}/dti.hdf",
  shell:
    "gmri2fem i2m dti2mesh"
    " --mesh {input.meshfile}"
    " --dti {input.dti}"
    " --md {input.md}"
    " --fa {input.fa}"
    " --mask {input.mask}"
    " --output {output.hdf}"

rule hdf2vtk:
    input:
        "mri_processed_data/{subject}/modeling/resolution{res}/data.hdf"
    output:
        "mri_processed_data/{subject}/modeling/resolution{res}/data.vtu"
    shell:
        "gmri2fem i2m hdf2vtk"
        " --input {input}"
        " --output {output}"
        " --ascii"




rule extract_concentration_times_LL:
  input:
    "mri_dataset/timetable.tsv"
  output:
    temp("mri_processed_{subject}/modeling/timestamps_LL.txt"),
  shell:
    "python scripts/extract_timestamps.py"
      " --timetable {input}"
      " --subject {wildcards.subject}"
      " --sequence_label looklocker"
      " --output {output}"


rule fenics2mri_workflow:
  input:
    referenceimage="mri_processed_data/{subject}/registered/{subject}_ses-01_T1w_registered.nii.gz",
    simulationfile="mri_processed_data/{subject}/modeling/resolution{res}/{funcname}.hdf",
    timestampfile="{subject}/timestamps_ll.txt",
  output:
    "{subject}/modeling/resolution{res}/mris/{funcname}_{idx}.nii.gz",
  shell:
    "python gmri2fem/mriprocessing/fenics2mri.py"
      " --simulationfile {input.simulationfile}"
      " --output {output}"
      " --referenceimage {input.referenceimage}"
      " --timestamps {input.timestampfile}"
      " --timeidx {wildcards.idx}"
      " --functionname 'total_concentration'"


rule fenics2mri_pseudoinverse:
  input:
    expand(
      "{subject}/modeling/resolution{res}/mris/data_{idx}.nii.gz",
      subject=SUBJECTS,
      res=config["resolution"],
      idx=range(5)
    )

