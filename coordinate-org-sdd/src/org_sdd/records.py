"""Strict control-record parsing and structure checks, without source reads.

Public API: parse_json(text) raises ValueError; validate_record(record, file)
returns diagnostics; validate_records(records, files=None) adds internal-link
checks; load_initiative(path) returns Dataset. Dataset.valid means structural
validity only. No method computes digests, readiness, or actor authority.
"""
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .diagnostics import Diagnostic, sorted_diagnostics

ID_RE = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
KINDS = ("initiative", "contract", "handoff", "approval", "evidence", "knowledge")
DIRECTORIES = {kind: kind + "s" for kind in ("contract", "handoff", "approval")}
DIRECTORIES.update(evidence="evidence", knowledge="knowledge")
GATES = ("scope", "contract", "requirements", "design", "tasks", "knowledge", "integration", "release", "resolution")
STAGES = ("planning", "execution", "local_complete")
REVIEW = ("unreviewed", "human_confirmed", "stale", "conflicted")


def parse_json(text):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def no_number(_):
        raise ValueError("Numbers are not supported in format 1.0")
    try:
        result = json.loads(text, object_pairs_hook=pairs, parse_constant=no_number,
                            parse_int=no_number, parse_float=no_number)
        def unicode_scalars(value):
            if isinstance(value, str):
                value.encode("utf-8", errors="strict")
            elif isinstance(value, dict):
                for key, child in value.items():
                    unicode_scalars(key)
                    unicode_scalars(child)
            elif isinstance(value, list):
                for child in value: unicode_scalars(child)
        unicode_scalars(result)
        return result
    except (ValueError, RecursionError) as exc:
        raise ValueError("Invalid strict JSON") from exc


def obj(**fields):
    return ("object", fields)


def arr(item, unique=None):
    return ("array", item, unique)


def enum(*values):
    return ("enum", values)


def nullable(item):
    return ("nullable", item)


OWNER = ("owner",)
RR = obj(initiative_id="id", record_id="id", digest="digest")
SR = obj(repository_id="id", path="path", revision=nullable("revision"), digest="digest",
         basis=enum("git", "snapshot"), note="text")
LOCATOR = ("locator",)
TARGET = ("target",)
PROVENANCE = obj(sources=arr(SR, "source"), observed_at="time", review_status=enum(*REVIEW), note="text")
DECISION = obj(id="id", question="text", owner_role="id", affected_ids=arr("id", "value"),
               affected_gates=arr(enum(*GATES), "value"), status=enum("unresolved", "resolved"),
               resolution=nullable("text"), evidence=arr(SR, "source"))
CHECK = obj(id="id", owner=OWNER, stage=enum("local_complete", "integration"),
            procedure="text", expected="text", required_sources=arr(SR, "source"), required_contracts=arr(RR, "record"))
POLICY = obj(role_assignments=arr(obj(role="id", actors=arr("id", "value")), "role"),
             gates=arr(obj(gate=enum(*GATES), required_roles=arr("id", "value")), "gate"),
             disclosure=obj(status=enum("unresolved", "resolved"), decision_id="id"))
COMMON = dict(format_version=enum("1.0"), kind=enum(*KINDS), id="id", initiative_id="id",
              owner=OWNER, status=enum("draft", "proposed", "approved", "superseded", "withdrawn"),
              provenance=PROVENANCE, illustrative="bool")
