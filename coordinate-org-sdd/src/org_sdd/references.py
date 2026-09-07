"""Identity helpers and explicit local source resolution; never network or writes.

Public helpers: canonical_bytes, byte_digest, record_digest, policy_digest,
record_ref, release_projection (caller supplies already selected evidence),
validate_context, validate_repo_map, and SourceResolver.resolve -> Resolution.
ReferenceFailure carries a safe Diagnostic for helper failures. Selection of
effective approvals/checks/release readiness belongs to downstream evaluators.
"""
import hashlib
import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .diagnostics import Diagnostic
from .records import (ID_RE, LOCATOR, RR, SR, Validator, arr, enum, obj,
                      parse_json, safe_path, validate_record)


class ReferenceFailure(ValueError):
    def __init__(self, code, field="", message="Reference could not be verified", file="<reference>", record_id=None):
        self.diagnostic = Diagnostic(code, file, record_id, field, message)
        super().__init__(message)


def canonical_bytes(value):
    """Exact format-1.0 canonical JSON; validate scalars even for direct callers."""
    try:
        def scalars(item):
            if item is None or type(item) is bool: return
            if isinstance(item, str): item.encode("utf-8"); return
            if isinstance(item, list):
                for child in item: scalars(child)
                return
            if isinstance(item, dict):
                for key, child in item.items():
                    if not isinstance(key, str): raise ValueError("Invalid key")
                    scalars(key); scalars(child)
                return
            raise ValueError("Unsupported scalar")
        scalars(value)
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, RecursionError) as exc:
        raise ReferenceFailure("FORMAT_INVALID", message="Cannot canonicalize malformed format-1.0 JSON") from exc


def byte_digest(content):
    if not isinstance(content, bytes): raise TypeError("byte_digest requires bytes")
    return "sha256:" + hashlib.sha256(content).hexdigest()


def record_digest(record):
    errors = validate_record(record)
    if errors: raise ReferenceFailure(errors[0].code, errors[0].field, "Cannot hash an invalid control record")
    return byte_digest(canonical_bytes(record))


def policy_digest(initiative):
    if validate_record(initiative) or initiative.get("kind") != "initiative":
        raise ReferenceFailure("FORMAT_INVALID", "policy", "A valid initiative is required")
    return byte_digest(canonical_bytes({"policy": initiative["policy"], "decisions": initiative["decisions"]}))


def record_ref(record):
    return dict(initiative_id=record["initiative_id"], record_id=record["id"], digest=record_digest(record))


def release_projection(initiative, contracts, handoffs, evidence, knowledge):
    """Pure projection over explicit record selections, never auto-select approval.

    Enforces kinds/identity sets. Caller must establish complete check/evidence
    selection and readiness separately before presenting an eligible scope.
    """
    if initiative.get("kind") != "initiative": raise ReferenceFailure("FORMAT_INVALID", "initiative")
    result = {"initiative": record_ref(initiative)}
    for label, kind, records in (("contracts", "contract", contracts), ("handoffs", "handoff", handoffs),
                                 ("evidence", "evidence", evidence), ("knowledge", "knowledge", knowledge)):
        refs = {}
        for record in records:
            if record.get("kind") != kind or record.get("initiative_id") != initiative["id"]:
                raise ReferenceFailure("FORMAT_INVALID", label, "Release selection has wrong kind or initiative")
            ref = record_ref(record)
            key = (ref["initiative_id"], ref["record_id"])
            if key in refs and refs[key] != ref: raise ReferenceFailure("DIGEST_MISMATCH", label, "Conflicting release selection identity")
            refs[key] = ref
        result[label] = [refs[key] for key in sorted(refs)]
    for field in ("contracts", "handoffs"):
        if {r["record_id"] for r in result[field]} != set(initiative["required_" + field]):
            raise ReferenceFailure("REFERENCE_UNRESOLVED", field, "Release selection must cover exactly required records")
    return result


