# <img src="assets/pipecleaner.png" height="40" /> PipeCleaner

PipeCleaner is an educational MIPS CPU simulation project for comparing a
single-cycle processor against a classic 5-stage pipelined processor.
The project is designed for collaborative development, where each module owner
implements one part of the system and all parts integrate through shared
interfaces in `common.py`.

## Project Objective

Build a consistent simulation framework that can:

- Parse a subset of MIPS assembly into a canonical instruction format.
- Execute the same program with two processor models:
	- Single-cycle
	- 5-stage pipelined (IF, ID, EX, MEM, WB)
- Model hazards (data and control) with stalls, flushes, and forwarding.
- Collect execution logs and compute performance metrics.
- Compare architectural trade-offs using CPI, latency, throughput, and speedup.

## Key Learning Outcomes

- Understand how datapath organization affects performance.
- See why pipelining improves throughput but introduces hazards.
- Practice decomposition of a CPU into clean, testable modules.
- Use interface contracts to integrate independently developed components.
- Quantify performance, not just functional correctness.

## Supported Instruction Subset

Current shared definitions target this subset:

- R-type: add, sub, and, or, slt, nop
- I-type: addi, lw, sw, beq, bne
- J-type: j

Instruction metadata and register names are defined centrally in `common.py`.

## Repository Structure

### Core Modules

- `common.py`
	- Shared instruction/state constructors
	- Pipeline latch layouts
	- Hazard signal and metric containers
	- Instruction and register reference tables

- `person1_parser.py`
	- Parses assembly source into instruction dictionaries
	- Resolves labels into PC-relative/immediate targets

- `person2_alu.py`
	- ALU operations (add/sub/and/or/slt)
	- Register read/write behavior
	- Sign extension helper

- `person3_single_cycle.py`
	- Single-cycle simulation loop
	- Executes one instruction per cycle
	- Produces final CPU state, log, and metrics

- `person4_pipeline.py`
	- Stage-level pipeline logic (IF/ID/EX/MEM/WB)
	- Main cycle-accurate pipeline loop
	- Integrates hazard signals and forwarding behavior

- `person5_hazard.py`
	- Hazard detection unit logic
	- Stall and flush decisions
	- Forwarding path selection

- `person6_metrics.py`
	- Shared test programs
	- Metric computation from logs
	- Single-cycle vs pipelined comparison reporting

### Mirror Test Workspace

The `test_files/` directory mirrors the same module layout for isolated testing
and reference scaffolding.

## Shared Data Contracts

All modules communicate through dictionary structures created by helper
functions in `common.py`.

- Instruction objects: `make_instruction(...)`
- CPU state: `make_cpu_state()`
- Pipeline latches: `make_pipeline_registers()`
- Hazard signals: `make_hazard_signals()`
- Log entries: `make_log_entry(...)`
- Metrics container: `make_metrics()`

Important integration rule:

- Keep these signatures and field names stable while developing modules in
	parallel.

## Execution Models

### Single-Cycle Model

For each instruction:

1. Fetch from PC
2. Decode and read registers
3. Execute ALU operation
4. Access memory (if needed)
5. Write back result (if needed)
6. Update PC

Properties:

- Functional baseline for correctness
- CPI target is ideally 1.0 in this simplified simulator
- Easier to debug than the pipeline

### 5-Stage Pipeline Model

Stages:

1. IF: Instruction Fetch
2. ID: Decode/Register Read
3. EX: Execute/Address/Branch Decision
4. MEM: Memory Access
5. WB: Register Write Back

Properties:

- Multiple instructions overlap in time
- Improved throughput potential
- Requires hazard management to preserve correctness

## Hazard Handling Scope

The hazard unit is expected to support:

- Load-use hazard detection and stall insertion
- Branch-related flush behavior when control flow changes
- ALU input forwarding from EX/MEM and MEM/WB latches

Events should be reflected in logs so performance penalties can be measured.

## Performance Metrics

The comparison engine computes:

- Total instructions
- Total cycles
- Stall cycles
- Flush cycles
- CPI = total_cycles / total_instructions
- Latency = total_cycles * clock_period
- Throughput (IPC) = total_instructions / total_cycles
- Speedup = single_cycle_cycles / pipelined_cycles

Interpretation guideline:

- Pipelined designs typically improve throughput, but CPI can increase above 1
	when hazards force bubbles.

## Development and Integration Strategy

Each module includes stable function signatures and self-test blocks. Several
files include a `USE_STUBS` toggle so development can proceed before all
dependencies are complete.

Typical workflow:

1. Build and test each module independently.
2. Keep stubs enabled while upstream modules are incomplete.
3. Disable stubs and integrate real imports incrementally.
4. Validate behavior with shared test programs.
5. Run end-to-end comparison through metrics reporting.

## Running the Modules

From the project root:

```bash
python person1_parser.py
python person2_alu.py
python person3_single_cycle.py
python person4_pipeline.py
python person5_hazard.py
python person6_metrics.py
```

Each file contains a quick self-test section under `if __name__ == "__main__":`.

## Test Program Coverage

`person6_metrics.py` defines reusable programs covering:

- No-hazard baseline
- RAW hazards
- Load-use hazards
- Branch taken / not taken
- Memory store/load behavior
- Mixed hazard scenarios

These tests are intended to verify both correctness and performance effects.

## Current Implementation Status

The repository currently provides strong scaffolding with shared interfaces,
module contracts, and test templates. Several functions are intentionally left
as `NotImplementedError` placeholders to be completed per module ownership.

Once all module TODOs are implemented and stubs are disabled, the final output
should be a complete comparative performance analyzer for single-cycle and
pipelined MIPS execution.
