# BatchCare

A dry cleaner can process several garments in one machine cycle only when the **recorded care instructions for every item** support the same settings. BatchCare is a standalone GenLayer contract for checking a proposed professional-cleaning batch and issuing a one-use, plan-bound ticket when all its owner-confirmed instructions agree.

**Status:** local prototype. `genvm-lint check` and type checking pass; 35 Direct Mode tests pass with a mocked LLM. There is **no deployment or live validator receipt yet**. Do not submit this as a verified GenLayer build until the live paths have been exercised and linked.

## What it decides

An operator opens a batch with one chosen method (`HYDROCARBON`, `PCE`, or `WET`) and one intensity (`GENTLE` or `NORMAL`). The operator adds 2–4 garments with short public written care instructions and the address of each item owner. Sealing freezes the operator, plan, owner list and care-text hashes. Each owner confirms the exact seal from their own wallet. The operator cannot change the batch after that.

| Review status | Meaning | One-use ticket? |
| --- | --- | --- |
| `ADMISSIBLE` | Every item explicitly allows both the chosen method and intensity. | Yes, for this sealed batch and plan only. |
| `SPLIT_BATCH` | At least one recorded instruction explicitly excludes a chosen setting. The report names the blocking item indices. | No. |
| `HOLD_UNKNOWN` | No explicit blocker, but at least one required instruction is unclear or missing. Silence never means permission. | No. |

A ticket can be consumed once by the recorded operator. The contract does **not** turn on a machine, move GEN, certify care-label authenticity, inspect fabric, verify what settings were actually used, or guarantee textile safety. The onchain decision is about the agreed transcription and typed plan only.

## Where consensus is used

`review_batch` copies the already-sealed public care texts into memory before entering a GenLayer non-deterministic block. A leader evaluates *each garment separately*, producing two restricted classifications (method and intensity) plus literal quotes from that garment's text. Each validator independently repeats the reading. The custom validator checks the entire ordered decision vector and text hashes; it does not merely check JSON syntax or the final batch result. Valid quotes can differ in wording, but must occur verbatim in their respective recorded texts.

The LLM cannot choose `ADMISSIBLE` or create a ticket. Once the bounded extraction reaches consensus, ordinary contract code applies this fixed rule: any `DENY` -> `SPLIT_BATCH`; otherwise any `UNKNOWN` -> `HOLD_UNKNOWN`; only all `ALLOW` -> `ADMISSIBLE`. Long label hashes are computed by code, not copied by the model. Malformed output, bad quotes and divergent validator classifications prevent a review from being stored.

## State and methods

Lifecycle: `DRAFT -> SEALED -> ADMISSIBLE | SPLIT_BATCH | HOLD_UNKNOWN`, with `ADMISSIBLE -> CONSUMED` permitted exactly once. A blocked or unknown batch needs a new batch with different terms; there is no owner-controlled verdict override.

| Method | Role / purpose |
| --- | --- |
| `open_batch(method, intensity)` | Caller becomes the operator. |
| `add_item(batch_id, owner, care_text)` | Operator adds a garment in DRAFT, maximum four. |
| `seal_batch(batch_id)` | Operator freezes plan, item order, owners and care-text hashes. |
| `confirm_item(batch_id, index, expected_seal)` | The recorded item's owner acknowledges that complete seal. |
| `review_batch(batch_id)` | Anyone may trigger consensus once every item is confirmed. |
| `consume_ticket(batch_id, expected_ticket)` | Operator consumes an admissible ticket once. |
| `get_batch`, `get_item`, `get_report`, `ticket_ready`, `count` | Public reads. Use finalized state for durable decisions. |

All inputs and reports are public. Do not enter private customer information or confidential garment notes. See [docs/DESIGN.md](docs/DESIGN.md) for the trust boundary and tests.

## Local checks

From this repository root (Python 3.12+):

1. `python3 -m venv .venv`
2. `source .venv/bin/activate` (on Windows PowerShell: `.venv\Scripts\Activate.ps1`)
3. `python -m pip install -r requirements-dev.txt`
4. `python scripts/prepare_test_sdk.py`
5. `genvm-lint check contracts/batch_care.py`
6. `python -m pytest tests -q`

Keep the virtual environment activated so the preparation script can find `genvm-lint` on your PATH. The preparation script only bridges an upstream SDK release-asset name mismatch. The 35 local tests exercise the actual contract with a mocked model: two-party confirmations, immutable seals, compatible and blocked batches, ambiguity holds, malicious leader results, wrong quotes, unauthorized calls and replayed tickets. Direct Mode is not a distributed validator test.

## Related work and limits

[CareLabelGuide](https://github.com/paulinx2nd/carelabelguide) already compiles single-garment written instructions into a wash/bleach/dry/iron cycle automaton. BatchCare instead judges **a shared professional-cleaning plan against several owner-confirmed items** and issues a single-use batch ticket; no code is copied from that project. Grouping garments by care labels is not a new idea outside GenLayer, and this project makes no first-ever claim.

This contract does not authenticate a sewn-in label or measure chemical compatibility, dye transfer, actual machine use, or garment damage. `ADMISSIBLE` means only that the recorded texts support the selected method and intensity under consensus. Live Studio outcomes and exact deployed-source identity must be added before a Builder submission.

License: MIT. See [LICENSE](LICENSE).
