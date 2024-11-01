rule sequence_stats_collected:
  input:
    lambda wc: [
      f"mri_processed_data/{{subject}}/statistics/{{subject}}_{session}_{{sequence}}_statstable.csv"
      for session in SESSIONS[wc.subject]
    ]
  output:
    r"mri_processed_data/{subject}/statistics/{subject}_{sequence,(?!.*ses-\d{2}).+}_statstable.csv",
  shell:
    "python scripts/concat_tables.py"
    " --input {input}"
    " --output {output}"


rule subject_collected:
  input:
    [
      f"mri_processed_data/{{subject}}/statistics/{{subject}}_{seq}_statstable.csv"
      for seq in [
        # "T1w",
        "LookLocker", 
        "mixed",
        "concentration",
        "csf-concentration",
        # "T1w-signal-difference",
        # "T1w-csf-signal-difference",
      ]
    ]
  output:
    "mri_processed_data/{subject}/statistics/{subject}_statstable.csv",
  shell:
    "python scripts/concat_tables.py"
    " --input {input}"
    " --output {output}"



rule mri_region_stats:
    input:
      segmentation="mri_processed_data/{subject}/segmentations/{subject}_seg-aparc+aseg_refined.nii.gz",
      timestamps="mri_dataset/timetable.tsv",
      lutfile="mri_processed_data/freesurfer_lut.json"
    shell:
      "python src/gonzo/regionwise_statistics.py"
      " --subject {wildcards.subject}"
      " --subject_session {wildcards.session}"
      " --sequence {params.sequence}"
      " --timestamp_sequence {params.timestamp_sequence}"
      " --data {input.data}"
      " --seg {input.segmentation}"
      " --timestamps {input.timestamps}"
      " --lutfile {input.lutfile}"
      " --output {output}"

use rule mri_region_stats as LookLocker_stats with:
    input:
      segmentation="mri_processed_data/{subject}/segmentations/{subject}_seg-aparc+aseg_refined.nii.gz",
      timestamps="mri_dataset/timetable.tsv",
      lutfile="mri_processed_data/freesurfer_lut.json",
      data="mri_processed_data/{subject}/T1maps/{subject}_{session}_T1map.nii.gz"
    output:
      "mri_processed_data/{subject}/statistics/{subject}_{session}_LookLocker_statstable.csv"
    params:
      sequence="looklocker",
      timestamp_sequence="looklocker"


use rule mri_region_stats as T1w_stats with:
    input:
      segmentation="mri_processed_data/{subject}/segmentations/{subject}_seg-aparc+aseg_refined.nii.gz",
      timestamps="mri_dataset/timetable.tsv",
      lutfile="mri_processed_data/freesurfer_lut.json",
      data="mri_processed_data/{subject}/T1w_normalized/{subject}_{session}_T1w_normalized.nii.gz"
    output:
      "mri_processed_data/{subject}/statistics/{subject}_{session}_T1w_statstable.csv"
    params:
      sequence="T1w-normalized",
      timestamp_sequence="T1w"

use rule mri_region_stats as mixed_stats with:
    input:
      data="mri_processed_data/{subject}/T1maps/{subject}_{session}_T1map.nii.gz",
      segmentation="mri_processed_data/{subject}/segmentations/{subject}_seg-csf-aparc+aseg.nii.gz",
      timestamps="mri_dataset/timetable.tsv",
      lutfile="mri_processed_data/freesurfer_lut.json"
    output:
      "mri_processed_data/{subject}/statistics/{subject}_{session}_mixed_statstable.csv"
    params:
      sequence="mixed",
      timestamp_sequence="mixed"


use rule mri_region_stats as concentration_tissue_stats with:
    input:
      data="mri_processed_data/{subject}/concentrations/{subject}_{session}_concentration.nii.gz",
      segmentation="mri_processed_data/{subject}/segmentations/{subject}_seg-aparc+aseg_refined.nii.gz",
      timestamps="mri_dataset/timetable.tsv",
      lutfile="mri_processed_data/freesurfer_lut.json"
    output:
      "mri_processed_data/{subject}/statistics/{subject}_{session}_concentration_statstable.csv"
    params:
      sequence="concentration",
      timestamp_sequence="looklocker"


use rule mri_region_stats as concentration_csf_stats with:
    input:
      data="mri_processed_data/{subject}/concentrations/{subject}_{session}_concentration.nii.gz",
      segmentation="mri_processed_data/{subject}/segmentations/{subject}_seg-csf-aparc+aseg.nii.gz",
      timestamps="mri_dataset/timetable.tsv",
      lutfile="mri_processed_data/freesurfer_lut.json"
    output:
      "mri_processed_data/{subject}/statistics/{subject}_{session}_csf-concentration_statstable.csv"
    params:
      sequence="csf-concentration",
      timestamp_sequence="mixed"


use rule mri_region_stats as T1w_tissue_signal_differences_stats with:
    input:
      data="mri_processed_data/{subject}/T1w_signal_difference/{subject}_{session}_T1w_signal-difference.nii.gz",
      segmentation="mri_processed_data/{subject}/segmentations/{subject}_seg-aparc+aseg_refined.nii.gz",
      timestamps="mri_dataset/timetable.tsv",
      lutfile="mri_processed_data/freesurfer_lut.json"
    output:
      "mri_processed_data/{subject}/statistics/{subject}_{session}_T1w-signal-difference_statstable.csv"
    params:
      sequence="T1w-signal-difference",
      timestamp_sequence="T1w"


use rule mri_region_stats as T1w_csf_signal_differences_stats with:
    input:
      data="mri_processed_data/{subject}/T1w_signal_difference/{subject}_{session}_T1w_signal-difference.nii.gz",
      segmentation="mri_processed_data/{subject}/segmentations/{subject}_seg-csf-aparc+aseg.nii.gz",
      timestamps="mri_dataset/timetable.tsv",
      lutfile="mri_processed_data/freesurfer_lut.json"
    output:
      "mri_processed_data/{subject}/statistics/{subject}_{session}_T1w-csf-signal-difference_statstable.csv"
    params:
      sequence="T1w-signal-difference",
      timestamp_sequence="T1w"
