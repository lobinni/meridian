"""glsim - a small GenVM stand-in, so the suites run with no Studio and no network.

What it gives a test:

  * a fake ``genlayer`` module (``gl``, ``Address``, ``u256``, ``DynArray``,
    ``TreeMap``) good enough to ``exec`` the contract source untouched;
  * a ``Chain`` to deploy the contract on, with a settable caller so every
    write can be attributed to an address, exactly like on chain;
  * a scripted model. ``gl.nondet.exec_prompt`` is routed to it, so a test
    decides what the LLM says - per prompt, per pass - without touching a
    real model;
  * a rigged wire. ``chain.rig_payload(...)`` / ``chain.rig_error(...)`` put
    a value on the consensus wire that ``leader_fn`` would never return,
    which is the only way to exercise the checks a validator runs against a
    peer it does not trust. A defence that cannot be exercised looks
    identical to one that is not there.

It is deliberately tiny. It is not a GenVM; it trusts the real network to be
weirder than it is. The opt-in integration suite exists for that.
"""

import json
import re
import sys
import types
import datetime
from dataclasses import dataclass


# --------------------------------------------------------------------------
# The fake genlayer module
# --------------------------------------------------------------------------


import typing


class UserError(Exception):
    """Raised by the contract on caller mistakes; the transaction rolls back."""


typing_any = typing.Any


class Result:
    pass


@dataclass
class Return(Result):
    calldata: typing_any = None


class Address(str):
    """A checksummed-address stand-in. Shape-checked by the contract itself
    (shaped_like_address); here it only needs to compare equal to itself."""

    def __new__(cls, v):
        return str.__new__(cls, str(v).strip())


def u256(x=0):
    return int(x)


class DynArray(list):
    def __class_getitem__(cls, _):
        return cls


class TreeMap(dict):
    def __class_getitem__(cls, _):
        return cls


class Allowable:
    pass


def allow_storage(cls):
    """The real decorator marks a dataclass as storage-eligible; the fake
    module only needs the name to exist so contracts load unchanged."""
    return cls


_UNSET = object()


def _zero_init_storage(instance):
    """Emulate GenVM zero-initialisation: annotated DynArray / TreeMap
    storage exists as empty collections BEFORE __init__ runs, and does not
    depend on __init__ doing anything at all."""
    for klass in reversed(type(instance).__mro__):
        for name, ann in getattr(klass, "__annotations__", {}).items():
            if ann is DynArray:
                setattr(instance, name, DynArray())
            elif ann is TreeMap:
                setattr(instance, name, TreeMap())


class _ContractBase:
    """Fallback for contract classes that define no __init__ of their own."""

    def __init__(self):
        _zero_init_storage(self)


def _passthrough(fn):
    fn.__is_gl_public__ = True
    return fn


class _Public:
    write = staticmethod(_passthrough)
    view = staticmethod(_passthrough)


class _Message:
    sender_address = Address("0x" + "00" * 20)


# The one live chain at a time. Prompts and consensus route through it.
_LIVE = None


def _exec_prompt(prompt, response_format=None):
    if _LIVE is None or _LIVE.model is None:
        raise RuntimeError("glsim: no model scripted on the live chain")
    return _LIVE._ask_model(prompt)


def _run_nondet_unsafe(leader_fn, validator_fn):
    chain = _LIVE
    leader_out = leader_fn()
    if chain is not None and chain._rig_error is not None:
        presented = chain._rig_error  # not a Return: the leader rolled back
    elif chain is not None and chain._rig_payload is not _UNSET:
        presented = Return(calldata=chain._rig_payload)  # a lying leader
    else:
        presented = Return(calldata=leader_out)
    if chain is not None:
        chain._rig_error = None
        chain._rig_payload = _UNSET
    ok = validator_fn(presented)
    if not ok:
        raise UserError("consensus: validators refused the leader's answer")
    if isinstance(presented, Return):
        return presented.calldata
    return leader_out


def _contract_interface(cls):
    return cls


def build_fake_genlayer():
    """A fresh `genlayer` module object, installed into sys.modules."""
    mod = types.ModuleType("genlayer")

    gl = types.SimpleNamespace()
    gl.Contract = _ContractBase
    gl.public = _Public
    gl.message = _Message()
    gl.message_raw = {"datetime": "2026-01-01T00:00:00Z"}
    gl.vm = types.SimpleNamespace(
        UserError=UserError,
        Result=Result,
        Return=Return,
        run_nondet_unsafe=_run_nondet_unsafe,
    )
    gl.nondet = types.SimpleNamespace(exec_prompt=_exec_prompt)
    gl.contract_interface = _contract_interface

    mod.gl = gl
    mod.Address = Address
    mod.u256 = u256
    mod.DynArray = DynArray
    mod.TreeMap = TreeMap
    mod.Allowable = Allowable
    mod.allow_storage = allow_storage
    mod.__all__ = [
        "gl",
        "Address",
        "u256",
        "DynArray",
        "TreeMap",
        "Allowable",
        "allow_storage",
    ]
    return mod


