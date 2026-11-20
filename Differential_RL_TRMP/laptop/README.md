# Laptop confirmation run: does a larger block-destruction size κ (12, 16) beat κ=4?

One script builds the C program, checks your machine, runs the experiment in parallel, **logs everything** and packs it
into a single file to upload.

## What you need
* A C compiler (`gcc` or `clang`) and `bash`.
  * **Linux**: `sudo apt install build-essential`.
  * **macOS**: `xcode-select --install` (gives `clang`).
  * **Windows**: use **WSL** (recommended): `wsl --install`, open Ubuntu, `sudo apt install build-essential`, and run
    everything inside WSL. Git-Bash + MinGW also works but its random-number generator differs, so the script then
    re-runs κ=4 itself (about 50 % more time) — that is handled automatically.
* The whole repository (the script needs `src/`, `instances/`, `init_state.dat` and `reference/`).
* Laptop **plugged in**, sleep disabled. All cores are used except one (change with `--jobs N`).

## Run it
```bash
cd Differential_RL_TRMP
bash laptop/run_confirm.sh --tier smoke     # 2-5 minutes: checks that everything works. Do this first.
bash laptop/run_confirm.sh --dry-run        # prints the plan and the time estimate for the default tier, runs nothing
bash laptop/run_confirm.sh                  # default tier "quick": 11 NEW instances, 10 runs, κ = 12 and 16
```
### Follow-up run: where does the gain end? (κ = 20, 24, 32)
```bash
cd Differential_RL_TRMP && git pull
bash laptop/run_confirm.sh --tier plateau --dry-run    # plan + time estimate (18 jobs, about 2.5-4 h on a 4-core laptop)
bash laptop/run_confirm.sh --tier plateau              # 6 n=400 instances x κ 20, 24, 32 x 10 runs
bash laptop/run_confirm.sh --tier plateau-lite         # 3 instances (one per aperture): about half the time (9 jobs)
```
These use the *same* six n=400 instances and seeds as the κ=12/16 run you already uploaded, so I can compare all five κ values
run by run — there is no need to re-run κ=12/16. Upload the `.tar.gz` it prints, exactly as before.

### Does the best κ scale with n? (n≈200)
```bash
bash laptop/run_confirm.sh --tier n200 --dry-run    # 25 jobs: 5 n≈200 instances x κ 8, 10, 20, 24, 32 x 10 runs (about 1-2 h)
```
Same five n≈200 instances and seeds as the κ=12/16 run, so all κ values pair run by run.

Other options: `--tier full` (all 26 instances with n≥198, 20 runs — many hours), `--kappas "12"`, `--runs 5`,
`--jobs 2`, `--rundir <folder>` (resume). Watch progress with `tail -f logs/<run folder>/progress.log`.

Stopped it (Ctrl+C, shutdown)? Re-run the command printed when you interrupted it (it ends with `--rundir <folder>`): finished
jobs are skipped.

## What it fairly compares
Every run of κ=12 / 16 stops after exactly as many candidate evaluations as the κ=4 run with the same index (so a larger κ
cannot win just by using more compute). Seeds are shared, so the comparison is paired. The pre-flight step (one κ=4 run,
~1 minute) checks that your machine reproduces my reference results exactly; if so, the bundled κ=4 reference is used.

## What to upload
When it finishes it prints `=====> UPLOAD THIS FILE: .../logs/<tier>_<time>_<host>.tar.gz` (a few hundred KB). Upload that file.
It contains `run_info.txt` (machine, compiler, settings), `progress.log` (timing of every job), `summary.txt` (a quick
table), and `results/*.csv|row|log` (every run's result). If something fails, upload the same folder/archive anyway —
`progress.log` and `results/*.log` tell me what happened.

## Troubleshooting
* `no C compiler found` → install one (see above).
* `missing src/...` → run from inside a full checkout (`git pull`), not a partial copy.
* `exit=` non-zero in `progress.log` → send the archive; re-running with `--rundir` retries only the failed jobs.
* Line-ending errors on Windows (`$'\r': command not found`) → run inside WSL, or `git config core.autocrlf input` and re-clone
  (`.gitattributes` already forces LF for `*.sh`).
