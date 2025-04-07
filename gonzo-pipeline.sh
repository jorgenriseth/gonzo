#!/bin/bash
cat build-record/pipeline-leaf-files.txt | xargs snakemake $@
