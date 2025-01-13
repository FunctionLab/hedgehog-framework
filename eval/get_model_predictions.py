from argparse import ArgumentParser
from collections import defaultdict
from copy import deepcopy
import glob
import os
import random
import string
from time import strftime

import h5py
import numpy as np
import pandas as pd
import torch
import yaml

from utils import init_weights
from utils import load_model_arch
from utils import unpackbits_sequence


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        "--config", help="A required .yaml file with training params")
    parser.add_argument(
        "--dataset", help="A required .h5 file of sequences to predict")
    parser.add_argument(
        "--outdir", help="An optional output directory path", default=None)
    parser.add_argument(
        "--data-seqlen",
        help=".h5 dataset sequence length, default is 4096bp",
        default=4096, type=int)
    args = parser.parse_args()

    setup_args = None
    with open(args.config) as f:
        setup_args = yaml.safe_load(f)

    outdir = args.outdir
    if args.outdir is None:
        outdir, _ = os.path.split(setup_args['checkpoint'])
    else:
        os.makedirs(outdir, exist_ok=True)
    print("Outputting predictions to {0}".format(outdir))

    setup_args['dataset'] = args.dataset
    config_out = os.path.join(outdir, os.path.basename(args.config))
    print(config_out)
    with open(config_out, 'w') as outfile:
        yaml.dump(setup_args, outfile)

    N_targets = 296
    targets = np.arange(N_targets)
    if 'seq_len' not in setup_args:
        setup_args['seq_len'] = 2048

    model_configs = setup_args['model']
    if 'class_args' not in model_configs:
        model_configs['class_args'] = {}
    # required input arguments to the model architecture class
    model_configs['class_args']['sequence_length'] = setup_args['seq_len']
    model_configs['class_args']['n_genomic_features'] = N_targets
    model = load_model_arch(model_configs)

    checkpoint = torch.load(setup_args['checkpoint'],
                            map_location=lambda storage, location: storage)
    model = init_weights(model, checkpoint)
    model.cuda()
    model.eval()

    outfile = os.path.join(outdir, '{0}.predictions.h5'.format(os.path.basename(args.dataset)))
    print(outfile)

    data_seq_len = args.data_seqlen
    seq_s = data_seq_len // 2 - setup_args['seq_len'] // 2
    seq_e = data_seq_len // 2 + int(np.ceil(setup_args['seq_len'] / 2.))

    with h5py.File(args.dataset, 'r') as read_fh, h5py.File(outfile, 'a') as write_fh:
        sequences = read_fh['sequences']

        if 'predictions' in write_fh:
            del write_fh['predictions']

        preds = write_fh.create_dataset(
            'predictions', (len(sequences), N_targets), dtype='float')

        for ix in range(0, len(sequences), setup_args['batch_size']):
            s = ix
            e = min(ix+setup_args['batch_size'], len(sequences))
            batch_seq = unpackbits_sequence(sequences[s:e], data_seq_len)
            batch_seq = batch_seq[:, seq_s:seq_e, :]
            batch_seq = torch.Tensor(batch_seq).cuda()
            with torch.no_grad():
                preds[s:e] = model(batch_seq.transpose(1, 2)).data.cpu().numpy()

