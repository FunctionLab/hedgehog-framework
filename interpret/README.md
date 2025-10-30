# Hedgehog Model Interpretation

This directory contains scripts for interpreting the Hedgehog model using DeepLIFT/DeepSHAP attribution methods and TF-MoDISco motif discovery. These tools help identify which sequence features (motifs) the model uses to make predictions.

## Requirements

A separate conda environment is recommended for interpretability analysis. Create it using:

```bash
conda env create -f sei-modisco-environment.yml
conda activate sei-modisco
```

Additional dependencies (install via pip after creating the environment):
- `tangermeme` - For computing DeepLIFT/DeepSHAP attributions
- `modisco-lite` or `tfmodisco-lite` - For motif discovery
- `h5py` - For HDF5 file handling

```bash
pip install tangermeme modisco-lite
```

## Overview

The interpretation workflow consists of three main steps:

1. **Compute attributions** - Use DeepLIFT/DeepSHAP to compute importance scores for each base in the input sequences
2. **Convert format** - Convert attribution HDF5 files to NPZ format for TF-MoDISco
3. **Discover motifs** - Run TF-MoDISco to identify recurring sequence patterns (motifs)

## Example Workflow

The `example/` directory contains a minimal working example with 389 test sequences and 11 target indices. This example demonstrates the complete interpretation pipeline.

### Example Data
- **Sequences**: `example/test_sequences_packbits.py` - 389 sequences in packbits format (4096 bp)
- **Targets**: `example/hedgehog_track_inds.txt` - 11 methylation profile indices (116, 123, 131, 132, 140, 142, 150, 151, 157, 160, 163)

### Step 1: Compute Attributions

```bash
conda activate sei-modisco

python3 deeplift_tgm_baselines.py \
    --packbits example/test_sequences_packbits.py \
    --checkpoint ../model/hedgehog.pth \
    --n-targets 296 \
    --model-seq-len 2048 \
    --seq-len 4096 \
    --targets-file example/hedgehog_track_inds.txt \
    --targets-per-job 11 \
    --outdir example/output \
    --n-shuffles 16 \
    --examples-per-call 389 \
    --pair-batch-size 64 \
    --device cuda \
    --save-dtype float16 \
    --compression lzf \
    --save-ohe
```

This creates:
- `example/output/ohe.npz` - One-hot encoded sequences
- `example/output/t116.h5`, `example/output/t123.h5`, etc. - Attribution files for each target

### Step 2: Convert to NPZ Format

```bash
python3 convert_h5_to_npz.py \
    --in-dir example/output \
    --out-dir example/output_npz
```

This creates NPZ files like `example/output_npz/hypcontribs_t116.npz` for TF-MoDISco.

### Step 3: Run TF-MoDISco (for one target)

```bash
modisco motifs \
    -s example/output/ohe.npz \
    -a example/output_npz/hypcontribs_t116.npz \
    -o example/output/modisco_t116.h5 \
    -n 2000 \
    -w 400
```

### Step 4: Generate HTML Report

```bash
mkdir -p example/reports/t116
modisco report \
    -i example/output/modisco_t116.h5 \
    -o example/reports/t116 \
    -s example/reports/t116
```

View the report by opening `example/reports/t116/motifs.html` in a browser.

**Note**: This example requires GPU execution. On CPU, attribution computation will be very slow and may produce numerical instabilities.

## Full Workflow

### Step 1: Compute DeepLIFT/DeepSHAP Attributions

The `deeplift_tgm_baselines.py` script computes attribution scores using the tangermeme library. It processes sequences in batches and can run as a SLURM array job across multiple targets (methylation profiles).

**Key features**:
- Works directly with Hedgehog model architecture
- Supports multiple reference (baseline) strategies: dinucleotide shuffle, uniform background, zeros, or custom references
- Processes data in streaming fashion to handle large datasets
- Saves attributions as HDF5 files (one per target)
- Optionally saves one-hot encoded sequences

**Direct usage**:
```bash
python deeplift_tgm_baselines.py \
    --packbits ../model/h5_datasets/test.seqlen=4096.seed=121.N=600000.h5 \
    --checkpoint ../model/hedgehog.pth \
    --n-targets 296 \
    --targets-file targets_subset.txt \
    --targets-per-job 25 \
    --outdir ./attributions \
    --n-shuffles 16 \
    --ref-kind dinuc_full \
    --model-seq-len 2048 \
    --device cuda
```

**SLURM array job** (recommended for multiple targets):
```bash
# Edit environment variables in submit_tgm_dynamic.sh first
export PACKBITS=../model/h5_datasets/test.seqlen=4096.seed=121.N=600000.h5
export CKPT=../model/hedgehog.pth
export OUTDIR=./attributions
export TARGETS_FILE=targets_of_interest.txt

sh submit_tgm_dynamic.sh
```

**Key parameters**:
- `--packbits`: Path to packbits-compressed sequences (HDF5 or NPY format)
- `--checkpoint`: Path to trained model weights
- `--targets-file`: Text file with target indices (one per line) to compute attributions for
- `--targets-per-job`: Number of targets per array task (for parallelization)
- `--n-shuffles`: Number of shuffled references per sequence (default: 16)
- `--ref-kind`: Reference generation strategy:
  - `dinuc_full`: Dinucleotide shuffle of entire sequence (default)
  - `dinuc_window`: Dinucleotide shuffle of window region only
  - `uniform025`: Uniform background (0.25 per base)
  - `zeros`: Zero background
  - `from_file`: Load custom references from file
