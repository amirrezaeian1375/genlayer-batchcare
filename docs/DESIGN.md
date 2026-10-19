# BatchCare design boundary

Status: local contract and tests complete; **not deployed**. This is a recorded-instructions and authorization primitive, not a textile-safety assessor.

## The hard question

Can one exact professional-cleaning machine plan be admitted for a batch of 2–4 garments whose owners acknowledged their recorded care texts? A code-only contract can compare typed machine settings but cannot reliably interpret natural-language qualifications such as "hydrocarbon solvent only" or "gentle process". GenLayer consensus performs only that limited interpretation. Code combines the per-item classifications and owns every state transition.

## Actors and frozen inputs

- The caller of `open_batch` becomes the operator; only that address adds items, seals the batch and consumes a ticket.
- Each added item names an owner and a short **public transcription** of its care instructions (20–400 characters after trimming). A submitted address alone is not proof of label authenticity.
- `seal_batch` freezes the operator, plan method/intensity and the ordered owner/label-hash list under one SHA-256 commitment. Items cannot be added or edited after sealing.
- Each item's owner must call `confirm_item` with that exact complete seal. A responsible integrator should display the complete plan and all items before asking anyone to sign. Confirmation binds the signer's address to the stored seal; it cannot prove they read every item or that the transcription matches a physical label.

## GenLayer boundary and equivalence

- A review is permissionless but requires every item confirmation. Storage is read and copied to ordinary Python values before entering the non-deterministic block.
- The leader is asked to classify the chosen method and intensity **separately for every garment** as `ALLOW`, `DENY`, or `UNKNOWN`, grounded in short literal quotes from that garment's text. `UNKNOWN` has an empty quote; positive/negative classifications require a nonempty quote that occurs in the corresponding frozen text. The model never chooses the batch outcome or a ticket.
- The custom validator independently reruns the classification. It checks batch seal, item count and order, code-computed label hashes, and the entire action-driving method/intensity vector. Merely validating schema or agreeing on the final batch label would not be enough. Leader and validator quotes may select different valid spans, but each must be an exact substring of its own frozen item text. Consensus on text cannot make a forged physical transcription authentic.
- The accepted vector is revalidated in deterministic code before state changes. A `DENY` on either axis blocks that item; if any blocker exists, the batch is `SPLIT_BATCH`. Otherwise any `UNKNOWN` produces `HOLD_UNKNOWN`. All axes `ALLOW` produces `ADMISSIBLE` with a ticket bound to batch ID and seal. No ticket is issued for uncertainty or explicit conflict.

## State, replay and external action

`DRAFT -> SEALED -> ADMISSIBLE | SPLIT_BATCH | HOLD_UNKNOWN`.

Only `ADMISSIBLE` can transition to `CONSUMED`, exactly once, when the same operator supplies the correct ticket. A consuming application should read only finalized state and bind physical machinery to the same settings; this contract does **not** operate that machinery. There is no deposit, payout, frontend, operator override or cancellation in v1. A new plan or corrected transcription requires a new batch; the old one remains readable.

Batches are independent and globally enumerated per contract. Each item and report is stored under its batch ID and index. No contract call uses a caller-supplied oracle or external URL. Public care text can contain untrusted instructions attempting prompt injection; bounded JSON framing and validation reduce, but do not remove, that risk.

## Non-goals and review checks

- No assertion about fabric composition, care-symbol recognition, physical label identity, dry-cleaning chemistry, dye bleed, machine telemetry, actual service delivery, damage, or legal liability. The only consequence is a one-use onchain batch authorization **under the public transcriptions**.
- Inputs are not private. Do not put customer identities or sensitive notes in care_text.
- Bounds: 2–4 items, maximum 400 care-text characters per item, exact enum plan, 100-character quote cap, no unbounded report read.
- Test malicious leader verdict, changed decision vector, invalid quote/hash, duplicate owner confirmation, wrong signer, attempted plan mutation, unknown/blocked outcome, batch isolation and duplicate ticket consumption. Then lint, typecheck, test Direct Mode and exercise at least one admissible and one incompatible full-consensus path on Studionet before claiming live verification.
- Nearby work: [CareLabelGuide](https://github.com/paulinx2nd/carelabelguide) handles a single item's wash/bleach/dry/iron stage automaton. BatchCare's distinct boundary is multi-item professional-cycle intersection, owner confirmation of a batch-level seal and a one-use batch ticket.
