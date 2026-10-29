"""Independent offline archive, source, descriptor, and owner-boundary replay."""

import copy
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
import types
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CANDIDATE = HERE.parents[2] / "deployment-preparation-r30"
PACKAGE = CANDIDATE / "tmp/761_deployment_preparation_r30/official-artifact-12880320744"
BUNDLE = "b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345"
SOURCE = "0bffe0c535e5897890aebf30879fdd3839dc52d6"
original_run = subprocess.run


def git_only(argv, *args, **kwargs):
    assert str(argv[0]) == "git", "Reviewer refuses any non-Git subprocess"
    return original_run(argv, *args, **kwargs)


subprocess.run = git_only


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


a = load(CANDIDATE / "deployment/cloud-reuse/r30-backend-artifact.py", "review_artifact")
proof = a.module("image-proof.py", a.PROOF_SHA)
verified = a.verify_bundle(PACKAGE, BUNDLE)
bundle = json.loads((PACKAGE / "backend-bundle-manifest.json").read_text())
manifest, contents = a.verify_source(PACKAGE, bundle["source_manifest_sha256"])
git_rows, git_contents = a.source_data(CANDIDATE)[1:3]
assert manifest["files"] == git_rows and contents == git_contents
assert len(git_rows) == 62
graph = proof.scan_archive(PACKAGE / "backend-image.tar.gz")
trusted = proof.trusted_role(graph, "backend", bundle["declared"], manifest)
assert trusted["config_id"] == "sha256:8e3e2a9d1f2d4706072eb0502b041d3db49d32b7a2fc48ac6b39fc2162336845"
assert trusted["labels"]["io.t44.r30.source-manifest-sha256"] == bundle["source_manifest_sha256"]
assert trusted["labels"]["io.t44.r30.run"] == bundle["run_id"]
assert len(trusted["diff_ids"]) == 11
assert len(bundle["official_python"]["diff_ids"]) == 4
assert trusted["diff_ids"][:4] == bundle["official_python"]["diff_ids"]
actual = dict(Os="linux", Architecture="amd64", Variant=trusted["variant"],
              RootFS=dict(Type="layers", Layers=trusted["diff_ids"]),
              Config=dict(Labels=trusted["labels"]), Id=trusted["config_id"])
classic = proof.prove_role(graph, "backend", bundle["declared"], manifest, actual)
descriptor = next(row for row in graph["names"].values() if isinstance(row["json"], dict)
                  and row["json"].get("mediaType") == "application/vnd.oci.image.manifest.v1+json")
oci_actual = copy.deepcopy(actual)
oci_actual.update(Id=descriptor["digest"], Descriptor=dict(mediaType=descriptor["json"]["mediaType"], digest=descriptor["digest"], size=descriptor["bytes"]))
oci = proof.prove_role(graph, "backend", bundle["declared"], manifest, oci_actual)
refusals = []
for name in ["descriptor-size", "labels", "layer-order"]:
    altered = copy.deepcopy(oci_actual)
    if name == "descriptor-size":
        altered["Descriptor"]["size"] += 1
    elif name == "labels":
        altered["Config"]["Labels"]["org.opencontainers.image.revision"] = "0" * 40
    else:
        altered["RootFS"]["Layers"] = list(reversed(altered["RootFS"]["Layers"]))
    try:
        proof.prove_role(graph, "backend", bundle["declared"], manifest, altered)
    except ValueError as error:
        refusals.append(dict(mutation=name, error=str(error)))
    else:
        raise AssertionError("Malformed identity accepted: " + name)

# Replay application filesystem from original ordered layers, without extraction or execution.
table = graph["names"]["manifest.json"]["json"][0]
deltas = {}
with tarfile.open(PACKAGE / "backend-image.tar.gz", "r|*") as outer:
    for entry in outer:
        if entry.name not in table["Layers"]:
            continue
        changes = []
        with tarfile.open(fileobj=outer.extractfile(entry), mode="r|*") as layer:
            for item in layer:
                name = item.name.removeprefix("./").lstrip("/")
                if not name.startswith("app/"):
                    continue
                path = name[4:]
                if not path.startswith(("backend/", "specs/database/", "specs/contracts/", "deployment/")):
                    continue
                if Path(path).name.startswith(".wh."):
                    changes.append(("whiteout", path, None))
                elif item.isfile():
                    raw = layer.extractfile(item).read()
                    changes.append(("file", path, dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), mode=item.mode & 0o777)))
                elif not item.isdir():
                    raise AssertionError("Application source symlink/special file: " + path)
        deltas[entry.name] = changes
runtime = {}
for layer in table["Layers"]:
    for action, path, value in deltas[layer]:
        if action == "file":
            runtime[path] = value
        else:
            parent = Path(path).parent.as_posix()
            target = path.replace(".wh.", "", 1)
            for existing in list(runtime):
                if (Path(path).name == ".wh..wh..opq" and existing.startswith(parent + "/")) or existing == target or existing.startswith(target + "/"):
                    runtime.pop(existing)
expected = [row for row in git_rows if row["path"] not in a.RUNTIME_EXCLUDED]
assert sorted(runtime.values(), key=lambda row: row["path"]) == expected
runtime_record = json.loads((PACKAGE / "actual-runtime-files.json").read_text())
assert runtime_record == dict(uid=10001, files=expected)

# Replay owner's exact assertions; only ROOT/PACKAGE and temporary-output location are adapted.
suite = unittest.TestSuite()
adapted = []
for filename in ["test_r30_artifact.py", "test_r30_window.py"]:
    path = CANDIDATE / "tmp/761_deployment_preparation_r30" / filename
    source = path.read_text()
    before = "ROOT = Path(__file__).resolve().parents[2]"
    assert source.count(before) == 1
    source = source.replace(before, "ROOT = Path(" + repr(str(CANDIDATE)) + ")")
    module = types.ModuleType("review_" + path.stem)
    module.__file__ = str(HERE / filename)
    exec(compile(source, str(path), "exec"), module.__dict__)
    if filename == "test_r30_window.py":
        module.PACKAGE = PACKAGE
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    adapted.append(dict(path=str(path.relative_to(CANDIDATE)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), adaptation="ROOT read path; PACKAGE allowed official artifact; __file__ scratch redirects temporary writes only"))
with (HERE / "owner-boundaries-replay.log").open("w") as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
assert result.wasSuccessful() and result.testsRun == 20
record = dict(source=SOURCE, bundle_manifest=BUNDLE, verified_bundle=verified,
              exact_git_context=62, exact_runtime_from_ordered_layers=len(runtime),
              runtime_report_nonroot_uid=runtime_record["uid"], ordered_layers=11,
              official_python_ordered_prefix_layers=4, config_id=trusted["config_id"],
              offline_classic_identity=classic, offline_oci_descriptor_identity=oci,
              altered_identities_refused=refusals, owner_boundary_replay=dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), adapted_test_paths=adapted),
              container_or_service_or_cloud_or_session_calls=False,
              limits="Synthetic inspect projections verify descriptor branches against real archive bytes; not actual Docker29 load, cache, or a new nonroot runtime execution")
(HERE / "artifact-review.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record))
