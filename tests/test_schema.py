"""Studio-schema preflight, offline.

"Could not load contract schema" in GenLayer Studio is not one error; it is
a family of them, and on the network they all report the same way: nothing
deploys and the methods panel is empty. Every cause has an offline witness,
so this suite turns each one into an assertion that fails BEFORE deploy:

  * the runner header on line 1, parseable, with a Depends pin;
  * exactly one gl.Contract subclass;
  * every public entrypoint fully annotated, with schema-legal types only;
  * storage fields declared on the class body, schema-legal, fully
    specialized (no bare TreeMap, no int, no list/dict builtins);
  * every storage dataclass decorated @allow_storage @dataclass, with no
    collection fields inside;
  * no sender_address in __init__ (breaks deployment on Studio);
  * no stdlib imports beyond what GenVM ships.

If this file passes and Studio still refuses, the problem is the network,
not the contract.
"""

import ast
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

ROOT = pathlib.Path(__file__).parent.parent
CONTRACT_PATH = ROOT / "contracts" / "meridian.py"
SOURCE = CONTRACT_PATH.read_text()
TREE = ast.parse(SOURCE, filename=str(CONTRACT_PATH))

# Types the Studio schema generator can serialize into an ABI.
PARAM_TYPES = {"str", "bool", "u8", "u16", "u32", "u64", "u128", "u256",
               "i8", "i16", "i32", "i64", "i128", "i256", "bigint", "Address",
               "bytes"}
RETURN_TYPES = PARAM_TYPES | {"None", "dict"}
STORAGE_SCALARS = {"str", "bool", "Address", "bytes", "bigint"} | {
    t for t in PARAM_TYPES if t[0] in "ui" and t[1:].isdigit()
}
ALLOWED_IMPORTS = {"genlayer", "dataclasses", "json", "datetime", "typing", "math"}


def _name(ann):
    """The bare name of an annotation node, or a description for generics."""
    if isinstance(ann, ast.Name):
        return ann.id
    if isinstance(ann, ast.Attribute):
        return ann.attr  # e.g. gl.vm.Result inside closures
    if isinstance(ann, ast.Constant):
        return str(ann.value)
    if isinstance(ann, ast.Subscript):
        return _name(ann.value)  # TreeMap[str, u256] -> "TreeMap"
    return type(ann).__name__


def _contract_class():
    classes = []
    for node in TREE.body:
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Attribute) and base.attr == "Contract":
                    classes.append(node)
    return classes


def _decorator_names(node):
    names = []
    for d in node.decorator_list:
        if isinstance(d, ast.Name):
            names.append(d.id)
        elif isinstance(d, ast.Attribute):
            names.append(d.attr)
        elif isinstance(d, ast.Call):
            f = d.func
            names.append(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "?"))
    return names


def _public_methods(contract):
    out = []
    for node in contract.body:
        if isinstance(node, ast.FunctionDef):
            decs = _decorator_names(node)
            if "write" in decs or "view" in decs:
                out.append(("write" if "write" in decs else "view", node))
    return out


# ---------------------------------------------------------------------------
# The header Studio reads before it will read anything else
# ---------------------------------------------------------------------------


def test_runner_header_is_line_one_and_parseable():
    first = SOURCE.splitlines()[0]
    assert first.startswith("#"), "line 1 must be the runner comment"
    payload = json.loads(first.lstrip("#").strip())
    assert "Depends" in payload
    assert payload["Depends"].startswith("py-genlayer:"), "pin the py-genlayer runner"
    # Nothing executes before the header either.
    assert SOURCE[0] == "#", "the header must be the very first byte"


# ---------------------------------------------------------------------------
# The single contract class
# ---------------------------------------------------------------------------


def test_exactly_one_contract_class():
    classes = _contract_class()
    assert len(classes) == 1, "Studio's schema maps one file to one contract class"
    assert classes[0].name == "Meridian"


# ---------------------------------------------------------------------------
# Public entrypoints: fully annotated, schema-legal
# ---------------------------------------------------------------------------


def test_every_public_method_is_fully_annotated():
    (contract,) = _contract_class()
    offenders = []
    for _kind, fn in _public_methods(contract):
        args = [a for a in fn.args.args if a.arg != "self"]
        for a in args:
            if a.annotation is None:
                offenders.append(f"{fn.name}: parameter {a.arg} has no annotation")
            elif _name(a.annotation) not in PARAM_TYPES:
                offenders.append(
                    f"{fn.name}: parameter {a.arg}: {_name(a.annotation)} is not ABI-legal"
                )
        if fn.returns is None:
            offenders.append(f"{fn.name}: missing a return annotation")
    assert offenders == [], "\n".join(offenders)


def test_public_return_types_are_schema_legal():
    (contract,) = _contract_class()
    for kind, fn in _public_methods(contract):
        if fn.returns is None:
            continue  # covered above
        ret = _name(fn.returns)
        assert ret in RETURN_TYPES, f"{kind} {fn.name} -> {ret} is not ABI-legal"
        assert ret != "Any", "typing.Any cannot reach the schema"


def test_every_public_method_returns_exactly_legal_leaf_types():
    """Views here return dict; the leaves must be calldata-safe. This is a
    source-level reminder more than a proof: the runbook asserts the shapes."""
    (contract,) = _contract_class()
    for _kind, fn in _public_methods(contract):
        src = ast.get_source_segment(SOURCE, fn)
        assert "typing.Any" not in src, f"typing.Any leaked into {fn.name}"


# ---------------------------------------------------------------------------
# Storage: class-body declared, legal, fully specialized
# ---------------------------------------------------------------------------


def _storage_annotations():
    (contract,) = _contract_class()
    out = {}
    for node in contract.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out[node.target.id] = node.annotation
    return out


