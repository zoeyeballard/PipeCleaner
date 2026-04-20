# <img src="assets/pipecleaner_logo.png" height="35" /> PipeCleaner

PipeCleaner is an educational MIPS performance analyzer used to compare
single-cycle timing against 5-stage pipelined timing on the same input program.

The project currently focuses on instruction parsing and metric reporting.
The main user-facing workflow is running `person6_metrics.py` on `.asm` inputs
(in assembly text or machine-word form).

## What It Does Right Now

- Parses a subset of MIPS instructions from:
  - Assembly source (e.g., `addi $t0, $zero, 5`)
  - 32-bit machine words in binary or hex (e.g., `0x20080005`)
- Supports labels for branch/jump targets.
- Computes and prints project-style reports for:
  - Non-pipeline mode (single-cycle timing reference)
  - Pipeline mode (5-stage timing with hazard-based stall estimates)
- Runs one file or all `.asm` files in a directory.

## Supported Instruction Subset

- R-type: `add`, `sub`, `and`, `or`, `slt`, `nop`
- I-type: `addi`, `lw`, `sw`, `beq`, `bne`
- J-type: `j`

Shared instruction metadata and register names live in `common.py`.

## Repository Structure

- `common.py`
  - Shared data contracts for instructions, CPU state, pipeline latches, hazards, logs, and metrics

- `person1_parser.py`
  - Program parser and decoder
  - Handles labels and branch-offset resolution
  - Accepts assembly and machine-code lines

- `rolandoU_alu.py`
  - Canonical ALU/register implementation (`alu_execute`, register read/write, sign extension)

- `person2_alu.py`
  - Compatibility wrapper that re-exports ALU functions from `rolandoU_alu.py`

- `person3_single_cycle.py`
  - Single-cycle execution path
  - Includes analytical helper `run_single_cycle_analyzer(...)` with timing table `DEFAULT_TIMING_PS`

- `person4_pipeline.py`
  - Pipeline-stage helpers plus pipeline metric path (`run_pipeline(...)`)
  - Uses hazard analysis to estimate stalls/cycles and compute pipelined metrics

- `person5_hazard.py`
  - Hazard utilities used by pipeline metrics
  - Includes static hazard counting (`analyze_hazards(...)`) and cycle-level helpers

- `person6_metrics.py`
  - Main CLI entry point and report formatter
  - Parses input files, runs single/pipeline analysis, and prints comparison output

- `input/`
  - Sample workloads in both assembly and machine-code forms

- `test_files/`
  - Mirror copy of core modules for isolated testing/reference

## Main Entry Point (Recommended)

Run from the project root:

```powershell
python person6_metrics.py input/balanced_mix1.asm
```

Analyze all `.asm` files in a directory:

```powershell
python person6_metrics.py --all --dir input
```

If your environment requires an explicit interpreter path on Windows, use it in
place of `python`.

## Typical Output

Reports include:

- Processed file list
- Instruction counts (`lw`, `sw`, `R-type`, `beq`)
- Non-pipeline section:
  - Per-instruction timing assumptions (ps)
  - CPI, total execution time, latency, throughput
- Pipeline section:
  - Derived pipelined clock
  - Stall cycles
  - CPI, total execution time, latency, throughput

## Notes on Current Model

- The parser and ALU paths are implemented and actively used.
- The metrics workflow is implemented and is the primary completed feature.
- Pipeline reporting is currently analytical/aggregate for performance output
  (hazard-informed cycle estimation), not a full per-stage timing waveform.
- Some stage-level helper functions exist for pipeline simulation, but CLI output
  is centered on metrics generation and report formatting.

## Quick Module-Level Runs

You can still execute individual modules for local checks:

```powershell
python person1_parser.py
python rolandoU_alu.py
python person3_single_cycle.py
python person4_pipeline.py
python person5_hazard.py
python person6_metrics.py input/balanced_mix1.asm
```

## Course Context

ECE 5367 - Computer Architecture (Spring 2026)

This codebase is structured as a collaborative multi-owner project where each
module keeps stable interfaces in `common.py`.