def validate_context(context, file=".sdd/org/context.json"):
    v = Validator(file)
    v.check(context, obj(format_version=enum("1.0"), initiative_id="id", repository_id="id", coordination=LOCATOR,
                         initiative_digest="digest", handoff_ids=arr("id", "value")), "")
    return v.diagnostics


def validate_repo_map(mapping, registered_ids, coordination_root, file="<repo-map>"):
    """Return diagnostics without opening sources; roots must exist on this host."""
    v = Validator(file)
    if not isinstance(mapping, dict) or set(mapping) != {"format_version", "repositories"}:
        v.error("", message="Repo map requires format_version and repositories")
        return v.diagnostics
    v.check(mapping["format_version"], enum("1.0"), "format_version")
    repositories = mapping["repositories"]
    if not isinstance(repositories, dict):
        v.error("repositories"); return v.diagnostics
    for index, (identity, entry) in enumerate(repositories.items()):
        field = f"repositories[{index}]"
        if not isinstance(identity, str) or not ID_RE.fullmatch(identity) or identity not in set(registered_ids) | {"coordination"}:
            v.error(field, "REFERENCE_UNRESOLVED", "Repo-map key must be registered")
        before = len(v.diagnostics)
        v.check(entry, obj(root="text", basis=enum("git", "snapshot")), field)
        if len(v.diagnostics) != before: continue
        path = Path(entry["root"])
        if not path.is_absolute() or any(ord(c) < 32 or ord(c) == 127 for c in entry["root"]):
            v.error(field + ".root", "PATH_UNSAFE", "Supply an explicit absolute local directory")
            continue
        try:
            resolved = path.resolve(strict=True)
            if not resolved.is_dir(): raise OSError("Not a directory")
            if identity == "coordination" and resolved != Path(coordination_root).resolve(strict=True):
                v.error(field + ".root", "PATH_UNSAFE", "Coordination mapping cannot override selected workspace")
        except (OSError, ValueError, RuntimeError): v.error(field + ".root", "REFERENCE_UNRESOLVED", "Mapped root is unavailable")
    return v.diagnostics


@dataclass
class Resolution:
    content: object
    source: dict
    diagnostics: list

    @property
    def valid(self): return not self.diagnostics

    @property
    def baseline(self):
        return {key: self.source.get(key) for key in ("repository_id", "path", "basis", "revision", "digest")}