def test_storage_fields_are_schema_legal():
    storage = _storage_annotations()
    assert len(storage) >= 1
    dataclasses = {
        n.name
        for n in TREE.body
        if isinstance(n, ast.ClassDef) and "dataclass" in _decorator_names(n)
    }
    for field, ann in storage.items():
        root = _name(ann)
        assert root not in {"int", "float", "list", "dict"}, (
            f"storage field {field}: {root} is forbidden - use sized ints / DynArray / TreeMap"
        )
        if root in ("DynArray", "TreeMap"):
            assert isinstance(ann, ast.Subscript), (
                f"storage field {field}: bare {root} is not allowed - specialize it"
            )
            inner = _name(ann.slice)
            assert (
                inner in STORAGE_SCALARS or inner in dataclasses or root == "TreeMap"
            ), f"storage field {field}: unsupported element type {inner}"
        else:
            assert root in STORAGE_SCALARS or root in dataclasses, (
                f"storage field {field}: unsupported type {root}"
            )


def test_no_instance_only_state():
    """self.x = ... for an undeclared x is silently discarded between calls;
    the suite refuses any assignment to a field the class never declared."""
    (contract,) = _contract_class()
    declared = set(_storage_annotations())
    leaks = []
    for node in ast.walk(contract):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if (
                    isinstance(t, ast.Attribute)
                    and isinstance(t.value, ast.Name)
                    and t.value.id == "self"
                    and t.attr not in declared
                ):
                    leaks.append(t.attr)
                # nested attributes like self.gates[i].x are storage rows, fine
    assert leaks == [], f"undeclared instance state: {leaks}"


# ---------------------------------------------------------------------------
# Storage dataclasses
# ---------------------------------------------------------------------------


def test_every_storage_dataclass_carries_allow_storage():
    rows = [n for n in TREE.body if isinstance(n, ast.ClassDef)]
    storage_used = set()
    for ann in _storage_annotations().values():
        if isinstance(ann, ast.Subscript):
            storage_used.add(_name(ann.slice))
    missing = []
    for cls in rows:
        if cls.name not in storage_used:
            continue
        decs = _decorator_names(cls)
        if "allow_storage" not in decs or "dataclass" not in decs:
            missing.append(cls.name)
    assert missing == [], (
        "storage dataclasses without @allow_storage + @dataclass are refused "
        f"at schema time: {missing}"
    )


def test_no_collection_inside_a_storage_dataclass():
    """GenVM forbids DynArray/TreeMap fields inside a stored dataclass; this
    contract uses flat linked rows instead - keep it that way."""
    for cls in TREE.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        if "dataclass" not in _decorator_names(cls):
            continue
        for node in cls.body:
            if isinstance(node, ast.AnnAssign):
                assert _name(node.annotation) not in {"DynArray", "TreeMap", "list", "dict"}, (
                    f"{cls.name}.{getattr(node.target, 'id', '?')}: a collection field "
                    "inside a storage dataclass is forbidden"
                )


# ---------------------------------------------------------------------------
# Deploy-time traps with offline witnesses
# ---------------------------------------------------------------------------


def test_schema_generator_needs_a_ctor():
    """Regression for a real deploy failure:

        TypeError: ('__init__ is absent', <class 'contract.Meridian'>)

    GenVM's get_schema() calls _get_ctor() unconditionally: a contract class
    with no __init__ at all cannot produce a schema, on any network."""
    (contract,) = _contract_class()
    ctor = None
    for node in contract.body:
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            ctor = node
    assert ctor is not None, (
        "__init__ must exist - GenVM's schema generator raises "
        "TypeError('__init__ is absent') without one"
    )
    params = [a for a in ctor.args.args if a.arg != "self"]
    for a in params:
        assert a.annotation is not None, f"ctor parameter {a.arg} must be annotated"
        assert _name(a.annotation) in PARAM_TYPES, (
            f"ctor parameter {a.arg}: {_name(a.annotation)} is not ABI-legal"
        )


def test_no_sender_address_in_init():
    (contract,) = _contract_class()
    for node in contract.body:
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            # AST nodes only, not the raw segment: the constructor's own
            # comments may TALK about sender_address (this one does); what
            # must never appear is a real attribute access.
            for sub in ast.walk(node):
                assert not (
                    isinstance(sub, ast.Attribute) and sub.attr == "sender_address"
                ), (
                    "sender_address inside __init__ fails at deployment on Studio - "
                    "take the address as a constructor parameter instead"
                )


def test_only_genvm_shipped_imports():
    for node in TREE.body:
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] in ALLOWED_IMPORTS, f"unexpected import {a.name}"
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "") in ALLOWED_IMPORTS, f"unexpected import from {node.module}"


def test_every_gl_attribute_used_exists_in_the_shim():
    """If a new genlayer primitive appears in the source, glsim must learn it
    too - otherwise the real network and the offline suite drift apart."""
    import glsim

    fake = glsim.build_fake_genlayer()

    # gl.<name> used anywhere in the source
    top = set()
    for node in ast.walk(TREE):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "gl":
            top.add(node.attr)
    missing = {a for a in top if not hasattr(fake.gl, a)}
    assert missing == set(), f"gl.* un-shimmed in glsim: {missing}"

    # gl.<namespace>.<name> one level deeper (vm / nondet / public / message ...)
    for ns in sorted(top):
        holder = getattr(fake.gl, ns, None)
        sub = set()
        for node in ast.walk(TREE):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "gl"
                and node.value.attr == ns
            ):
                sub.add(node.attr)
        missing = {a for a in sub if not hasattr(holder, a)}
        assert missing == set(), f"gl.{ns}.* un-shimmed in glsim: {missing}"
