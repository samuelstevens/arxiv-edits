"""
This calculates similarity lookups, feature vectors, and models for evaluating whether a sentence is part of a large chunk.

To run this analysis from scratch, delete the -vector.pckl and -lookup.pckl files in alignments/similarity.

Then run:
1. chunks/lookups.py
2. chunks/data.py
3. chunks/model.py 
4. chunks/evaluate.py on the best hyperparameters
"""

from arxivedits.chunks import evaluate, features, lookup, data
