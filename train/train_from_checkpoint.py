from argparse import ArgumentParser
import os
import random
import string
from time import strftime

import numpy as np
from scipy.stats import pearsonr
from scipy.stats import spearmanr
import torch
import yaml

from selene_sdk.train_model import TrainModel
from selene_sdk.samplers.dataloader import _H5Dataset
from selene_sdk.samplers.dataloader import H5DataLoader
from selene_sdk.samplers import MultiSampler
from selene_sdk.utils.config_utils import module_from_dir
from selene_sdk.utils.config_utils import module_from_file

from loss_functions import mse
from loss_functions import spearman_by_track_default
from utils import load_model_arch


LOSS_FN = {
    'mse': mse,
    'spearman_by_track_default': spearman_by_track_default,
}


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "--config", help="A required .yaml file with training params")
    parser.add_argument(
        "--lr", help="Specify a learning rate. Default lr=0.01",
        type=float, default=0.01)
    args = parser.parse_args()

    setup_args = None
    with open(args.config) as f:
        setup_args = yaml.safe_load(f)

    res = ''.join(random.choices(string.ascii_uppercase +
                                 string.digits, k=8))
    output_dir = os.path.join(
        setup_args['output_dir'],
        '{0}-{1}'.format(strftime("%Y-%m-%d-%H-%M-%S"), res))
    os.makedirs(output_dir, exist_ok=True)
    print(output_dir)

    setup_args['output_dir'] = output_dir
    setup_args['lr'] = args.lr

    config_out = '{0}_lr={1}.yaml'.format(
        os.path.basename(args.config).rsplit('.', 1)[0], args.lr)
    print(config_out)
    with open(os.path.join(output_dir, config_out), 'w') as outfile:
        yaml.dump(setup_args, outfile)

    if "random_seed" in setup_args:
        seed = setup_args["random_seed"]
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        print("Setting random seed = {0}".format(seed))
    else:
        print("Warning: no random seed specified in config file. "
              "Using a random seed ensures results are reproducible.")

    N_targets = 296
    targets = np.arange(N_targets)

    if 'seq_len' not in setup_args:
        setup_args['seq_len'] = 4096
    print('seq_len =', setup_args['seq_len'])
    if 'n_cpus' not in setup_args:
        setup_args['n_cpus'] = 1

    valid_file = "../model/h5_datasets/validate.seqlen=4096.seed=121.N=32000.h5"
    train_dataset = _H5Dataset(
        setup_args['train_file'],
        unpackbits_seq=True,
        use_seq_len=setup_args['seq_len'])
    valid_dataset = _H5Dataset(
        valid_file,
        unpackbits_seq=True,
        use_seq_len=setup_args['seq_len'])
    print(setup_args['train_file'], valid_file)

    train_dl = H5DataLoader(
        train_dataset,
        batch_size=setup_args['batch_size'],
        num_workers=setup_args['n_cpus'] - 1,
        seed=seed,
        shuffle=True)

    valid_dl = H5DataLoader(
        valid_dataset,
        batch_size=setup_args['batch_size'],
        num_workers=1,
        seed=seed,
        shuffle=False)

    multi_sampler = MultiSampler(train_dl, valid_dl, targets)

    model_configs = setup_args['model']
    if 'class_args' not in model_configs:
        model_configs['class_args'] = {}
    # required input arguments to the model architecture class
    model_configs['class_args']['sequence_length'] = setup_args['seq_len']
    model_configs['class_args']['n_genomic_features'] = N_targets
    model, optim, optim_args = load_model_arch(
        model_configs, lr=args.lr, output_dir=output_dir)

    trainer = TrainModel(
        model,
        multi_sampler,
        LOSS_FN[setup_args['loss']],
        optim, optim_args,
        setup_args['batch_size'],
        1000000,  # max steps
        setup_args['report_after_n_steps'],
        output_dir,
        report_gt_feature_n_positives=5,
        n_validation_samples=32000,
        n_test_samples=600000,
        cpu_n_threads=setup_args['n_cpus'],
        use_cuda=True,
        data_parallel=setup_args['data_parallel'] if 'data_parallel' in setup_args else False,
        use_scheduler=True,
        deterministic=True,
        checkpoint_resume=setup_args['checkpoint'] if 'checkpoint' in setup_args else None,
        metrics=dict(spearmanr=spearmanr, pearsonr=pearsonr)
    )

    trainer.train_and_validate()
