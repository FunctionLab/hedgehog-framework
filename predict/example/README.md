Processing steps, starting from `test.vcf` to get to the FASTA files used in `../predict`. 

```
# for ease of processing, turn the VCF into a BED file
awk 'BEGIN{OFS="\t"}{print $1, $2, $2+1, $3, $4, $5}' test.vcf > test.bed

# intersect the variant coordinates with +/- 1kb sequence context around
# CpG loci in the human genome. often there will be multiple CpGs within 1kb
# of each variant.
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
