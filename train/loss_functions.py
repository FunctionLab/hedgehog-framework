"""
The criterion the model aims to minimize.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchsort


def mse(pred, target):
    mask = torch.isnan(target)
    return F.mse_loss(pred[~mask], target[~mask])


def spearman_ts_default(pred, target, **kw):
    pred = torchsort.soft_rank(pred, **kw)
    target = torchsort.soft_rank(target, **kw)
    pred = pred - pred.mean()
    pred = pred / pred.norm()
    target = target - target.mean()
    target = target / target.norm()
    rho = (pred * target).sum()
    return -1 * rho


def spearman_by_track_default(pred, target):
    n_targets = target.size()[1]
    corrs = torch.zeros(n_targets)
    for c in torch.arange(n_targets):
        pvec = pred[:, c]
        tvec = target[:, c]
        pvec = pvec[~torch.isnan(tvec)]
        tvec = tvec[~torch.isnan(tvec)]
        corrs[c] = spearman_ts_default(pvec.reshape((1, len(pvec))),
                                       tvec.reshape((1, len(pvec))),)
    return corrs.nanmean()