PAYLOADS = {
    "initiative": dict(purpose="text", scope="text", participants=arr(obj(repository_id="id", locator=LOCATOR, owner=OWNER), "repository_id"),
                       integration_owner=OWNER, rollout_owner=OWNER, rollback_owner=OWNER, policy=POLICY,
                       decisions=arr(DECISION, "id"), required_contracts=arr("id", "value"), required_handoffs=arr("id", "value"),
                       checks=arr(CHECK, "id"), integration_checks=arr("id", "value")),
    "contract": dict(category=enum("api", "event", "data", "nfr"), provider="id", consumers=arr("id", "value"),
                     definition_refs=arr(SR, "source"), display_version="text", baseline_digest=nullable("digest"),
                     acceptance_checks=arr("id", "value"), compatibility=obj(assessment=enum("unchanged", "compatible", "breaking", "unknown"),
                     rationale="text", evidence_ids=arr("id", "value"), resolution_ids=arr("id", "value"))),
    "handoff": dict(supplying_owner=OWNER, receiving_owner=OWNER, repository_id="id", scope="text", obligations=arr(RR, "record"),
                    local_artifacts=obj(requirements=nullable(SR), design=nullable(SR), tasks=nullable(SR)),
                    trace=arr(obj(obligation=RR, disposition=enum("implemented", "not_applicable", "unresolved"),
                                  requirements=arr("text", "value"), design_elements=arr("text", "value"), tasks=arr("text", "value"),
                                  resolution_ids=arr("id", "value")), "obligation"),
                    dependencies=arr(obj(id="id", consumer_stage=enum(*STAGES), producer_id="id",
                                         required_stage=enum("contract_approved", *STAGES, "integration", "release"),
                                         obligations=arr(RR, "record"), evidence_ids=arr("id", "value")), "id"),
                    acceptance_checks=arr("id", "value"), completion_evidence_ids=arr("id", "value"), knowledge_ids=arr("id", "value")),
    "approval": dict(actor="id", role="id", gate=enum(*GATES), decision=enum("approved", "rejected", "revoked"),
                     timestamp="time", target=TARGET, policy_digest="digest", **{"supersedes?": "id"}),
    "evidence": dict(check_id=nullable("id"), purpose=enum("verification", "compatibility", "resolution", "publication"),
                     outcome=enum("passed", "failed", "not_run"), procedure="text", timestamp="time", source_refs=arr(SR, "source"),
                     contract_refs=arr(RR, "record"), baseline_digests=arr("digest", "value"), attachments=arr(SR, "source")),
    "knowledge": dict(source_refs=arr(SR, "source"), contract_refs=arr(RR, "record"), affected_participants=arr("id", "value"),
                      freshness=enum("current", "stale", "conflicted", "unresolved"), stale_after=nullable("time"),
                      okf_refs=arr(SR, "source"), publication=obj(disposition=enum("not_required", "pending", "published"),
                      evidence_ids=arr("id", "value"), reason="text")),
}


def safe_path(value, locator=False):
    if locator and value == ".":
        return True
    return (isinstance(value, str) and bool(value) and not any(ord(c) < 32 or ord(c) == 127 for c in value)
            and not any(c in value for c in "\\:") and all(p not in ("", ".", "..") for p in value.split("/")))


