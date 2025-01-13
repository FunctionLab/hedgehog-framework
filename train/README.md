# Hedgehog training framework

To run Hedgehog deep learning sequence model training, you will need GPU computing capability (we run training on 4 a100 GPUs).

Please run the relevant commands in `../download_data.sh` (most have been commented out to avoid downloading unnecessary data) in order to get the data files necessary for training.

Hedgehog is trained on 2048bp sequences centered at CpG loci from the Berry dataset. Chromosome 10 was held out for validation, and chromosomes 8 and 9 were held out for testing. Chromosomes X and Y were excluded to remove sex-specific methyation effects. 

Accordingly, we created training, validation, and test datasets using the code in `../model/create_h5_datasets.ipynb`.

Hedgehog training starts with initialization of weights from a previously trained chromatin profiling model (Sei), so the first command we run is
```
sh train.sh ./train.yaml
```
(Note that `sh` can be replaced with `sbatch` after the example SLURM configurations in the file are modified for your system.)

Following this, you can resume training of the Hedgehog model using 
```
sh train_from_checkpoint.sh ./train_from_checkpoint.yaml
```
`./train_from_checkpoint.yaml` must be modified so that `checkpoint` contains the correct path to your previously trained model. 

Also note that both `.sh` scripts contain the optimal learning rate given Hedgehog's final training specifications (e.g. differential Spearman's loss function, SGD optimizer, the pre-generated training datasets). The final Hedgehog model was trained for a month and used `../model/h5_datasets/train.seqlen=4096.seed=121.N=12000000.h5` with seed 43 for the first 2 weeks of training and then another sampling of the Berry dataset
`../model/h5_datasets/train.seqlen=4096.seed=121.N=12000000.1.h5` with seed 44 for the next 2 weeks of training on 4 a100 GPUs.