- `--save-dtype`: Output precision (float32 or float16 to save space)
- `--compression`: HDF5 compression (lzf, gzip, or none)

**Output**: Creates `t{N}.h5` files in the output directory, where N is the target index. Each file contains a `hyp_contribs` dataset of shape `(n_sequences, 4, seq_length)`.

### Step 2: Prepare One-Hot Encoded Sequences (Optional)

If you need to generate OHE sequences separately (not done in Step 1 with `--save-ohe`):

```bash
python ohe_from_packbits.py \
    --packbits ../model/h5_datasets/test.seqlen=4096.seed=121.N=600000.h5 \
    --seq-len 4096 \
    --model-seq-len 2048 \
    --out ./ohe.npz
```

This converts packbits-compressed sequences to one-hot encoded format required by TF-MoDISco.

### Step 3: Convert Attributions to NPZ Format

TF-MoDISco expects NPZ files. Convert the HDF5 attribution files:

```bash
python convert_h5_to_npz.py \
    --in-dir ./attributions \
    --out-dir ./attributions_npz
```

This creates `hypcontribs_t{N}.npz` files for each target.

### Step 4: Run TF-MoDISco

Run TF-MoDISco to discover sequence motifs from the attributions:

```bash
# Edit environment variables in submit_modisco_array.sh first
export OHE=./ohe.npz
export NPZ_DIR=./attributions_npz
export OUT_DIR=./modisco_results
export REPORT_DIR=./modisco_reports

sh submit_modisco_array.sh
```

**Key parameters** (set as environment variables):
- `MODISCO_W`: Sliding window width for motif discovery (default: 400)
- `MODISCO_N`: Number of seqlets to use per metacluster (default: 2000)
- `CONCURRENCY`: Number of parallel jobs (default: 16)

**Output**:
- `modisco_t{N}.h5` files with discovered motifs
- HTML reports in `REPORT_DIR/t{N}/` with motif visualizations and statistics

## Understanding the Output

### Attribution Scores
Attribution scores (hypothetical contributions) indicate the importance of each nucleotide for the model's prediction:
- Positive scores: Nucleotide increases predicted methylation
- Negative scores: Nucleotide decreases predicted methylation
- Magnitude indicates strength of effect

### TF-MoDISco Results
TF-MoDISco identifies:
- **Patterns**: Recurring sequence motifs discovered in the attributions
- **Metaclusters**: Groups of similar patterns (pos/neg patterns)
- **Seqlets**: Individual sequence snippets contributing to patterns

HTML reports provide:
- Pattern logos (position weight matrices)
- Per-position contribution scores
- Distribution of seqlets across sequences
- Motif comparison with known TF binding sites (if annotations provided)

## Common Use Cases

### Running the Example
The fastest way to get started is to use the provided example:
```bash
cd interpret
conda activate sei-modisco
# Follow the Example Workflow section above
```

### Analyzing Specific Methylation Profiles
Create a targets file with indices of interest (e.g., tissue-specific profiles):
```bash
echo "42" > my_targets.txt
echo "101" >> my_targets.txt
echo "256" >> my_targets.txt
```
Then run the pipeline with `--targets-file my_targets.txt`.

### Comparing References
Different reference strategies can reveal different aspects:
- `dinuc_full`: Best for general motif discovery (preserves dinucleotide composition)
- `uniform025`: Highlights any deviation from uniform background
- `zeros`: Shows raw contribution (not relative to background)

### Reducing Memory Usage
- Use `--save-dtype float16` to halve storage requirements
- Use `--compression gzip` for better compression (slower I/O)
- Adjust `--examples-per-call` to control memory during processing

## File Organization

```
interpret/
├── README.md                      # This file
├── deeplift_tgm_baselines.py     # Compute DeepLIFT/DeepSHAP attributions
├── ohe_from_packbits.py          # Convert packbits to one-hot encoding
├── convert_h5_to_npz.py          # Convert HDF5 attributions to NPZ
├── submit_tgm_dynamic.sh         # SLURM submission for attributions
├── submit_modisco_array.sh       # SLURM submission for TF-MoDISco
├── modisco_array.sh              # Individual TF-MoDISco job script
├── sei-modisco-environment.yml   # Conda environment specification
└── example/                       # Example data and workflow
    ├── test_sequences_packbits.py # 389 test sequences
    ├── hedgehog_track_inds.txt    # 11 target indices
    └── output/                    # Generated by running example
```

## Troubleshooting

**Import errors**: Ensure the `model/` and `train/` directories are accessible. The scripts automatically add these to the Python path.

**CUDA out of memory**: Reduce `--pair-batch-size` or `--examples-per-call` parameters.

**SLURM configuration**: Update SBATCH directives and email addresses in the `.sh` scripts for your cluster.

**Missing dependencies**: The environment file provides core dependencies. Install `tangermeme` and `modisco-lite` separately via pip.

## References

- DeepLIFT: [https://github.com/kundajelab/deeplift](https://github.com/kundajelab/deeplift)
- TF-MoDISco: [https://github.com/jmschrei/tfmodisco-lite](https://github.com/jmschrei/tfmodisco-lite)
- tangermeme: [https://github.com/jmschrei/tangermeme](https://github.com/jmschrei/tangermeme)