def valid_time(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


class Validator:
    def __init__(self, file, record_id=None):
        self.file = file
        self.record_id = record_id if isinstance(record_id, str) and ID_RE.fullmatch(record_id) else None
        self.diagnostics = []

    def error(self, field, code="FORMAT_INVALID", message="Invalid field; consult the record contract"):
        self.diagnostics.append(Diagnostic(code, self.file, self.record_id, field, message))

    def check(self, value, schema, field):
        if isinstance(schema, str):
            valid = {"text": lambda: isinstance(value, str) and bool(value.strip()),
                     "id": lambda: isinstance(value, str) and bool(ID_RE.fullmatch(value)),
                     "digest": lambda: isinstance(value, str) and bool(DIGEST_RE.fullmatch(value)),
                     "revision": lambda: isinstance(value, str) and bool(re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value)),
                     "time": lambda: valid_time(value), "bool": lambda: type(value) is bool,
                     "path": lambda: safe_path(value)}[schema]()
            if not valid:
                self.error(field, "PATH_UNSAFE" if schema == "path" else "FORMAT_INVALID")
            return
        tag = schema[0]
        if tag == "nullable":
            if value is not None:
                self.check(value, schema[1], field)
        elif tag == "enum":
            if not isinstance(value, str) or value not in schema[1]:
                self.error(field, "VERSION_UNSUPPORTED" if field == "format_version" else "FORMAT_INVALID")
        elif tag == "object":
            if not isinstance(value, dict):
                self.error(field)
                return
            fields = schema[1]
            allowed = {key.rstrip("?") for key in fields}
            if set(value) - allowed:
                self.error(field, message="Unknown field(s); consult the record contract")
            for key, subschema in fields.items():
                name = key.rstrip("?")
                child = f"{field}.{name}" if field else name
                if name not in value:
                    if not key.endswith("?"):
                        self.error(child, message="Required field is missing")
                else:
                    self.check(value[name], subschema, child)
        elif tag == "array":
            if not isinstance(value, list):
                self.error(field)
                return
            seen = set()
            for i, item in enumerate(value):
                child = f"{field}[{i}]"
                self.check(item, schema[1], child)
                unique = schema[2]
                if unique:
                    ident = item
                    if isinstance(item, dict):
                        if unique == "record": ident = [item.get("initiative_id"), item.get("record_id")]
                        elif unique == "source": ident = [item.get("repository_id"), item.get("path"), item.get("revision")]
                        elif unique == "obligation":
                            ref = item.get("obligation", {})
                            ident = [ref.get("initiative_id"), ref.get("record_id")] if isinstance(ref, dict) else ref
                        else: ident = item.get(unique)
                    key = json.dumps(ident, sort_keys=True)
                    if key in seen: self.error(child, message="Repeated identity in array")
                    seen.add(key)
        elif tag == "owner":
            self.check(value, obj(unresolved="id") if isinstance(value, dict) and "unresolved" in value else obj(actor="id", role="id"), field)
        elif tag == "locator":
            local = isinstance(value, dict) and value.get("type") == "local"
            self.check(value, obj(type=enum("local"), root="text", path="text") if local else obj(type=enum("git"), url="text", path="text"), field)
            if isinstance(value, dict):
                if not safe_path(value.get("path"), True): self.error(field + ".path", "PATH_UNSAFE")
                if local:
                    root = value.get("root")
                    if not isinstance(root, str) or not (root.startswith("/") or re.match(r"[A-Za-z]:[\\/]", root)):
                        self.error(field + ".root", "PATH_UNSAFE")
                elif isinstance(value.get("url"), str):
                    from urllib.parse import urlsplit
                    try:
                        parsed = urlsplit(value["url"])
                        if parsed.username is not None or parsed.password is not None: self.error(field + ".url", "PATH_UNSAFE")
                    except ValueError: self.error(field + ".url")
        elif tag == "target":
            fields = dict(initiative_id="id", record_id="id", type=enum("record", "release_scope", "source"), digest="digest")
            if isinstance(value, dict) and value.get("type") == "source": fields["source"] = SR
            self.check(value, obj(**fields), field)


def walk(value, field=""):
    yield field, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{field}.{key}" if field else key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{field}[{index}]")


def validate_record(record, file="<record>"):
    validator = Validator(file, record.get("id") if isinstance(record, dict) else None)
    if not isinstance(record, dict) or record.get("kind") not in KINDS:
        validator.error("kind")
        return validator.diagnostics
    validator.check(record, obj(**COMMON, **PAYLOADS[record["kind"]]), "")
    if validator.diagnostics:
        return sorted_diagnostics(validator.diagnostics)
    for field, value in walk(record):
        if isinstance(value, dict) and set(value) == set(SR[1]):
            if (value["basis"] == "git") != (value["revision"] is not None): validator.error(field + ".revision")
    if record["kind"] == "initiative":
        for i, decision in enumerate(record["decisions"]):
            if (decision["status"] == "unresolved") != (decision["resolution"] is None): validator.error(f"decisions[{i}].resolution")
            if decision["status"] == "resolved" and not decision["evidence"]: validator.error(f"decisions[{i}].evidence")
    if record["kind"] == "evidence":
        if (record["purpose"] == "verification") != (record["check_id"] is not None): validator.error("check_id")
    if record["kind"] == "approval" and record["target"]["type"] == "source":
        if record["target"]["digest"] != record["target"]["source"]["digest"]: validator.error("target.digest")
    return sorted_diagnostics(validator.diagnostics)


