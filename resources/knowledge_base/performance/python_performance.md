# Python Performance Optimization

## Measure First
Do not optimize on guesswork. Profile with `cProfile`, `timeit`, or a sampling profiler to find the real hotspots. Most time is usually spent in a small fraction of the code; optimize that and leave the rest readable.

## Algorithmic Complexity
The biggest wins come from better algorithms and data structures, not micro-tuning. Use `set`/`dict` for membership tests (O(1)) instead of scanning a list (O(n)). Avoid nested loops that create O(n²) behavior over large inputs. Watch for accidental quadratic work such as repeated string concatenation in a loop — build a list and `"".join()` instead.

## Idiomatic Speed
Prefer comprehensions and generator expressions to manual loops for building collections. Use generators to stream large datasets instead of materializing them in memory. Cache expensive pure-function results with `functools.lru_cache`. Hoist invariant computations out of loops. Use local variables in hot loops (attribute and global lookups are slower).

## I/O and Concurrency
I/O-bound work benefits from `asyncio` or threads; CPU-bound work needs `multiprocessing` or native extensions because of the GIL. Batch network and database calls to avoid the N+1 query problem. Reuse connections and sessions rather than opening one per call.

## Memory
Use `__slots__` on classes with many instances to cut per-instance overhead. Prefer streaming and chunking for large files. Release references you no longer need so the garbage collector can reclaim memory.
