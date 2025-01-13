# Hedgehog evaluation

The script `get_model_predictions.py` can be used for any HDF5 file of one-hot
encoded sequences that has been compressed via `np.packbits(seq > 0, axis=0)`,
see `./model/create_h5_datasets.ipynb` for reference on how to create these
HDF5 files. If you generate your own dataset and `packbits` sequences of 2048 
in length, you will need to use the optional argument `--data-seqlen=2048` for 
correct decompression (unpacking) of the sequence one-hot encoding.

For evaluating Hedgehog on the test holdout dataset, we can run 
```
sh eval.sh ../model/h5_datasets/test.seqlen\=4096.seed\=121.N\=600000.h5 \
           ../model/h5_predictions
```

