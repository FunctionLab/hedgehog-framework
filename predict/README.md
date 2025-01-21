# Hedgehog CpG locus variant effect predictions 

Please run the relevant commands in `../download_data.sh` (most have been 
commented out to avoid downloading unnecessary data) in order to get the 
data files necessary for variant effect prediction.

Because Hedgehog only predicts methylation level changes at CpG
loci, variant effect prediction entails computing the difference between
methylation level predictions for a centered CpG locus given an off-center
mutation. Given Hedgehog's input sequence length of 2048bp, variants can be
up to 1024bp away from the center CpG locus. We only provide functionality
for handling single-base mutations, not insertions or deletions.

Also note that Hedgehog excludes `chrX` and `chrY` from training to remove
sex chromosome-specific methylation effects, so we recommend removing
`chrX` and `chrY` variants from your variant set of interest as well.

As a result, the steps to run variant effect prediction are as follows:
- Step 0: **If the CpG locus associated with the variant is known (e.g. mQTLs
associate a variant to a CpG locus), skip this step.**
Otherwise, a variant could impact any CpG locus within 1024bp away. 
In this case, we recommend intersecting your variant file with the
appropriate BED file of CpG locus +/- 1kb regions in `./data` (we provide hg19 
and hg38 files). Follow the steps in `./example` to go from a `test.vcf` file to
a BED file as described.

- Step 1: For every variant-CpG locus pair, create reference and alternative
allele 1024bp sequences (centered at the CpG locus) and output each of these
into reference and alternative allele sequence FASTA files. See `./example` for
an example script to do so (`./example/cpg_variants_to_fasta.py`) 
Additionally, we will soon provide notebooks associated with the manuscript 
results for mQTL analysis and HGMD pathogenic mutation prediction which
can be adapted for your own analysis. 

- Step 2: Run 
```
sh fasta.sh <path-to-reference-fasta>/refs.fasta <output-directory>
sh fasta.sh <path-to-alternative-fasta>/alts.fasta <output-directory>
```

- Step 3: In our manuscript, we restrict our analysis to the CpG locus
that is maximally impacted by a given variant by taking the maximum
absolute difference score between the alternative allele predictions and
the reference allele predictions, across all 296 methylation profiles predicted
by Hedgehog.

- Step 4: To add additional context to your analysis, the methylation sequence class
assignment of the CpG loci are available at `./data/berry.liftover_hg19.intersect_meseq_clusters.bed`
and `./data/berry.hg38.intersect_meseq_clusters.bed` (depending on which genome
version your variant coordinates use). Simply filter the BED file to the CpG
loci that are impacted by your variant set and use the methylation sequence
class assignment to get a high-level characterization of these loci based on
methylation regulation patterns.

