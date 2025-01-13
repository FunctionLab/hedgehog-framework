import os
from collections import Counter
from collections import defaultdict

from argparse import ArgumentParser
import numpy as np
import pandas as pd

from selene_sdk.sequences import Genome
from utils import process_variants


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--input",
        required=True,
        help="Input BED file with variant and CpG information.")
    parser.add_argument(
        "--output",
        required=True,
        help="Output file prefix to save FASTA files.")
    parser.add_argument(
        "--genome",
        required=True,
        help="Specify 'hg19' or 'hg38'.")
    args = parser.parse_args()
    print(args.input, args.output)
    loci_df = pd.read_csv(args.input, sep='\t', header=None)

    # CpG locus -> list(variants) within 1kb of that locus
    loci_to_variants = defaultdict(list)
    vset = set()
    skip = 0
    for row in loci_df.itertuples():
        lc, lp = row._10.split('_')
        lp = int(lp)
        variant = '{0}_{1}_{2}_{3}_{4}'.format(row._1, row._2, row._4, row._5, row._6)
        # off by 1 extra filtering step
        if lp - row._2 == 1024:
            skip += 1
            continue
        loci_to_variants[(lc, lp)].append(variant)
        vset.add(variant)

    genome = Genome('../../resources/{0}_UCSC.fa'.format(args.genome))
    refs, alts, labels = process_variants(loci_to_variants.items(), 2048, genome)
    print(Counter(labels['sub_info']))

    labels['ref'] = refs
    labels['alt'] = alts
    with open('{0}.refs.pm1kb.seqlen=2048.fasta'.format(args.output),
              'w+') as fh:
        for row in labels.itertuples():
            fh.write(">{0}_{1}_ref\n".format(row.loci, row.variant))
            assert len(row.ref) == 2048
            fh.write('{0}\n'.format(row.ref))
    with open('{0}.alts.pm1kb.seqlen=2048.fasta'.format(args.output),
              'w+') as fh:
        for row in labels.itertuples():
            fh.write(">{0}_{1}_alt\n".format(row.loci, row.variant))
            assert len(row.alt) == 2048
            fh.write('{0}\n'.format(row.alt))


