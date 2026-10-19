# Studionet deployment record

Observed 2026-10-19. These are hosted development-network results from synthetic public care texts, not observations of real garments, machines or service delivery.

- Network: GenLayer Studionet, chain ID `61999`.
- Contract: [`0x4D34b41d39c493fC9F306004EaA600c91b902203`](https://explorer-studio.genlayer.com/address/0x4D34b41d39c493fC9F306004EaA600c91b902203).
- Operator/deployer: `0x3d9E39265d74511065f88C987f898c1d02892f3e`.
- Second item owner: `0x4b6D51a58987362CfA3619D2fF1F434994fD2423`.
- Runner pinned in source: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.

## Real transaction record

All 16 calls below are FINALIZED with GenVM SUCCESS and accepted consensus in Normal (Full Consensus) mode. Both review transactions show five initial validators and zero leader rotations. No GEN value was sent with the calls.

| Action | Explorer transaction | Observed effect |
| --- | --- | --- |
| Deploy | [`0x597a9e4b...b941e0d5`](https://explorer-studio.genlayer.com/tx/0x597a9e4ba7a439dcca12890f331ec81964d780a1107d5517997fed9db941e0d5) | `BatchCare` deployed. |
| Open batch `0`: `HYDROCARBON/GENTLE` | [`0x840ff37e...75fb57d0`](https://explorer-studio.genlayer.com/tx/0x840ff37ee8f8c11b59f83af52cfec5e4b6a33f66fb0c3c6295eafbfa75fb57d0) | Returned batch ID `0`. |
| Add item `0` (operator owns it) | [`0xb48ebce6...7d414d88`](https://explorer-studio.genlayer.com/tx/0xb48ebce696c143c037682fa37e24dc3cb50d1551f8e5c8b0355cd3357d414d88) | Hydrocarbon-only, gentle-process text; returned index `0`. |
| Add item `1` (second owner) | [`0x6051a6b4...db69a555`](https://explorer-studio.genlayer.com/tx/0x6051a6b46edee4ec8d7a2f8d0fdb6351f0135095d27e9ee25ab85304db69a555) | Hydrocarbon-or-PCE, gentle-process text; returned index `1`. |
| Seal batch `0` | [`0xe4952407...dbaba73f`](https://explorer-studio.genlayer.com/tx/0xe4952407bdbf16256dd8e7edb77f3365f5927f4a55ba2045035435efdbaba73f) | Seal `04529c84181e9df0511fcc8af0cead082dc4ee90fd598bbd6ff1c4975161166e`. |
| Operator confirms item `0` | [`0x9eec3afd...3848ec6a`](https://explorer-studio.genlayer.com/tx/0x9eec3afd0c79b4d7d34b5a7716e205c74fca2fc92f882c72fe3dc1973848ec6a) | Correct owner and seal. |
| Second owner confirms item `1` | [`0x7b27ae91...031bd942`](https://explorer-studio.genlayer.com/tx/0x7b27ae91710229f280edbb1cbe49699390dcd27601b119893f3a2ef4031bd942) | Independent signer; correct seal. |
| Review batch `0` | [`0xbec10524...ce3e0edd`](https://explorer-studio.genlayer.com/tx/0xbec105240a281cf6dc44f11d7637457d0bfef020edce976440d9369cce3e0edd) | `ADMISSIBLE`; all four item-axis classifications `ALLOW`. |
| Operator consumes ticket | [`0x81860560...4c71f418`](https://explorer-studio.genlayer.com/tx/0x81860560995d1c0928353f0122996c9cb0e206d79f885c860ba954ac4c71f418) | Exact ticket `0e2655646324eb723862b9ebad9fef62acd7f6a36a79219fde9e3712a64fee33` consumed. |
| Open batch `1`: `PCE/GENTLE` | [`0x13370a32...f2f2a0f8`](https://explorer-studio.genlayer.com/tx/0x13370a32ff4d7f5fa249f8bb4729ae62afa801b8e160d90e97c12beff2f2a0f8) | Returned batch ID `1`. |
| Add item `0` | [`0x343d0168...17825697`](https://explorer-studio.genlayer.com/tx/0x343d0168cc9da27af2eb426c0e6c9aea53c61838b5b86bac1f83ec0717825697) | Same hydrocarbon-only text. |
| Add item `1` | [`0x5b3a6a64...85b5fcc9`](https://explorer-studio.genlayer.com/tx/0x5b3a6a64a26447d4c4b9d6fb3b1729d46110f2367f7f54f8307beb4785b5fcc9) | Same hydrocarbon-or-PCE text. |
| Seal batch `1` | [`0xc8b0a3a7...d74650d9`](https://explorer-studio.genlayer.com/tx/0xc8b0a3a73f3a1c2897b6bec1383120d30d49f2198f7f1b224dd900abd74650d9) | Seal `e2000d8c58ef5c9f82ff7ba9237614d598326f6d88f3e0d24aa0d47d6ab256a9`. |
| Operator confirms item `0` | [`0xb7e01b04...da1535e4`](https://explorer-studio.genlayer.com/tx/0xb7e01b04f53be464be5e45665f301f980a9b62beb1c586b843b199bada1535e4) | Correct signer and seal. |
| Second owner confirms item `1` | [`0x6c6e2170...8e10ac72`](https://explorer-studio.genlayer.com/tx/0x6c6e21705bba1c12901d79a450de581a0f410ff5968486d20d3767ab8e10ac72) | Correct signer and seal. |
| Review batch `1` | [`0xad21fc32...6a59a8c7`](https://explorer-studio.genlayer.com/tx/0xad21fc32e47671caf949b33a9d50d3753cada266b0761e2f7fd39e6a6a59a8c7) | `SPLIT_BATCH`; item `0` method `DENY`, item `1` method `ALLOW`. |

Both seals were independently recomputed from the published method/intensity, ordered owner addresses and the exact two synthetic care texts. The two review receipts include a complete per-item vector and literal spans. `HOLD_UNKNOWN` and duplicate-ticket rejection have local-test coverage only, not live receipts.

## Finalized state reads

The Studio Read Methods selector was set to **Finalized**:

- `get_batch("0")` after review: `status=ADMISSIBLE`, `confirmed=2`, `blocked=[]`, `unknown=[]`, ticket `0e2655646324eb723862b9ebad9fef62acd7f6a36a79219fde9e3712a64fee33`.
- `get_report("0")`: both items had method/intensity `ALLOW` and literal quotes from their respective public care texts. After operator consumption, `get_batch("0")` returned `status=CONSUMED`; `ticket_ready("0")` should therefore be false by code, but was **not** independently read onchain.
- `get_batch("1")`: `status=SPLIT_BATCH`, `confirmed=2`, `blocked=[0]`, `unknown=[]`, `ticket=""`. No approval ticket exists for the incompatible plan.

These are readbacks of publicly declared care-text constraints. They are not proof that either text came from a sewn-in care label or that any machine was used.

## Deployed source parity

- Repository file `contracts/batch_care.py`: 13,766 bytes (LF, final newline); SHA-256 `1d4ef1a728caa3290c42043a792a0cd2a2c977d137f916d9cab8665c2ec7fecd`.
- `gen_getContractCode` from Studionet: 14,080 bytes (CRLF, no final newline); SHA-256 `1349ff4f88cbfc73c173f40e3e4dbfc758f69eb24f02567c1e2646fa40107f79`.
- **Raw byte equality: false. Normalized text equality: true.** Replacing onchain CRLF with LF and adding the missing final LF yields the repository file exactly. No code-token changes were found. Do not claim byte-for-byte source parity.

To reproduce: POST JSON-RPC `gen_getContractCode` to `https://studio.genlayer.com/api` with `params` containing only the contract address as a **string**; base64-decode `result` and compare source after the two line-ending adjustments. Studio state can reset, so verify the address remains available before relying on it.

## Local verification

`genvm-lint check contracts/batch_care.py` and `genvm-lint typecheck contracts/batch_care.py` passed locally. `python -m pytest tests -q` completed **35 Direct Mode tests** against the actual contract with LLM calls mocked. Studionet `gen_getContractSchemaForCode` also returned all 11 public methods before deployment. Local Direct Mode tests do not exercise a distributed validator network; the two live `review_batch` receipts above do.

Use the pinned requirements in `requirements-dev.txt` and `scripts/prepare_test_sdk.py` to reproduce; activate your virtual environment first. This is a bounded proof of an authorization workflow over agreed public transcriptions, not professional dry-cleaning advice, damage attribution or real-world execution verification.
