from collections import OrderedDict
from shutil import copyfile
from shutil import copytree
import os

import numpy as np
import torch

from selene_sdk.utils import NonStrandSpecific
from selene_sdk.utils.config_utils import module_from_dir
from selene_sdk.utils.config_utils import module_from_file


def load_model_arch(model_configs, lr=None, output_dir=None):
    """
    Load model architecture from config file specifications.
    Wrap with NonStrandSpecific.

    If `lr` and `output_dir` are not None, assume model is
    in training mode and save the model file to the
    output directory. Return optimizer as well.
    """
    import_model_from = model_configs["path"]
    model_class_name = model_configs["class"]

    module = None
    if os.path.isdir(import_model_from):
        import_model_from = import_model_from.rstrip(os.sep)
        module = module_from_dir(import_model_from)
        if output_dir:
            copytree(
                import_model_from,
                os.path.join(output_dir, os.path.basename(import_model_from)))
    else:
        module = module_from_file(import_model_from)
        if output_dir:
            copyfile(
                import_model_from,
                os.path.join(output_dir, os.path.basename(import_model_from)))
    model_class = getattr(module, model_class_name)
    model = model_class(**model_configs["class_args"])
    model = NonStrandSpecific(
        model, mode='mean')
    if lr:
        optim_class, optim_kwargs = module.get_optimizer(lr)
        return model, optim_class, optim_kwargs
    return model


def init_pretrain_weights(model, checkpoint, freeze_upto=None):
    """Initialize the model weights for a pretrained model.
    The classifier part of the architecture is randomly initialized.
    """
    state_dict = checkpoint
    if 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']

    model_keys = list(model.state_dict().keys())
    state_dict_keys = list(state_dict.keys())

    new_state_dict = OrderedDict()
    for (k1, k2) in zip(model_keys, state_dict_keys):
        if 'classifier' in k1:
            print('Skip key:', k1, k2)
            continue
        value = state_dict[k2]
        try:
            new_state_dict[k1] = value
        except Exception as e:
            raise ValueError("Failed to load weight {0} into model architecture module {1}.".format(
                k1, k2))
    model.load_state_dict(new_state_dict, strict=False)

    # Requires manual inspection / counting of model layers.
    # 12 = everything except last, 1 = freeze only 1st layer conv
    if freeze_upto is not None:
        print("Freezing weights up to {0}".format(freeze_upto))
        count = 0
        for child in model.children():
            for c in child.children():
                if count == freeze_upto:
                    break
                for param in c.parameters():
                    param.requires_grad = False
                print('Setting requires_grad=False', c, count)
                count += 1
    return model


def init_weights(model, checkpoint):
    """
    Load model weights
    """
    state_dict = checkpoint
    if 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']

    model_keys = list(model.state_dict().keys())
    state_dict_keys = list(state_dict.keys())

    new_state_dict = OrderedDict()
    for (k1, k2) in zip(model_keys, state_dict_keys):
        value = state_dict[k2]
        try:
            new_state_dict[k1] = value
        except Exception as e:
            raise ValueError(
                "Failed to load weight {0} "
                "into model architecture module {1}.".format(k1, k2))
    model.load_state_dict(new_state_dict, strict=False)
    return model


def unpackbits_sequence(sequence, s_len):
    sequence = np.unpackbits(sequence.astype(np.uint8), axis=-2)
    nulls = np.sum(sequence, axis=-1) == sequence.shape[-1]
    sequence = sequence.astype(float)
    sequence[nulls, :] = 1.0 / sequence.shape[-1]
    if sequence.ndim == 3:
        sequence = sequence[:, :s_len, :]
    else:
        sequence = sequence[:s_len, :]
    return sequence

