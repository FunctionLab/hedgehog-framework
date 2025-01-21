# Example for variant effect prediction

This example details a case where you have a set of variants for which you are
interested in characterizing the impact of the variant on neighboring CpG loci.
All possible neighboring CpG loci are considered. If you have a case where you
already know what CpG loci you are interested in analyzing for each variant (e.g.
mQTLs associate variants to particular CpG locus), you may instead need to adapt 
`cpg_variants_to_fasta.py` to your input and just generate sequence reference
and alternative allele FASTA files on which to run `../fasta.sh`. 

Also note that Hedgehog excludes `chrX` and `chrY` from training to remove
sex chromosome-specific methylation effects, so we recommend removing
`chrX` and `chrY` variants from your variant set of interest as well.

## Steps

Processing steps, starting from `test.vcf` to get to the FASTA files used in `../predict`.

```
# for ease of processing, turn the VCF into a BED file
awk 'BEGIN{OFS="\t"}{print $1, $2, $2+1, $3, $4, $5}' test.vcf > test.bed

# make sure your BED file is sorted e.g. `sort -k1V -k2n <input-file> > <output-file>`
# before running `bedtools intersect`

# intersect the variant coordinates with +/- 1kb sequence context around
# CpG loci in the human genome. often there will be multiple CpGs within 1kb
# of each variant. we have provided hg19 and hg38 files depending on which
# genome version your variant coordinates are from, see `../data/berry.hg38.pm1kb.bed`.
# in this case, `test.vcf` is in hg19. 
bedtools intersect -a test.bed \
                   -b ../data/berry.liftover_hg19.pm1kb.bed \
                   -wa -wb > test.intersect_cpg_seq_context.bed

# create full 2kb sequences centered on the CpGs, with the off-center
# variant ref/alt substitutions. this will be used as input to the Hedgehog
# model.
python cpg_variants_to_fasta.py --input test.intersect_cpg_seq_context.bed \
                                --output test \
                                --genome hg19

```
Finally, run `../fasta.sh` with the resulting ref and alt FASTA files per the `predict` directory README.
```
# ran from the `../predict` directory as the working directory
sh fasta.sh ./example/test.refs.pm1kb.seqlen\=2048.fasta ./example/hedgehog_output
sh fasta.sh ./example/test.alts.pm1kb.seqlen\=2048.fasta ./example/hedgehog_output/
```

## Output

The directory `./hedgehog_output` contains the outputs from running the above command.
The reference allele Hedgehog predictions are in `test.refs.pm1kb.seqlen=2048_predictions.h5`
and the alternative allele Hedgehog predictions are in `test.alts.pm1kb.seqlen=2048_predictions.h5`.
These HDF5 files can be loaded using the `h5py` Python package, e.g.
```
import h5py
refs = h5py.File('./test.refs.pm1kb.seqlen=2048_predictions.h5', 'r')['data'][()]
alts = h5py.File('./test.alts.pm1kb.seqlen=2048_predictions.h5', 'r')['data'][()]
```

The columns of `refs` and `alts` are the 296 methylation profiles predicted by
Hedgehog, the labels for which are available in `../../model/hedgehog_targets_cleaned.tsv`.

The row label `.txt` files `test.refs.pm1kb.seqlen=2048_row_labels.txt` and `test.alts.pm1kb.seqlen=2048_row_labels.txt`
correspond to the rows in the `refs` and `alts` matrices. They index the FASTA
sequence IDs generated in `cpg_variants_to_fasta.py` and the ref and alt 
`row_labels.txt` files will match each other. Loading one of the row labels
files will be sufficient:
```
import pandas as pd
rowlabels = pd.read_csv('test.refs.pm1kb.seqlen=2048_row_labels.txt', sep='\t')
```
A snippet of the file:
```
index	name
0	chr1_3206171_chr1_3207180_rs2250291_T_C_ref
1	chr1_3206191_chr1_3207180_rs2250291_T_C_ref
2	chr1_3206199_chr1_3207180_rs2250291_T_C_ref
```
can be separated back out into the respective CpG locus and variant information
as follows:
```
dist = []
variants = []
locis = []
loci_positions = []
vp_id = []
for row in rowlabels['name']:
    lc, lp, vc, vp, vid, vr, va, _ = row.split('_')
    vp_id.append(vid)
    d = int(lp) - int(vp)
    dist.append(d)
    variants.append('{0}_{1}_{2}_{3}'.format(vc, vp, vr, va))
    locis.append('{0}_{1}'.format(lc, lp))
    loci_positions.append(int(lp))
rowlabels['dist'] = np.abs(dist)
rowlabels['variant'] = variants
rowlabels['loci'] = locis
rowlabels['loci_pos'] = loci_positions
rowlabels['id'] = vp_id
```

Now you may analyze the predicted impact of these variants on CpG loci as
desired. In our manuscript, we largely focus on variant effect prediction
in the context of the difference between `alts` and `refs`.
Furthermore, for all CpG within 1kb of a variant, we only keep the 
maximally impacted CpG for analysis 
```
diffs = alts - refs
diffvec = np.max(np.abs(diffs), axis=1)
```
based on the maximum absolute difference score for each variant-CpG pair
across all 296 methylation profiles. 

To add additional context to your analysis, the methylation sequence class
assignment of the CpG loci are available at `../data/berry.liftover_hg19.intersect_meseq_clusters.bed`
Simply filter the BED file to the CpG loci that are impacted by your variant 
set and use the methylation sequence class assignment to get a high-level 
characterization of these loci based on methylation regulation patterns.
Methylation sequence class assignment labels are available in Supp Table 2
`../data/methylation_seq_classes_ST2.tsv`.

