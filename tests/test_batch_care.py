"""Direct Mode tests execute the real contract with only the model boundary mocked."""

import hashlib
import json

import pytest


CONTRACT = "contracts/batch_care.py"
PROMPT = r"Interpret only the recorded garment care instructions"
LABEL_A = "Professional dry clean with hydrocarbon solvent only. Use a gentle process."
LABEL_B = "Professional dry clean with hydrocarbon or PCE solvents. Use a gentle process."
LABEL_C = "Professional cleaning recommended; consult a specialist before treatment."


def addr(value):
    return "0x" + value.hex()


def batch(contract, batch_id):
    return json.loads(contract.get_batch(batch_id))


def item(contract, batch_id, index):
    return json.loads(contract.get_item(batch_id, index))


def result(contract, batch_id):
    return json.loads(contract.get_report(batch_id))


def ruling(index, text, method, intensity, method_quote="", intensity_quote=""):
    return {
        "index": index,
        "label_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "method": method,
        "intensity": intensity,
        "method_quote": method_quote,
        "intensity_quote": intensity_quote,
    }


def allow_pair(vm):
    rows = [
        ruling(0, LABEL_A, "ALLOW", "ALLOW", "hydrocarbon solvent only", "gentle process"),
        ruling(1, LABEL_B, "ALLOW", "ALLOW", "hydrocarbon or PCE solvents", "gentle process"),
    ]
    for row in rows:
        del row["label_hash"]  # Models must not be asked to copy long hashes.
    vm.mock_llm(PROMPT, json.dumps({"items": rows}))


def sealed_pair(vm, deploy, operator, alice, bob, method="HYDROCARBON",
                intensity="GENTLE", label_b=LABEL_B):
    contract = deploy(CONTRACT)
    vm.sender = operator
    batch_id = contract.open_batch(method, intensity)
    contract.add_item(batch_id, addr(alice), LABEL_A)
    contract.add_item(batch_id, addr(bob), label_b)
    seal = contract.seal_batch(batch_id)
    vm.sender = alice
    contract.confirm_item(batch_id, 0, seal)
    vm.sender = bob
    contract.confirm_item(batch_id, 1, seal)
    return contract, batch_id, seal


def test_open_add_seal_confirm_freezes_all_terms(direct_vm, direct_deploy,
                                                   direct_owner, direct_alice, direct_bob):
    contract, batch_id, seal = sealed_pair(
        direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob
    )
    assert batch_id == "0" and contract.count() == 1
    state = batch(contract, batch_id)
    assert state["status"] == "SEALED" and state["confirmed"] == 2
    assert state["seal_hash"] == seal and len(seal) == 64
    assert item(contract, batch_id, 0)["owner"] == addr(direct_alice).lower()
    assert item(contract, batch_id, 1)["label_hash"] == hashlib.sha256(
        LABEL_B.encode()
    ).hexdigest()
    direct_vm.sender = direct_owner
    with direct_vm.expect_revert("Batch cannot accept more items"):
        contract.add_item(batch_id, addr(direct_owner), LABEL_C)
    with direct_vm.expect_revert("Batch needs at least two items before sealing"):
        contract.seal_batch(batch_id)


@pytest.mark.parametrize("method,intensity", [
    ("PERC", "GENTLE"), ("HYDROCARBON", "FAST"), ("wet", "NORMAL"),
    ("", "NORMAL"), ("WET", None),
])
def test_invalid_machine_cycle(direct_deploy, direct_vm, method, intensity):
    contract = direct_deploy(CONTRACT)
    with direct_vm.expect_revert("Unsupported machine cycle"):
        contract.open_batch(method, intensity)
    assert contract.count() == 0


@pytest.mark.parametrize("owner,text,error", [
    ("0x" + "0" * 40, LABEL_A, "zero address"),
    ("alice", LABEL_A, "20-byte address"),
    (None, LABEL_A, "20-byte address"),
    ("0x" + "1" * 40, "short", "outside the bounds"),
    ("0x" + "1" * 40, "x" * 401, "outside the bounds"),
    ("0x" + "1" * 40, None, "Invalid care instruction text"),
])
def test_add_item_input_guards(direct_deploy, direct_vm, owner, text, error):
    contract = direct_deploy(CONTRACT)
    batch_id = contract.open_batch("HYDROCARBON", "GENTLE")
    with direct_vm.expect_revert(error):
        contract.add_item(batch_id, owner, text)
    assert batch(contract, batch_id)["item_count"] == 0


