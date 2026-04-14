# ECE 5367 Final Project — Pipelined Performance Analyzer
## Group Reference Guide | Spring 2026 | Due: April 20

---

## File Map

```
test_files/
├── common.py               ← SHARED — everyone imports from here. Do not modify alone.
├── person1_parser.py       ← Person 1: MIPS text → instruction dicts
├── person2_alu.py          ← Person 2: ALU operations + register file
├── person3_single_cycle.py ← Person 3: Single-cycle execution loop
├── person4_pipeline.py     ← Alex: 5-stage pipeline (IF/ID/EX/MEM/WB)
├── person5_hazard.py       ← Person 5: Hazard detection + forwarding unit
└── person6_metrics.py      ← Person 6: Metrics, test programs, comparison report
```

---

## Ground Rules

1. **Never modify common.py alone.** Any struct change needs group agreement.
2. **Each file has a `USE_STUBS` flag at the top.** Keep it `True` while your
   dependencies are in progress. Flip it to `False` when you're ready to integrate.
3. **Run your own file's self-test daily:** `python personX_yourfile.py`
4. **Don't rename or reorder function arguments.** Other people's code calls your functions.

---

## Who Depends on Whom

```
common.py
   ├── person1_parser.py       (no deps — start immediately)
   ├── person2_alu.py          (no deps — start immediately)
   ├── person3_single_cycle.py (uses 1 + 2, but has stubs)
   ├── person4_pipeline.py     (uses 2 + 5, but has stubs)
   ├── person5_hazard.py       (no deps — start immediately)
   └── person6_metrics.py      (uses 3 + 4, but has stubs)
```

**Persons 1, 2, and 5 are fully unblocked from day one.**
Persons 3, 4, and 6 have stub modes so they can build in parallel.

---

## Integration Checklist

When you're ready to plug in a real module, do this:

### Person 3 (integrating 1 & 2):
```python
# person3_single_cycle.py, top of file:
USE_STUBS = False          # ← change this
from person1_parser import parse_program
from person2_alu import alu_execute, register_read, register_write, sign_extend
```
Then run: `python person3_single_cycle.py` and verify register outputs match expected.

### Person 4 (integrating 2 & 5):
```python
# person4_pipeline.py, top of file:
USE_STUBS = False
from person2_alu import alu_execute, register_read, register_write, sign_extend
from person5_hazard import detect_hazards
```

### Person 6 (integrating 3 & 4):
```python
# person6_metrics.py, top of file:
USE_STUBS = False
from person3_single_cycle import run_single_cycle
from person4_pipeline import run_pipeline
from person1_parser import parse_program
```

---

## Test Programs (Person 6 owns these)

All programs live in `person6_metrics.get_test_programs()`. Use them for your own tests too:

```python
from person6_metrics import get_test_programs
programs = get_test_programs()
source = programs["raw_hazard"]   # or any other key
```

| Name              | Tests                              |
|-------------------|------------------------------------|
| no_hazards        | Basic correctness, no forwarding   |
| raw_hazard        | Read-after-write, forwarding path  |
| load_use_hazard   | LW stall (1 bubble required)       |
| branch_not_taken  | BEQ not taken — no flush           |
| branch_taken      | BEQ taken — 2 flush cycles         |
| memory_ops        | SW then LW                         |
| mixed_hazards     | Multiple hazard types together     |

---

## Expected Final Output

Running `python person6_metrics.py` with all stubs removed should produce a table like:

```
╔══════════════════════════════════════════╗
║  MIPS Performance Analysis: raw_hazard   ║
╠═════════════════╦═══════════╦════════════╣
║ Metric          ║ Single    ║ Pipelined  ║
╠═════════════════╬═══════════╬════════════╣
║ Total Cycles    ║     2     ║     4      ║
║ CPI             ║   1.000   ║   2.000    ║
║ Throughput(IPC) ║   1.000   ║   0.500    ║
║ Stall Cycles    ║     0     ║     1      ║
╠═════════════════╩═══════════╩════════════╣
║ Speedup (single/pipelined): 0.50x        ║
╚══════════════════════════════════════════╝
```

---

## Suggested Timeline

| Day        | Goal                                                              |
|------------|-------------------------------------------------------------------|
| Tue Apr 14 | Everyone reads common.py and their own stub file                  |
| Wed Apr 15 | Person 1, 2, 5 self-tests passing, all people finish all programs              |
| Thu Apr 16 | Person 3 integrated (1+2), Person 4 integrated (2+5)              |
| Fri Apr 17 | Person 6 integrated (3+4), full comparison report running         |
| Sat Apr 18 | All test programs pass, edge cases verified, report written       |
| Sun Apr 19 | Submit                                                            |

---

## Quick Debugging Reference

**"My output is wrong but no errors"** — Add `print()` statements after each stage call
in person4_pipeline.py to trace pipeline register values cycle by cycle.

**"Forwarding not working"** — Print `hazard_signals` at the top of each cycle in
person4_pipeline.py's loop before the stages run.

**"Branch is wrong"** — Confirm PC update logic in person3 (_compute_next_pc) and
person5 (needs_flush) are consistent on what "branch taken" means.

**"Metrics seem off"** — Confirm person6's cycle counting matches: pipeline needs
`n + 4` cycles minimum (fill + drain) even with zero hazards.