# TRMP

Evolutionary/NEH-based local search heuristic for sensor group scheduling (minimizing total sensor reorientation cost).

## Build

```
gcc -O2 -o es_pre_sfFIN.exe es_pre_sfFIN.c -lm
```

## Run

```
./es_pre_sfFIN.exe <seed> <instance_file> <output_file>
```

- `<seed>` - integer RNG seed
- `<instance_file>` - one of the files in `instances/`
- `<output_file>` - results are appended here

Example:

```
./es_pre_sfFIN.exe 1 instances/covers_dirn050m030r150s03i00.dat results.txt
```

The program reads `init_state.dat` (initial sensor angles) from the current working directory, so run it from the project root.

## Files

- `es_pre_sfFIN.c` - main algorithm source
- `init_state.dat` - initial sensor angle state
- `instances/` - problem instances
- `results_ESapproach.ods` - reference results
