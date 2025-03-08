<p align="center">
  <img height="150" src="img/Hedgehog.png">
</p>

#

Welcome to the Hedgehog model repository! Hedgehog is a sequence-based deep learning model for prediction of methylation levels at CpG locus in the human genome across 296 methylation profiles available in the Berry dataset. This repository can be used to train, evaluate, and apply the Hedgehog model to make predictions on CpG locus disruptions to methylation levels given neighboring variants.  

## Requirements

Hedgehog requires Python 3.9+ and Python packages PyTorch (>=1.0), Selene (>=0.6.0), and torchsort (>=0.1.9, needed for training). You can follow PyTorch installation steps [here](https://pytorch.org/get-started/locally/). We recommend installing Selene via `pip install selene-sdk` (more documentation on Selene [here](https://github.com/FunctionLab/selene)).

For torchsort installation, we run the following steps after all other dependencies are installed. Note that torchsort needs to be installed on a GPU node (e.g. whatever GPU node you plan to run training on) with GCC and CUDA.
```
pip install --force-reinstall --no-cache-dir --no-deps torchsort
```

We also provide `env.yaml` and `env.txt` which are exported from the conda environment we used, but recommend installation in the order we specified above rather than using these files directly since installation difficulties can be common across different OS. We provide these primarily as a reference for any dependencies that we may have missed (please file a GitHub issue if you catch any so we can improve our documentation!).

(Hedgehog was originally trained with Python 3.8 with a local installation of Selene but we have since updated our requirements in the Selene package to require Python 3.9+.) 

## Setup

First review `./download_data.sh`, which has a number of commented out lines, and re-comment in any necessary data files for the steps you are interested in running. You may have been provided with a username and password for download via our website server. 

## Overview

Please refer to the individual README.md files in each directory for more
detailed usage steps. Briefly, you can use each directory for the following:
- `train`: Trains the Hedgehog model architecture
- `eval`: Evaluates the Hedgehog model. Code can also be used to get Hedgehog
          predictions given any `np.packbits` compressed sequences matrix
          stored in an HDF5 file.
- `predict`: Variant effect prediction, where the change in methylation levels
             at a center CpG locus is predicted given a variant. Code gets
             Hedgehog predictions given FASTA reference and alternative allele
             sequences as input.

## Help

Post in the Github issues or e-mail Kathy Chen (chen.kathleenm@gmail.com) with any questions about the repository, requests for more data, etc.

