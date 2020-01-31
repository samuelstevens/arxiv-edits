# Profiling performance with cProfile and snakeviz

```bash
# this creates a binary profile file named evaluate.prof
python -m cProfile -o evaluate.prof arxivedits/evaluate.py

# this breaks it down and makes it easier to understand
snakeviz evaluate.prof
```