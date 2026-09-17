#!/usr/bin/env python3
"""Verify a Meridian deployment is the file you reviewed.

    python scripts/verify_deployment.py                 # address from deployments/studionet.json
    python scripts/verify_deployment.py 0xADDRESS
    python scripts/verify_deployment.py 0xADDRESS --rpc https://studio.genlayer.com/api
    python scripts/verify_deployment.py 0xADDRESS --onchain-source saved_from_explorer.py

Why this exists: paste-deployments make "what I reviewed" and "what is live"
two different files. This script closes the gap three ways:

  1. BYTE-FOR-BYTE: fetch the on-chain source over JSON-RPC (best effort -
     Studio's method set changes between releases) and compare it with
     contracts/meridian.py, printing both SHA-256 digests. If the network
     won't cooperate, use --onchain-source with the source view from the
     explorer and the same comparison still runs.
  2. STATIC PREFLIGHT: the schema-killers that can't hide behind a hash:
     runner header on line 1, exactly one gl.Contract subclass, an explicit
     constructor, @allow_storage on every storage dataclass.

Exit code 0 means clean. Anything else is a reason to stop, not a detail.

Stdlib only. No third-party imports, ever.
"""

import argparse
import ast
import base64
import hashlib
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).parent.parent
LOCAL_SOURCE = ROOT / "contracts" / "meridian.py"
DEFAULT_RECORD = ROOT / "deployments" / "studionet.json"
DEFAULT_RPC = "https://studio.genlayer.com/api"

# Studio has shipped several method names for source retrieval across
# releases; try them all before giving up with instructions.
RPC_METHODS = ("gen_getContractCode", "gen_getCode", "eth_getCode")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rpc(rpc_url: str, method: str, params: list):
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    req = urllib.request.Request(
        rpc_url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode())
    if "error" in payload and payload["error"]:
        raise RuntimeError(str(payload["error"])[:200])
    return payload.get("result")


def decode_source(result) -> bytes | None:
    """Best-effort decoding of whatever the RPC returned into source bytes."""
    if result is None:
        return None
    if isinstance(result, dict):
        for key in ("source", "code", "data"):
            if key in result:
                return decode_source(result[key])
        return None
    if not isinstance(result, str):
        return None
    s = result.strip()
    if not s:
        return None
    if s.startswith("0x"):
        try:
            return bytes.fromhex(s[2:])
        except ValueError:
            return None
    if s.startswith("#") or "gl.Contract" in s:
        return s.encode()
    try:
        return base64.b64decode(s)
    except Exception:
        return s.encode()


def fetch_onchain_source(address: str, rpc_url: str) -> bytes | None:
    errors = []
    for method in RPC_METHODS:
        for params in ([address], [{"address": address}]):
            try:
                raw = rpc(rpc_url, method, params)
                decoded = decode_source(raw)
                if decoded and b"Meridian" in decoded:
                    return decoded
                if decoded:
                    errors.append(f"{method}: returned {len(decoded)} bytes, not this contract")
            except Exception as e:  # method unknown, network down, wrong shape
                errors.append(f"{method}: {str(e)[:80]}")
    print("  (rpc attempts exhausted:", "; ".join(errors[:4]), ")")
    return None


def static_preflight(src: bytes, label: str) -> list[str]:
    """The four schema-killers that decide whether Studio can even build a
    schema. Returns a list of problems (empty means clean)."""
    problems = []
    text = src.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("#") or "Depends" not in lines[0]:
        problems.append(f"{label}: missing the runner header on line 1")
    tree = ast.parse(text, filename=label)
    contracts = [
        n
        for n in tree.body
        if isinstance(n, ast.ClassDef)
        and any(isinstance(b, ast.Attribute) and b.attr == "Contract" for b in n.bases)
    ]
    if len(contracts) != 1:
        problems.append(f"{label}: {len(contracts)} gl.Contract subclasses, need exactly one")
    else:
        if not any(
            isinstance(f, ast.FunctionDef) and f.name == "__init__" for f in contracts[0].body
        ):
            problems.append(f"{label}: no __init__ - schema raises TypeError('__init__ is absent')")
    for cls in tree.body:
        if isinstance(cls, ast.ClassDef):
            decs = [d.id if isinstance(d, ast.Name) else getattr(d, "attr", "") for d in cls.decorator_list]
            if "dataclass" in decs and "allow_storage" not in decs:
                problems.append(f"{label}: storage dataclass {cls.name} lacks @allow_storage")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("address", nargs="?", help="deployed contract address (default: deployments/studionet.json)")
    ap.add_argument("--rpc", default=DEFAULT_RPC, help="JSON-RPC endpoint")
    ap.add_argument("--onchain-source", metavar="FILE", help="source saved from the explorer's source view")
    ap.add_argument("--local", default=str(LOCAL_SOURCE), help="local file the deployment should match")
    args = ap.parse_args()

    address = args.address
    if not address and DEFAULT_RECORD.exists():
        record = json.loads(DEFAULT_RECORD.read_text())
        address = record["address"]
        args.rpc = args.rpc or DEFAULT_RPC
    if not address:
        ap.error("no address given and no deployments/studionet.json found")

    local_path = pathlib.Path(args.local)
    local = local_path.read_bytes()
    print(f"local   {local_path}  sha256 {sha256(local)[:16]}…")

    if args.onchain_source:
        onchain = pathlib.Path(args.onchain_source).read_bytes()
        print(f"on-chain (from explorer paste, {args.onchain_source})  sha256 {sha256(onchain)[:16]}…")
    else:
        print(f"on-chain {address} via {args.rpc}")
        onchain = fetch_onchain_source(address, args.rpc)

    ok = True
    if onchain is None:
        print("\nRESULT: SKIP - could not fetch on-chain source automatically.")
        print("Open the explorer's source view for the address, save it, then:")
        print(f"  python scripts/verify_deployment.py {address} --onchain-source saved.py")
        ok = False
    elif onchain == local:
        print("\nRESULT: MATCH - the on-chain source is byte-for-byte the local file.")
    else:
        print("\nRESULT: MISMATCH - the deployed source is NOT the local file.")
        print(f"  local   sha256 {sha256(local)}")
        print(f"  onchain sha256 {sha256(onchain)}")
        ok = False

    problems = static_preflight(local, "local")
    if onchain:
        problems += static_preflight(onchain, "on-chain")
    if problems:
        ok = False
        print("\npreflight problems:")
        for p in problems:
            print(" -", p)
    else:
        print("preflight: header, single contract class, constructor, @allow_storage - clean")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
