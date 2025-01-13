# Hedgehog CpG locus variant effect predictions 

Because Hedgehog only predicts methylation level changes at CpG
loci, variant effect prediction entails computing the difference between
methylation level predictions for a centered CpG locus given an off-center
mutation. Given Hedgehog's input sequence length of 2048bp, variants can be
up to 1024bp away from the center CpG locus. 

As a result, the steps to run variant effect prediction are as follows:
- Step 0: If the CpG locus associated with the variant is known (e.g. mQTL
case), skip this step. Otherwise, a variant could impact any CpG locus within
1024bp. In this case, we recommend intersecting your variant file with the
appropriate BED file of CpG locus +/- 1kb regions in `./data` (we provide hg19 
and hg38 files). Follow the steps in `example` to go from a `test.vcf` file to
a BED file as described.

- Step 1: For every variant-CpG locus pair, create reference and alternative
allele 1024bp sequences (centered at the CpG locus) and output each of these
into reference and alternative allele sequence FASTA files. See `example` for
an example script to do so. 
Additionally, we will provide notebooks associated with the manuscript results 
(coming soon) for `mqtl_effect_sizes` and `pathogenic_mutations` as other
example workflows. 

- Step 2: Run 
```
sh fasta.sh <path-to-reference-fasta>/refs.fasta <output-directory>
sh fasta.sh <path-to-alternative-fasta>/alts.fasta <output-directory>
```

- Step 3: To add additional context to your analysis, the methylation sequence class
assignment of the CpG loci are available at `./data/berry.liftover_hg19.intersect_meseq_clusters.bed`
and `./data/berry.hg38.intersect_meseq_clusters.bed` depending on which genome
version you are working with. Download instructions for these BED files is
in `../download_data.sh`. 
