from collections import OrderedDict

import numpy as np
import pandas as pd
from selene_sdk.sequences import Genome


def process_variants(loci_to_variants, seq_len, genome, compress=False):
    """
    Assumes `seq_len` is an even number
    """
    output_refs = []
    output_alts = []
    output_labels = []

    variants_total = 0
    mismatch_total = 0
    for (chrom, pos), variants in loci_to_variants:
        query = genome.get_sequence_from_coords(
            chrom, pos - seq_len // 2, pos + seq_len // 2)
        contains_unk = False
        if len(query) != seq_len:
            print("Skipping: ({0} {1}), seq len = {2}".format(
                chrom, pos, len(query)))
            continue
        ref = str.upper(query[(seq_len // 2) - 1])
        if ref.upper() != 'C':
            mismatch_total += 1
            if mismatch_total % 100 == 0:
                print("Mismatches: {0}, {1}".format(mismatch_total, ref))
            continue
        if 'N' in query.upper():
            contains_unk = True
        for v in set(variants):
            variants_total += 1
            info = v.split('_')
            if len(info) == 5:
                c, p, vid, r, a = v.split('_')
            else:
                c, p, r, a = v.split('_')
            p = int(p)
            ref_sequence, alt_sequence, vinfo = substitution(
                query, pos, c, p, r, a)
            # this could be done faster by using the encoding directly
            # and making the encoded substitutions instead of doing it after
            # the fact
            if compress:
                ref_enc = Genome.sequence_to_encoding(ref_sequence)
                alt_enc = Genome.sequence_to_encoding(alt_sequence)
                ref_enc = np.packbits(ref_enc.T > 0, axis=1)
                alt_enc = np.packbits(alt_enc.T > 0, axis=1)
                output_refs.append(ref_enc.T)
                output_alts.append(alt_enc.T)
            else:
                output_refs.append(ref_sequence)
                output_alts.append(alt_sequence)
            output_labels.append({
                'loci': '{0}_{1}'.format(chrom, pos),
                'contains_unk': contains_unk,
                'variant': v,
                'sub_info': vinfo
            })
    print("Skipped prop. {0}".format(mismatch_total / variants_total))
    return output_refs, output_alts, pd.DataFrame(output_labels)


def substitution(seq, spos, vchr, vpos, vref, valt):
    """
    This function assumes the center is len(seq) // 2.
    """
    slen = len(seq)
    sub_pos = vpos - (spos - slen // 2) - 1

    # what is the base at this position in the queried sequence
    ans = seq[sub_pos].upper()
    vref, valt = vref.upper(), valt.upper()  # just some data cleaning

    ref_sequence, alt_sequence = None, None
    info = 'nomatch'
    if ans == vref:  # NORMAL CASE, base matches ref
        ref_sequence = seq
        alt_seq = list(seq)
        alt_seq[sub_pos] = valt
        alt_sequence = ''.join(alt_seq)
        info = 'match'
    elif ans == valt:  # alt and ref swapped, swap accordingly in the resulting outputs
        # example: ans = 'A', ref = 'G', alt = 'A'
        alt_sequence = seq
        ref_seq = list(seq)
        ref_seq[sub_pos] = vref
        ref_sequence = ''.join(ref_seq)
        info = 'swap'
        assert alt_sequence[sub_pos].upper() == valt, ('alt', alt_sequence[sub_pos].upper(), valt, ans)
        assert ref_sequence[sub_pos].upper() == vref, ('ref', ref_sequence[sub_pos].upper(), vref, ans)
    elif ans == Genome.COMPLEMENTARY_BASE_DICT[vref]:  # complementary base
        # take the complementary bases since our model isn't strand specific
        # example: ans = 'A', ref = 'T', alt = 'C'
        # our original sequence contains the complement of ref, no need to change that.
        # complement the alt base before making the substitution
        ref_sequence = seq
        alt_seq = list(seq)
        alt_seq[sub_pos] = Genome.COMPLEMENTARY_BASE_DICT[valt]
        alt_sequence = ''.join(alt_seq)
        info = 'complement'
        assert ref_sequence[sub_pos].upper() == Genome.COMPLEMENTARY_BASE_DICT[vref], \
                ('ref', ref_sequence[sub_pos].upper(), vref, ans)
        assert alt_sequence[sub_pos].upper() == Genome.COMPLEMENTARY_BASE_DICT[valt], \
                ('alt', alt_sequence[sub_pos].upper(), valt, ans)
    elif ans == Genome.COMPLEMENTARY_BASE_DICT[valt]:  # alt and ref swapped, and complementary base
        # example: ans = 'A', ref = 'C', alt = 'T'
        # our original sequence contains the complement of alt
        # complement the ref base before making the substitution
        alt_sequence = seq  # reference sequence queried is actually the alt sequence
        ref_seq = list(seq)
        ref_seq[sub_pos] = Genome.COMPLEMENTARY_BASE_DICT[vref]
        ref_sequence = ''.join(ref_seq)
        info = 'complement_swap'
        assert ref_sequence[sub_pos].upper() == Genome.COMPLEMENTARY_BASE_DICT[vref], \
                ('ref', ref_sequence[sub_pos].upper(), vref, ans)
        assert alt_sequence[sub_pos].upper() == Genome.COMPLEMENTARY_BASE_DICT[valt], \
                ('alt', alt_sequence[sub_pos].upper(), valt, ans)
    else:
        return ref_sequence, alt_sequence, info  # None, None, 'nomatch'
    return ref_sequence, alt_sequence, info


def init_weights(model, checkpoint):
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
             raise ValueError("Failed to load weight {0} into model architecture module {1}.".format(
                 k1, k2))
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
