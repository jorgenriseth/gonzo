rule extract_concentration_times_T1w:
   input:
       timetable="mri_dataset/timetable.csv"
   output:
       temp("mri_processed_data/{subject}/timestamps_T1w.txt")
   shell:
       "python scripts/extract_timestamps.py"
       " --timetable {input}"
       " --subject {wildcards.subject}"
       " --sequence_label T1w"
       " --output {output}"


rule extract_concentration_times_LL:
   input:
       timetable="mri_dataset/timetable.csv"
   output:
       temp("mri_processed_data/{subject}/timestamps_LL.txt")
   shell:
       "python scripts/extract_timestamps.py"
       " --timetable {input}"
       " --subject {wildcards.subject}"
       " --sequence_label looklocker"
       " --output {output}"
