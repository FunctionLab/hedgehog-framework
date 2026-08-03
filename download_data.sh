#!/bin/sh

# Usage: `sh ./download_data.sh <USER> <PW>`
USER=$1
PW=$2

# FASTA files download into `resources` directory, 6.1G
wget https://zenodo.org/record/4906962/files/sei_framework_resources.tar.gz && \
    tar -xzvf sei_framework_resources.tar.gz && rm sei_framework_resources.tar.gz

# Wreath model weights, 597M
wget https://wreath.princeton.edu/data/wreath.pth && mv ./wreath.pth model/

# For the remaining .tar.gz files, you can download based on
# which analyses you want to run, keeping in mind the storage
# requirements for this data. The commands are commented out to avoid
# running them unnecessarily if you are not interested in a particular
# step.

###############################################################################
#
# Download if you want to run `train`
#
###############################################################################


# Needed for weight initialization with chromatin profiling DL model,
# 3.4G
# wget https://sei-files.s3.amazonaws.com/resources.tar.gz
#The sei.pth file can be found under `resources/`
#mv ./sei.pth model/

# HDF5 datasets used for training and evaluation, 100G
# wget https://wreath.princeton.edu/data/wreath_h5_datasets.tar.gz && \
#     tar -xzvf wreath_h5_datasets.tar.gz -C model/ && \
#     rm wreath_h5_datasets.tar.gz




###############################################################################
#
# Download if you want to run `eval`
#
###############################################################################

# Same as above, run the command for downloading `wreath_h5_datasets.tar.gz`
# if you want to run evaluation on the test holdout dataset.
# If you have space constraints you can delete the training and validation
# files from the decompressed directory when not running `train`.




###############################################################################
#
# Download if you want to run `predict`
#
###############################################################################

# BED files used to get the CpG loci coordinates and the methylation
# sequence class assignments, 6G
# wget https://wreath.princeton.edu/data/predict_data.tar.gz && \
#     tar -xzvf predict_data.tar.gz -C predict/ && rm predict_data.tar.gz

# Example output files, ~20M
# wget https://wreath.princeton.edu/data/predict_example.tar.gz && \
#     tar -xzvf predict_example.tar.gz -C predict/example --strip-components=1 && \
#     rm predict_example.tar.gz




###############################################################################
#
# Download if you want to run `create_h5_datasets.ipynb`, which samples
# human genomic sequences centered at CpG loci and retrieves their methylation
# profiles from the Berry dataset
#
###############################################################################


# Berry dataset, 65G
# wget https://wreath.princeton.edu/data/berry_for_ML.tar.gz && \
#     tar -xzvf berry_for_ML.tar.gz -C model/ && rm berry_for_ML.tar.gz