def load_module(path):
    """Exec a contract file against the fake module and return the module."""
    sys.modules["genlayer"] = build_fake_genlayer()
    with open(path, "r") as fh:
        src = fh.read()
    name = "contract_under_test_%d" % abs(hash(str(path)))
    g = {"__name__": name, "__file__": str(path)}
    exec(compile(src, str(path), "exec"), g)
    module = types.ModuleType(name)
    module.__dict__.update(g)
    return module


# --------------------------------------------------------------------------
# The chain
# --------------------------------------------------------------------------

CURATOR = Address("0x" + "aa" * 20)
OPERATOR = Address("0x" + "bb" * 20)
KEEPER = Address("0x" + "cc" * 20)
KEEPER2 = Address("0x" + "dd" * 20)
STRANGER = Address("0x" + "ee" * 20)


class Chain:
    """One contract instance on a pretend chain.

    tx() sets the caller and the clock, then invokes the method. UserError
    propagates like a revert: the suites assert on it.
    """

    def __init__(self, module, contract_name, deploy_args=()):
        global _LIVE
        self.module = module
        # The gl namespace THIS contract was executed against - there may be
        # several fake genlayer modules around, and only the one's own gl
        # carries its sender and clock.
        self.gl = module.__dict__["gl"]
        contract_cls = getattr(module, contract_name)
        # GenVM zero-initialises storage outside Python: it happens even
        # when the contract's own __init__ is a bare `pass`.
        self.contract = contract_cls.__new__(contract_cls)
        _zero_init_storage(self.contract)
        self.contract.__init__(*deploy_args)
        self.model = None
        self.prompts = []  # every prompt anybody ran, leader or validator
        self._rig_payload = _UNSET
        self._rig_error = None
        self._clock = 1_767_225_600  # 2026-01-01T00:00:00Z
        _LIVE = self

    # -- clock ---------------------------------------------------------
    def _tick(self):
        self._clock += 60
        iso = datetime.datetime.utcfromtimestamp(self._clock).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.gl.message_raw["datetime"] = iso

    def advance(self, seconds=3600):
        self._clock += seconds

    # -- prompting -------------------------------------------------------
    def _ask_model(self, prompt):
        self.prompts.append(prompt)
        return self.model(prompt)

    @property
    def prompt_count(self):
        return len(self.prompts)

    # -- transactions ------------------------------------------------------
    def tx(self, fn, *args, sender=CURATOR, **kwargs):
        global _LIVE
        _LIVE = self
        self.gl.message.sender_address = Address(sender)
        self._tick()
        return fn(*args, **kwargs)

    # -- rigs ---------------------------------------------------------------
    def rig_payload(self, payload):
        """Next consensus round: validators are handed THIS instead of the
        leader's real answer. If they accept it, it is what gets applied -
        a lying leader that won."""
        self._rig_payload = payload

    def rig_error(self, exc=None):
        """Next consensus round: the leader rolls back, so validators see
        something that is not a Return at all."""
        self._rig_error = exc if exc is not None else UserError("leader failed")


# --------------------------------------------------------------------------
# A model good enough to drive end-to-end runs
# --------------------------------------------------------------------------

_ROW = re.compile(r"\[(\d+)\]\s*(.*)")
_BLOCK = re.compile(r"<(\w+)>\n(.*?)\n</\1>", re.S)


def keyword_model(prompt):
    """Reads the <conditions> rows and the <filing> block, and raises a bit
    for a row when the filing contains the marker  proven(<first word of
    the condition>)  - case-insensitive. This is what ties a bit to the
    CONTENT of a condition rather than to its POSITION: the reversed pass
    renumbers the rows, and the marker still finds the same condition.
    because: deliberately varies run to run, so any test that compared it
    between nodes would fail - consensus must never touch it.
    """
    blocks = dict(_BLOCK.findall(prompt))
    conds = _ROW.findall(blocks.get("conditions", ""))
    filing = blocks.get("filing", "").lower()
    bits = []
    for _idx, text in conds:
        word = text.split()[0].lower() if text.split() else ""
        marker = "proven(%s)" % word
        bits.append("1" if marker in filing else "0")
    return {
        "mask": "|".join(bits),
        # Varies per call. Consensus never compares it, and no test should.
        "because": "call-%d marks here" % (hash(prompt) % 997),
    }