def test_at_least_two_and_at_most_four_items(direct_deploy, direct_vm,
                                               direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    bid = contract.open_batch("WET", "NORMAL")
    with direct_vm.expect_revert("at least two"):
        contract.seal_batch(bid)
    for index in range(4):
        contract.add_item(bid, addr(direct_alice if index % 2 == 0 else direct_bob), LABEL_A)
    with direct_vm.expect_revert("cannot accept more items"):
        contract.add_item(bid, addr(direct_bob), LABEL_B)
    seal = contract.seal_batch(bid)
    assert len(seal) == 64 and batch(contract, bid)["item_count"] == 4


def test_only_owner_can_confirm_exact_seal_once(direct_vm, direct_deploy,
                                                   direct_owner, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_owner
    bid = contract.open_batch("HYDROCARBON", "GENTLE")
    contract.add_item(bid, addr(direct_alice), LABEL_A)
    contract.add_item(bid, addr(direct_bob), LABEL_B)
    with direct_vm.expect_revert("wrong state"):
        contract.confirm_item(bid, 0, "0" * 64)
    seal = contract.seal_batch(bid)
    direct_vm.sender = direct_owner
    with direct_vm.expect_revert("Only the recorded owner"):
        contract.confirm_item(bid, 0, seal)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("seal mismatch"):
        contract.confirm_item(bid, 0, "f" * 64)
    with direct_vm.expect_revert("Invalid item index"):
        contract.confirm_item(bid, 8, seal)
    contract.confirm_item(bid, 0, seal)
    with direct_vm.expect_revert("already confirmed"):
        contract.confirm_item(bid, 0, seal)
    assert batch(contract, bid)["confirmed"] == 1


def test_review_requires_every_owner_confirmation(direct_vm, direct_deploy,
                                                    direct_owner, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_owner
    bid = contract.open_batch("HYDROCARBON", "GENTLE")
    contract.add_item(bid, addr(direct_alice), LABEL_A)
    contract.add_item(bid, addr(direct_bob), LABEL_B)
    with direct_vm.expect_revert("Every item must be confirmed"):
        contract.review_batch(bid)
    seal = contract.seal_batch(bid)
    direct_vm.sender = direct_alice
    contract.confirm_item(bid, 0, seal)
    with direct_vm.expect_revert("Every item must be confirmed"):
        contract.review_batch(bid)
    assert contract.get_report(bid) == ""


def test_compatible_pair_produces_one_use_ticket(direct_vm, direct_deploy,
                                                   direct_owner, direct_alice, direct_bob):
    contract, bid, seal = sealed_pair(
        direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob
    )
    allow_pair(direct_vm)
    direct_vm.strict_mocks = True
    assert contract.review_batch(bid) == "ADMISSIBLE"
    assert direct_vm.run_validator() is True
    state = batch(contract, bid)
    assert state["seal_hash"] == seal and state["status"] == "ADMISSIBLE"
    assert state["blocked"] == [] and state["unknown"] == []
    assert len(state["ticket"]) == 64 and contract.ticket_ready(bid)
    assert len(result(contract, bid)) == 2
    assert result(contract, bid)[0]["label_hash"] == hashlib.sha256(LABEL_A.encode()).hexdigest()
    with direct_vm.expect_revert("Every item must be confirmed"):
        contract.review_batch(bid)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Only the operator"):
        contract.consume_ticket(bid, state["ticket"])
    direct_vm.sender = direct_owner
    with direct_vm.expect_revert("No valid ticket"):
        contract.consume_ticket(bid, "f" * 64)
    assert contract.consume_ticket(bid, state["ticket"]) == state["ticket"]
    assert batch(contract, bid)["status"] == "CONSUMED"
    assert not contract.ticket_ready(bid)
    with direct_vm.expect_revert("No valid ticket"):
        contract.consume_ticket(bid, state["ticket"])


def test_incompatible_solvent_blocks_the_pair(direct_vm, direct_deploy,
                                               direct_owner, direct_alice, direct_bob):
    contract, bid, _ = sealed_pair(
        direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, method="PCE"
    )
    direct_vm.mock_llm(PROMPT, json.dumps({"items": [
        ruling(0, LABEL_A, "DENY", "ALLOW", "hydrocarbon solvent only", "gentle process"),
        ruling(1, LABEL_B, "ALLOW", "ALLOW", "hydrocarbon or PCE solvents", "gentle process"),
    ]}))
    assert contract.review_batch(bid) == "SPLIT_BATCH"
    assert direct_vm.run_validator() is True
    state = batch(contract, bid)
    assert state["blocked"] == [0] and not contract.ticket_ready(bid)
    direct_vm.sender = direct_owner
    with direct_vm.expect_revert("No valid ticket"):
        contract.consume_ticket(bid, "0" * 64)


def test_normal_intensity_denied_for_gentle_only_labels(direct_vm, direct_deploy,
                                                           direct_owner, direct_alice, direct_bob):
    contract, bid, _ = sealed_pair(
        direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob,
        intensity="NORMAL"
    )
    direct_vm.mock_llm(PROMPT, json.dumps({"items": [
        ruling(0, LABEL_A, "ALLOW", "DENY", "hydrocarbon solvent only", "gentle process"),
        ruling(1, LABEL_B, "ALLOW", "DENY", "hydrocarbon or PCE solvents", "gentle process"),
    ]}))
    assert contract.review_batch(bid) == "SPLIT_BATCH"
    assert batch(contract, bid)["blocked"] == [0, 1]


def test_missing_care_detail_holds_instead_of_allowing(direct_vm, direct_deploy,
                                                         direct_owner, direct_alice, direct_bob):
    contract, bid, _ = sealed_pair(
        direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob, label_b=LABEL_C
    )
    direct_vm.mock_llm(PROMPT, json.dumps({"items": [
        ruling(0, LABEL_A, "ALLOW", "ALLOW", "hydrocarbon solvent only", "gentle process"),
        ruling(1, LABEL_C, "UNKNOWN", "UNKNOWN"),
    ]}))
    assert contract.review_batch(bid) == "HOLD_UNKNOWN"
    state = batch(contract, bid)
    assert state["unknown"] == [1] and state["ticket"] == ""
    assert not contract.ticket_ready(bid)


def test_explicit_denial_takes_priority_over_unknown(direct_vm, direct_deploy,
                                                       direct_owner, direct_alice, direct_bob):
    contract, bid, _ = sealed_pair(
        direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob,
        method="PCE", label_b=LABEL_C
    )
    direct_vm.mock_llm(PROMPT, json.dumps({"items": [
        ruling(0, LABEL_A, "DENY", "ALLOW", "hydrocarbon solvent only", "gentle process"),
        ruling(1, LABEL_C, "UNKNOWN", "UNKNOWN"),
    ]}))
    assert contract.review_batch(bid) == "SPLIT_BATCH"
    assert batch(contract, bid)["blocked"] == [0]
    assert batch(contract, bid)["unknown"] == [1]


@pytest.mark.parametrize("mutator", [
    lambda x: {"items": x["items"][:1]},
    lambda x: {"items": [x["items"][1], x["items"][0]]},
    lambda x: {"items": [{**x["items"][0], "label_hash": "0" * 64}, x["items"][1]]},
    lambda x: {"items": [{**x["items"][0], "method": "MAYBE"}, x["items"][1]]},
    lambda x: {"items": [{**x["items"][0], "method_quote": "not in label"}, x["items"][1]]},
    lambda x: {"items": [{**x["items"][0], "intensity_quote": ""}, x["items"][1]]},
    lambda x: {"items": [{**x["items"][0], "index": True}, x["items"][1]]},
    lambda x: {"items": [{**x["items"][0], "unexpected": 1}, x["items"][1]]},
    lambda x: {"items": [{**x["items"][0], "method": "UNKNOWN", "method_quote": "gentle process"}, x["items"][1]]},
])
def test_malformed_model_output_cannot_write_state(direct_vm, direct_deploy,
                                                    direct_owner, direct_alice, direct_bob,
                                                    mutator):
    contract, bid, _ = sealed_pair(
        direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob
    )
    normal = {"items": [
        ruling(0, LABEL_A, "ALLOW", "ALLOW", "hydrocarbon solvent only", "gentle process"),
        ruling(1, LABEL_B, "ALLOW", "ALLOW", "hydrocarbon or PCE solvents", "gentle process"),
    ]}
    direct_vm.mock_llm(PROMPT, json.dumps(mutator(normal)))
    with direct_vm.expect_revert():
        contract.review_batch(bid)
    assert batch(contract, bid)["status"] == "SEALED"
    assert contract.get_report(bid) == ""


def test_validator_rejects_different_consequential_vector(direct_vm, direct_deploy,
                                                             direct_owner, direct_alice, direct_bob):
    contract, bid, seal = sealed_pair(
        direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob
    )
    allow_pair(direct_vm)
    assert contract.review_batch(bid) == "ADMISSIBLE"
    truth = {"seal_hash": seal, "items": result(contract, bid)}
    assert direct_vm.run_validator(leader_result=truth) is True
    forged = {"seal_hash": seal, "items": [
        {**truth["items"][0], "method": "DENY"}, truth["items"][1]
    ]}
    assert direct_vm.run_validator(leader_result=forged) is False
    assert direct_vm.run_validator(leader_result={**truth, "seal_hash": "0" * 64}) is False
    assert direct_vm.run_validator(leader_result={**truth, "items": truth["items"][:1]}) is False
    assert direct_vm.run_validator(leader_error=RuntimeError("leader crashed")) is False


def test_validator_rejects_semantic_dissent_on_same_labels(direct_vm, direct_deploy,
                                                             direct_owner, direct_alice, direct_bob):
    contract, bid, _ = sealed_pair(
        direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob
    )
    allow_pair(direct_vm)
    contract.review_batch(bid)
    direct_vm.clear_mocks()
    direct_vm.mock_llm(PROMPT, json.dumps({"items": [
        ruling(0, LABEL_A, "DENY", "ALLOW", "hydrocarbon solvent only", "gentle process"),
        ruling(1, LABEL_B, "ALLOW", "ALLOW", "hydrocarbon or PCE solvents", "gentle process"),
    ]}))
    assert direct_vm.run_validator() is False


def test_unrelated_batches_are_isolated(direct_vm, direct_deploy,
                                         direct_owner, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_owner
    first = contract.open_batch("HYDROCARBON", "GENTLE")
    second = contract.open_batch("WET", "NORMAL")
    contract.add_item(first, addr(direct_alice), LABEL_A)
    contract.add_item(second, addr(direct_bob), LABEL_B)
    assert contract.count() == 2
    assert batch(contract, first)["item_count"] == 1
    assert batch(contract, second)["item_count"] == 1
    assert contract.get_report(first) == "" and contract.get_report(second) == ""


def test_operator_authorization_and_per_item_owner(direct_vm, direct_deploy,
                                                    direct_owner, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_owner
    bid = contract.open_batch("HYDROCARBON", "GENTLE")
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Only the operator can add items"):
        contract.add_item(bid, addr(direct_alice), LABEL_A)
    direct_vm.sender = direct_owner
    contract.add_item(bid, addr(direct_alice), LABEL_A)
    contract.add_item(bid, addr(direct_bob), LABEL_B)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Only the operator can seal"):
        contract.seal_batch(bid)
    direct_vm.sender = direct_owner
    seal = contract.seal_batch(bid)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Only the recorded owner"):
        contract.confirm_item(bid, 1, seal)
    contract.confirm_item(bid, 0, seal)
    assert batch(contract, bid)["confirmed"] == 1


def test_seal_binds_machine_cycle_and_item_order(direct_vm, direct_deploy,
                                                  direct_owner, direct_alice, direct_bob):
    contract = direct_deploy(CONTRACT)
    direct_vm.sender = direct_owner
    seals = []
    for method, texts in (("HYDROCARBON", (LABEL_A, LABEL_B)),
                          ("PCE", (LABEL_A, LABEL_B)),
                          ("HYDROCARBON", (LABEL_B, LABEL_A))):
        bid = contract.open_batch(method, "GENTLE")
        contract.add_item(bid, addr(direct_alice), texts[0])
        contract.add_item(bid, addr(direct_bob), texts[1])
        seals.append(contract.seal_batch(bid))
    assert len(set(seals)) == 3


def test_validator_tolerates_distinct_valid_quote_spans(direct_vm, direct_deploy,
                                                         direct_owner, direct_alice, direct_bob):
    contract, bid, _ = sealed_pair(
        direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob
    )
    allow_pair(direct_vm)
    contract.review_batch(bid)
    direct_vm.clear_mocks()
    direct_vm.mock_llm(PROMPT, json.dumps({"items": [
        ruling(0, LABEL_A, "ALLOW", "ALLOW",
               "Professional dry clean with hydrocarbon solvent only", "Use a gentle process"),
        ruling(1, LABEL_B, "ALLOW", "ALLOW",
               "Professional dry clean with hydrocarbon or PCE solvents", "Use a gentle process"),
    ]}))
    assert direct_vm.run_validator() is True