def validate_records(records, files=None):
    files = files or ["<record>" for _ in records]
    if len(files) != len(records): raise ValueError("One file identifier is required per record")
    diagnostics = []
    for record, file in zip(records, files): diagnostics.extend(validate_record(record, file))
    if diagnostics: return sorted_diagnostics(diagnostics)
    index = {}
    for record, file in zip(records, files):
        if record["id"] in index: diagnostics.append(Diagnostic("ID_DUPLICATE", file, record["id"], "id", "Record ID must be unique"))
        index[record["id"]] = record
    initiatives = [r for r in records if r["kind"] == "initiative"]
    if len(initiatives) != 1:
        return sorted_diagnostics(diagnostics + [Diagnostic("FORMAT_INVALID", "initiative.json", None, "kind", "Exactly one initiative is required")])
    initiative = initiatives[0]
    repos = {p["repository_id"] for p in initiative["participants"]} | {"coordination"}
    decisions = {d["id"]: d for d in initiative["decisions"]}
    checks = {c["id"]: c for c in initiative["checks"]}
    for record, file in zip(records, files):
        v = Validator(file, record["id"])
        def link(identity, kind, field):
            target = index.get(identity)
            if target is None: v.error(field, "REFERENCE_UNRESOLVED", "Register the referenced record")
            elif kind and target["kind"] not in kind: v.error(field, message="Referenced record has the wrong kind")
        def ids(values, kind, field):
            for i, identity in enumerate(values): link(identity, kind, f"{field}[{i}]")
        def check_ids(values, field, stage=None):
            for i, identity in enumerate(values):
                if identity not in checks: v.error(f"{field}[{i}]", "REFERENCE_UNRESOLVED")
                elif stage and checks[identity]["stage"] != stage: v.error(f"{field}[{i}]")
        if record["initiative_id"] != initiative["id"]: v.error("initiative_id", "REFERENCE_UNRESOLVED")
        for field, value in walk(record):
            if not isinstance(value, dict): continue
            if set(value) == {"unresolved"} and value["unresolved"] not in decisions: v.error(field + ".unresolved", "REFERENCE_UNRESOLVED")
            if set(value) == set(SR[1]) and value["repository_id"] not in repos: v.error(field + ".repository_id", "REFERENCE_UNRESOLVED")
            if set(value) == set(RR[1]):
                if value["initiative_id"] != initiative["id"]: v.error(field + ".initiative_id", "REFERENCE_UNRESOLVED")
                link(value["record_id"], ("contract",), field)
        kind = record["kind"]
        if kind == "initiative":
            if "coordination" in {p["repository_id"] for p in record["participants"]}: v.error("participants", message="Reserved repository ID cannot be registered")
            ids(record["required_contracts"], ("contract",), "required_contracts")
            ids(record["required_handoffs"], ("handoff",), "required_handoffs")
            check_ids(record["integration_checks"], "integration_checks", "integration")
            decision = decisions.get(record["policy"]["disclosure"]["decision_id"])
            if decision is None: v.error("policy.disclosure.decision_id", "REFERENCE_UNRESOLVED")
            elif record["policy"]["disclosure"]["status"] == "resolved" and decision["status"] != "resolved": v.error("policy.disclosure.status")
            for i, decision in enumerate(record["decisions"]): ids(decision["affected_ids"], None, f"decisions[{i}].affected_ids")
        elif kind == "contract":
            for field, values in (("provider", [record["provider"]]), ("consumers", record["consumers"])):
                for identity in values:
                    if identity not in repos - {"coordination"}: v.error(field, "REFERENCE_UNRESOLVED")
            check_ids(record["acceptance_checks"], "acceptance_checks")
            ids(record["compatibility"]["evidence_ids"], ("evidence",), "compatibility.evidence_ids")
            ids(record["compatibility"]["resolution_ids"], ("evidence",), "compatibility.resolution_ids")
        elif kind == "handoff":
            if record["repository_id"] not in repos - {"coordination"}: v.error("repository_id", "REFERENCE_UNRESOLVED")
            check_ids(record["acceptance_checks"], "acceptance_checks", "local_complete")
            ids(record["completion_evidence_ids"], ("evidence",), "completion_evidence_ids")
            ids(record["knowledge_ids"], ("knowledge",), "knowledge_ids")
            for i, trace in enumerate(record["trace"]): ids(trace["resolution_ids"], ("evidence",), f"trace[{i}].resolution_ids")
            for i, dep in enumerate(record["dependencies"]):
                expected = "contract" if dep["required_stage"] == "contract_approved" else "handoff" if dep["required_stage"] in STAGES else "initiative"
                link(dep["producer_id"], (expected,), f"dependencies[{i}].producer_id")
                ids(dep["evidence_ids"], ("evidence",), f"dependencies[{i}].evidence_ids")
        elif kind == "approval":
            target = record["target"]
            expected = {"scope": "initiative", "contract": "contract", "requirements": "handoff", "design": "handoff", "tasks": "handoff", "knowledge": "knowledge", "integration": "evidence", "release": "initiative", "resolution": "evidence"}[record["gate"]]
            link(target["record_id"], (expected,), "target.record_id")
            if target["initiative_id"] != initiative["id"]: v.error("target.initiative_id", "REFERENCE_UNRESOLVED")
            required_type = "source" if record["gate"] in ("requirements", "design", "tasks") else "release_scope" if record["gate"] == "release" else "record"
            if target["type"] != required_type: v.error("target.type")
            if "supersedes" in record:
                link(record["supersedes"], ("approval",), "supersedes")
                previous = index.get(record["supersedes"])
                if previous and previous["kind"] == "approval":
                    if any(record[key] != previous[key] for key in ("initiative_id", "actor", "role", "gate")) or any(target[key] != previous["target"][key] for key in ("initiative_id", "record_id", "type")):
                        v.error("supersedes", message="Supersession must retain actor, role, gate and target identity")
                seen, current = {record["id"]}, previous
                while current and current["kind"] == "approval":
                    if current["id"] in seen:
                        v.error("supersedes", message="Supersession cycle must be resolved")
                        break
                    seen.add(current["id"])
                    current = index.get(current.get("supersedes"))
        elif kind == "evidence":
            if record["check_id"] is not None: check_ids([record["check_id"]], "check_id")
        elif kind == "knowledge":
            for i, identity in enumerate(record["affected_participants"]):
                if identity not in repos - {"coordination"}: v.error(f"affected_participants[{i}]", "REFERENCE_UNRESOLVED")
            ids(record["publication"]["evidence_ids"], ("evidence",), "publication.evidence_ids")
        diagnostics.extend(v.diagnostics)
    return sorted_diagnostics(diagnostics)