class SourceResolver:
    def __init__(self, mapping, registered_ids, coordination_root, timeout=10):
        errors = validate_repo_map(mapping, registered_ids, coordination_root)
        if errors: raise ReferenceFailure(errors[0].code, errors[0].field, errors[0].message, errors[0].file)
        self.roots = {key: (Path(value["root"]).resolve(strict=True), value["basis"]) for key, value in mapping["repositories"].items()}
        self.registered_ids = set(registered_ids) | {"coordination"}
        self.timeout = timeout

    def _git(self, root, *args):
        # No ambient repository, alternate object store, replacement objects,
        # prompt, filters, hook, pager or lazy network fetch can redirect reads.
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                           GIT_TERMINAL_PROMPT="0", GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1",
                           GIT_OPTIONAL_LOCKS="0", GIT_PAGER="cat")
        try:
            result = subprocess.run(["git", "--no-pager", "-c", "core.hooksPath=" + os.devnull,
                                     "-c", "core.fsmonitor=false", "-C", str(root), *args],
                                    shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=self.timeout, env=environment, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ReferenceFailure("REFERENCE_UNRESOLVED", message="Bounded local Git read unavailable") from exc
        if result.returncode:
            raise ReferenceFailure("REFERENCE_UNRESOLVED", message="Pinned local Git object unavailable")
        return result.stdout

    def _git_source(self, root, source):
        # Confirm mapped root is the checkout root, not a subdirectory silently
        # discovering a different repository in a parent directory.
        top = self._git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()
        if Path(top).resolve() != root: raise ReferenceFailure("PATH_UNSAFE", message="Git map must identify its checkout root")
        object_dir = self._git(root, "rev-parse", "--git-path", "objects").decode("utf-8").strip()
        object_path = Path(object_dir)
        if not object_path.is_absolute(): object_path = root / object_path
        if (object_path / "info" / "alternates").exists():
            raise ReferenceFailure("PATH_UNSAFE", message="External Git object alternates are not authorized")
        if any((object_path / "pack").glob("*.promisor")):
            raise ReferenceFailure("REFERENCE_UNRESOLVED", message="Partial-clone object stores require a complete authorized local snapshot")
        revision = source["revision"]
        if self._git(root, "cat-file", "-t", revision).strip() != b"commit":
            raise ReferenceFailure("FORMAT_INVALID", "revision", "Pinned Git object must be a commit")
        tree = self._git(root, "ls-tree", "-z", "--full-tree", revision, "--", source["path"])
        entries = [entry for entry in tree.split(b"\0") if entry]
        exact = []
        for entry in entries:
            header, path = entry.split(b"\t", 1)
            if path == source["path"].encode("utf-8"): exact.append(header.split())
        if len(exact) != 1: raise ReferenceFailure("REFERENCE_UNRESOLVED", "path", "Pinned Git file unavailable")
        mode, kind, object_id = exact[0]
        if mode not in (b"100644", b"100755") or kind != b"blob":
            raise ReferenceFailure("PATH_UNSAFE", "path", "Git source must be a regular blob, not link/tree/submodule")
        return self._git(root, "cat-file", "blob", object_id.decode("ascii"))

    def _snapshot(self, root, path):
        try:
            candidate = (root / path).resolve(strict=True)
            if not candidate.is_relative_to(root): raise ReferenceFailure("PATH_UNSAFE", "path", "Source escapes mapped root")
            if not candidate.is_file(): raise ReferenceFailure("PATH_UNSAFE", "path", "Source must be a regular file")
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
            descriptor = os.open(candidate, flags)
            with os.fdopen(descriptor, "rb") as handle:
                if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode): raise ReferenceFailure("PATH_UNSAFE", "path", "Source must remain a regular file")
                return handle.read()
        except ReferenceFailure: raise
        except (OSError, ValueError, RuntimeError) as exc:
            raise ReferenceFailure("REFERENCE_UNRESOLVED", "path", "Authorized snapshot unavailable") from exc

    def resolve(self, source, file="<source>", record_id=None, field="source"):
        v = Validator(file, record_id)
        v.check(source, SR, field)
        if not v.diagnostics and (source["basis"] == "git") != (source["revision"] is not None): v.error(field + ".revision")
        if v.diagnostics: return Resolution(None, source if isinstance(source, dict) else {}, v.diagnostics)
        try:
            if source["repository_id"] not in self.registered_ids or source["repository_id"] not in self.roots:
                raise ReferenceFailure("REFERENCE_UNRESOLVED", "repository_id", "Supply an authorized mapping for this source")
            root, basis = self.roots[source["repository_id"]]
            if source["basis"] == "git":
                if basis != "git": raise ReferenceFailure("REFERENCE_UNRESOLVED", "basis", "Snapshot mapping cannot verify Git identity")
                content = self._git_source(root, source)
            else: content = self._snapshot(root, source["path"])
            if byte_digest(content) != source["digest"]: raise ReferenceFailure("DIGEST_MISMATCH", "digest", "Source bytes differ from declared baseline")
            return Resolution(content, source, [])
        except (UnicodeError, ValueError) as exc:
            if isinstance(exc, ReferenceFailure): failure = exc
            else: failure = ReferenceFailure("FORMAT_INVALID", message="Source identity could not be decoded")
            d = failure.diagnostic
            return Resolution(None, source, [Diagnostic(d.code, file, v.record_id, field + ("." + d.field if d.field else ""), d.message)])
