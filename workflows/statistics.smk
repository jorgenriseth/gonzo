rule concentration_stats:
    input:
      segmentation="mri_processed_data/{subject}/segmentations/{subject}_seg-extended-fs.nii.gz",
      mris=lambda wc: [f"mri_processed_data/{wc.subject}/concentrations/{wc.subject}_{ses}_concentration.nii.gz"
      for ses in SESSIONS[wc.subject] if Path(f"mri_processed_data/{wc.subject}/concentrations/{wc.subject}_{ses}_concentration.nii.gz").exists()],
      timestamps="mri_dataset/timetable.tsv",
    output:
      "mri_processed_data/{subject}/statistics/{subject}_stats-concentration-extended-fs.csv"
    params:
      mris=lambda wildcards, input: " ".join([f"-m {f}" for f in input.mris])
    shell:
      "gmri2fem mri stats"
      " -s {input.segmentation}"
      " {params.mris}"
      " -o {output}"
      " --timetable {input.timestamps}"
      " --timelabel 'looklocker'"

