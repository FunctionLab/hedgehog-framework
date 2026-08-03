# Wreath Interpretability Example

This directory contains example data for testing the Wreath model interpretation pipeline.

## Example Data

### Input Files

**`test_sequences_packbits.py`**
- 389 DNA sequences in packbits format
- Each sequence is 4096 bp (packed to 512 × 4 uint8 array)
- Unpacks to 4096 bp, center-cropped to 2048 bp for model input
- Format: numpy array of shape (389, 512, 4)

**`Wreath_track_inds.txt`**
- 11 methylation profile target indices
- Indices: 116, 123, 131, 132, 140, 142, 150, 151, 157, 160, 163
- Each line contains one target index (0-295 for Wreath's 296 profiles)

## Running the Example

See the main [interpret/README.md](../README.md#example-workflow) for the complete step-by-step workflow.

Quick start:
```bash
cd interpret
conda activate sei-modisco

# Step 1: Compute attributions
python3 deeplift_tgm_baselines.py \
    --packbits example/test_sequences_packbits.py \
    --checkpoint ../model/wreath.pth \
    --n-targets 296 \
    --model-seq-len 2048 \
    --seq-len 4096 \
    --targets-file example/wreath_track_inds.txt \
    --targets-per-job 11 \
    --outdir example/output \
    --n-shuffles 16 \
    --device cuda \
    --save-ohe

# Step 2: Convert to NPZ
python3 convert_h5_to_npz.py \
    --in-dir example/output \
    --out-dir example/output_npz

# Step 3: Run TF-MoDISco on target 116
modisco motifs \
    -s example/output/ohe.npz \
    -a example/output_npz/hypcontribs_t116.npz \
    -o example/output/modisco_t116.h5 \
    -n 2000 -w 400

# Step 4: Generate HTML report
mkdir -p example/reports/t116
modisco report \
    -i example/output/modisco_t116.h5 \
    -o example/reports/t116 \
    -s example/reports/t116
```

## Expected Output Structure

After running the example, you should have:

```
example/
├── test_sequences_packbits.py          # Input data
├── wreath_track_inds.txt             # Target indices
├── output/                              # Step 1 output
│   ├── ohe.npz                         # One-hot encoded sequences (389, 4, 2048)
│   ├── t116.h5                         # Attributions for target 116
│   ├── t123.h5                         # Attributions for target 123
│   └── ... (11 total attribution files)
├── output_npz/                          # Step 2 output
│   ├── hypcontribs_t116.npz            # NPZ format for TF-MoDISco
│   ├── hypcontribs_t123.npz
│   └── ... (11 total NPZ files)
└── reports/                             # Step 4 output
    ├── t116/
    │   └── motifs.html                 # View this in browser
    ├── t123/
    └── ... (one directory per target)
```

## Notes

- **GPU Required**: This example requires GPU execution. CPU will be extremely slow and may produce numerical instabilities.
- **Runtime**: On GPU, expect ~5-10 minutes for all 11 targets. TF-MoDISco adds ~2-5 minutes per target.
- **Storage**: ~50-100 MB total output for this small example.
- **Scaling**: For full 296 targets on larger datasets, multiply storage and time requirements accordingly.

## Target Information

The 11 example targets correspond to specific methylation profiles from the Berry dataset. See `../model/wreath_targets_cleaned.tsv` for the mapping of target indices to tissue/cell type methylation profiles.