@dataclass
class Dataset:
    root: Path
    records: dict
    files: dict
    diagnostics: list

    @property
    def valid(self): return not self.diagnostics

    @property
    def initiative(self): return next((r for r in self.records.values() if r["kind"] == "initiative"), None)


def load_initiative(path):
    """Read only contained control files; top-level I/O errors propagate as OSError."""
    root = Path(path).resolve(strict=True)
    if not root.is_dir(): raise NotADirectoryError("Initiative root must be a directory")
    paths = [(root / "initiative.json", "initiative")]
    for kind in KINDS[1:]:
        directory = root / DIRECTORIES[kind]
        if directory.exists():
            if not directory.resolve().is_relative_to(root):
                return Dataset(root, {}, {}, [Diagnostic("PATH_UNSAFE", DIRECTORIES[kind], None, "", "Control directory escapes initiative")])
            paths.extend((p, kind) for p in sorted(directory.glob("*.json")))
    records, files, diagnostics = [], [], []
    for path, kind in paths:
        relative = path.relative_to(root).as_posix()
        if not path.resolve().is_relative_to(root) or not path.is_file():
            if path == root / "initiative.json" and not path.exists(): raise FileNotFoundError("initiative.json is required")
            diagnostics.append(Diagnostic("PATH_UNSAFE", relative, None, "", "Control file must remain a regular contained file"))
            continue
        try: record = parse_json(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError):
            diagnostics.append(Diagnostic("FORMAT_INVALID", relative, None, "", "Invalid strict UTF-8 JSON"))
            continue
        errors = validate_record(record, relative)
        diagnostics.extend(errors)
        if errors: continue
        if record["kind"] != kind or (kind != "initiative" and path.stem != record["id"]):
            diagnostics.append(Diagnostic("FORMAT_INVALID", relative, record["id"], "id", "Kind/directory or ID/filename mismatch"))
        records.append(record)
        files.append(relative)
    diagnostics.extend(validate_records(records, files))
    return Dataset(root, {r["id"]: r for r in records}, {r["id"]: f for r, f in zip(records, files)}, sorted_diagnostics(diagnostics))
