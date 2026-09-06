"""Local regression tests: actual API/orchestration, synthetic provider output."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from app import v2_routes
from app.contracts import Pathway, Scenario, StrokeResult, TruthPacket, utcnow
from app.services.claude_runtime import ClaudeRuntimeService
from app.services.orchestrator import GanymedeOrchestrator, parse_triage_hit_list, TRANSLATION_REGISTERS
from app.services.session import Session, SessionRegistry, SessionCancelledError
from app.services.session_store import SessionStore
from app.services.substrate import ClaudeCliRunner, SubstrateResult, assemble_corpus


async def until(predicate, timeout=5):
    async def wait():
        while not predicate():
            await asyncio.sleep(0.01)
    await asyncio.wait_for(wait(), timeout)


PACKETS = [{"subject": "fixture", "content": "Synthetic evidence only"}]


class AuditAPITests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ganymede-regression-")
        self.addCleanup(self.directory.cleanup)
        self.env = patch.dict(os.environ, {
            "GANYMEDE_DATA_DIR": self.directory.name,
            "GANYMEDE_DISABLE_SESSION_PERSISTENCE": "1",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.runtime = ClaudeRuntimeService()
        self.orchestrator = GanymedeOrchestrator(self.runtime)
        self.registry = SessionRegistry()
        self.app = FastAPI()
        self.app.include_router(v2_routes.router)
        self.calls = []
        self.block_role = None
        self.gate = asyncio.Event()
        self.subject_count = 1
        self.dispatch_payload = None
        self.bridge_fails = False

        async def invoke(runner, *, prompt, system_file, tools=None):
            role = "research" if tools else Path(system_file).name.split("-")[0]
            if "<HIT_LIST_JSON>" in prompt:
                role = "triage"
            self.calls.append((role, prompt))
            if role == self.block_role:
                await self.gate.wait()
            if role == "dispatcher":
                text = json.dumps(self.dispatch_payload)
            elif role == "triage":
                text = "<HIT_LIST_JSON>" + json.dumps({"subjects": [
                    {"name": f"fixture{i}", "surgical_prompt": f"query {i}"}
                    for i in range(self.subject_count)
                ]}) + "</HIT_LIST_JSON>"
            elif role == "research":
                text = "Synthetic packet https://example.invalid/fixture"
            elif role == "bridge":
                if self.bridge_fails:
                    raise RuntimeError("Synthetic bridge failure")
                text = "BRIDGE CRITIQUE"
            elif role == "auditor":
                text = "AUDITOR CRITIQUE"
            else:
                text = "SYNTHESIS ANSWER"
            return SubstrateResult(text=text)

        for mock in (
            patch.object(v2_routes, "_orchestrator", return_value=self.orchestrator),
            patch.object(v2_routes, "registry", return_value=self.registry),
            patch.object(ClaudeCliRunner, "invoke", new=invoke),
        ):
            mock.start()
            self.addCleanup(mock.stop)

    async def asyncTearDown(self):
        for session in self.registry.list_all():
            await session.request_cancel("Test cleanup")
        await self.runtime.close()

    async def http(self, method, path, body=None):
        sent = []
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": method, "scheme": "http", "path": path,
            "raw_path": path.encode(), "query_string": b"",
            "headers": [(b"content-type", b"application/json")],
            "client": ("127.0.0.1", 12345), "server": ("127.0.0.1", 8000),
        }
        async def receive():
            return {"type": "http.request", "body": json.dumps(body).encode(), "more_body": False}
        async def send(message):
            sent.append(message)
        await self.app(scope, receive, send)
        status = next(m["status"] for m in sent if m["type"] == "http.response.start")
        raw = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
        return status, json.loads(raw)

    async def create(self, pathway="cleanroom", iterative=False, slots=1):
        scenarios = {
            "cleanroom": {"question": "Synthetic question"},
            "genie": {"current_state": "Fixture now", "wished_for_state": "Fixture goal"},
            "offensive": {"target": "Fictional competitor", "objective_state": "Fixture goal"},
            "mirror_audit": {"prior_resolution": "EXACT PRIOR ANALYSIS", "extra_context": "Fixture context"},
        }
        status, result = await self.http("POST", "/api/v2/sessions", {
            "pathway": pathway, "scenario": scenarios[pathway],
            "iterative": iterative, "max_strokes": slots,
        })
        self.assertEqual(status, 201, result)
        return result["session_id"]

    async def route(self, sid, endpoint, body=None):
        return await self.http("POST", f"/api/v2/sessions/{sid}/{endpoint}", body)

    async def test_f01_iteration_budget_and_final_role_controls(self):
        for slots, bridge in ((1, True), (2, True), (3, True), (4, True), (3, False)):
            with self.subTest(slots=slots, bridge=bridge):
                sid = await self.create(iterative=True, slots=max(2, slots))
                status, reply = await self.route(sid, "iterate", {
                    "truth_packets": PACKETS, "include_bridge": bridge, "max_strokes": slots,
                })
                self.assertEqual(status, 200, reply)
                self.assertEqual(len(reply["strokes"]), slots)
                status, final = await self.route(sid, "complete")
                self.assertEqual(status, 200, final)
                self.assertEqual(final["final_resolution"]["final_text"], "SYNTHESIS ANSWER")
                self.assertEqual(len(final["final_resolution"]["strokes"]), slots)

    async def test_f01_bridge_failure_and_bicameral_finalization(self):
        sid = await self.create(iterative=True, slots=4)
        self.bridge_fails = True
        status, reply = await self.route(sid, "iterate", {"truth_packets": PACKETS})
        self.assertEqual(status, 200, reply)
        self.assertEqual((await self.route(sid, "complete"))[1]["final_resolution"]["final_text"], "SYNTHESIS ANSWER")
        self.bridge_fails = False
        sid = await self.create(iterative=True, slots=2)
        status, reply = await self.route(sid, "bicameral-loop", {"truth_packets": PACKETS, "max_iterations": 1})
        self.assertEqual(status, 200, reply)
        self.assertEqual(reply["strokes"][-1]["audit_kind"], "bridge")
        self.assertEqual((await self.route(sid, "complete"))[1]["final_resolution"]["final_text"], "SYNTHESIS ANSWER")

    async def test_f02_all_pathways_and_mirror_target(self):
        for pathway in ("cleanroom", "genie", "offensive", "mirror_audit"):
            with self.subTest(pathway=pathway):
                sid = await self.create(pathway)
                status, reply = await self.route(sid, "synthesize", {"truth_packets": PACKETS})
                self.assertEqual(status, 200, reply)
                expected = "AUDITOR CRITIQUE" if pathway == "mirror_audit" else "SYNTHESIS ANSWER"
                self.assertEqual(reply["stroke"]["raw_response"], expected)
                self.assertEqual((await self.route(sid, "complete"))[1]["final_resolution"]["final_text"], expected)
        auditor_prompt = next(prompt for role, prompt in self.calls if role == "auditor")
        self.assertIn("EXACT PRIOR ANALYSIS", auditor_prompt)
        self.assertIn("Fixture context", auditor_prompt)
        sid = await self.create("mirror_audit", iterative=True, slots=4)
        self.assertEqual((await self.route(sid, "iterate", {"truth_packets": PACKETS}))[0], 200)
        self.assertEqual((await self.route(sid, "run-full-loop", {}))[0], 422)
        self.assertEqual((await self.route(sid, "synthesize", {"truth_packets": []}))[0], 422)
        missing = await self.registry.create(Scenario(question="not a prior analysis"), Pathway.MIRROR_AUDIT)
        count = len(self.calls)
        self.assertEqual((await self.route(missing.id, "synthesize", {"truth_packets": PACKETS}))[0], 422)
        self.assertEqual(len(self.calls), count)

    async def test_f03_cancel_during_triage_and_before_start(self):
        sid = await self.create()
        self.block_role = "triage"
        self.assertEqual((await self.route(sid, "run-full-loop", {}))[0], 202)
        await until(lambda: any(role == "triage" for role, _ in self.calls))
        status, reply = await self.route(sid, "cancel")
        self.assertEqual(status, 200, reply)
        self.assertEqual(reply["state"]["status"], "cancelled")
        self.gate.set()
        self.assertFalse(any(role == "research" for role, _ in self.calls))
        self.assertEqual((await self.route(sid, "run-full-loop", {}))[0], 409)
        self.assertEqual((await self.route(sid, "complete"))[0], 409)

    async def test_f03_cancel_during_research_stops_following_subjects(self):
        sid = await self.create()
        self.subject_count = 3
        self.block_role = "research"
        await self.route(sid, "run-full-loop", {"max_subjects": 3})
        await until(lambda: any(role == "research" for role, _ in self.calls))
        await self.route(sid, "cancel")
        self.gate.set()
        self.assertEqual(sum(role == "research" for role, _ in self.calls), 1)
        self.assertEqual(self.registry.get(sid).strokes, [])

    async def test_f04_duplicate_and_cross_endpoint_start_rejected(self):
        sid = await self.create(iterative=True, slots=4)
        self.block_role = "triage"
        self.assertEqual((await self.route(sid, "run-full-loop", {}))[0], 202)
        # Reservation must already exist, even before the driver is scheduled.
        self.assertEqual((await self.route(sid, "run-full-loop", {}))[0], 409)
        for endpoint in ("synthesize", "iterate", "bicameral-loop"):
            status, reply = await self.route(sid, endpoint, {"truth_packets": PACKETS})
            self.assertEqual(status, 409, reply)
        self.assertEqual((await self.route(sid, "complete"))[0], 409)
        other = await self.create()
        self.assertEqual((await self.route(other, "run-full-loop", {}))[0], 202)
        await until(lambda: sum(role == "triage" for role, _ in self.calls) == 2)
        self.gate.set()
        await until(lambda: all(self.registry.get(s).status == "complete" for s in (sid, other)))

    async def test_f04_direct_nested_driver_reserves_session(self):
        sid = await self.create(iterative=True, slots=4)
        self.block_role = "engine"
        session = self.registry.get(sid)
        drive = asyncio.create_task(self.orchestrator.run_iterative_engine(
            session, [TruthPacket(**PACKETS[0])], max_strokes=4,
        ))
        await until(lambda: bool(self.calls))
        with self.assertRaisesRegex(RuntimeError, "active operation"):
            await self.orchestrator.run_synthesis_stroke(session, [TruthPacket(**PACKETS[0])])
        self.gate.set()
        self.assertEqual(len(await drive), 4)

    async def test_f05_late_synthesis_does_not_rewrite_cancelled_state(self):
        sid = await self.create()
        self.block_role = "engine"
        work = asyncio.create_task(self.route(sid, "synthesize", {"truth_packets": PACKETS}))
        await until(lambda: bool(self.calls))
        await self.route(sid, "cancel")
        self.gate.set()
        self.assertEqual((await work)[0], 409)
        self.assertEqual((await self.route(sid, "complete"))[0], 409)
        session = self.registry.get(sid)
        self.assertEqual(session.status, "cancelled")
        self.assertEqual(session.strokes, [])
        with self.assertRaises(SessionCancelledError):
            await session.record_stroke(self.stroke())

    @staticmethod
    def stroke(number=1, pathway=Pathway.CLEANROOM):
        return StrokeResult(stroke_number=number, pathway=pathway, raw_response="fixture",
                            started_at=utcnow(), completed_at=utcnow())

    async def test_f05_completed_snapshot_stable_and_translation_supported(self):
        sid = await self.create()
        await self.route(sid, "synthesize", {"truth_packets": PACKETS})
        session = self.registry.get(sid)
        first = await session.complete()
        self.assertIs(await session.complete(), first)
        with self.assertRaises(RuntimeError):
            await session.record_stroke(self.stroke(2))
        register = next(iter(TRANSLATION_REGISTERS))
        self.assertEqual((await self.route(sid, "translate", {"stroke_number": 1, "register": register}))[0], 200)
        self.block_role = "engine"
        previous = len(self.calls)
        work = asyncio.create_task(self.route(sid, "translate", {"stroke_number": 1, "register": register}))
        await until(lambda: len(self.calls) > previous)
        status, stopped = await self.route(sid, "cancel")
        self.assertEqual(status, 200)
        self.assertTrue(stopped["cancelled"])
        self.assertEqual((await work)[0], 409)
        self.assertIs(session.final, first)
        self.assertEqual(session.status, "complete")
        self.gate.set()
        self.assertEqual((await self.route(sid, "translate", {"stroke_number": 1, "register": register}))[0], 200)

    async def test_f05_persisted_terminal_state_and_final_selector(self):
        store = SessionStore(str(Path(self.directory.name) / "fixture.db"))
        for terminal in ("complete", "cancelled", "error"):
            session = await self.registry.create(Scenario(question="fixture"), Pathway.CLEANROOM)
            await session.record_stroke(self.stroke())
            await session.record_stroke(self.stroke(2, Pathway.MIRROR_AUDIT).model_copy(update={"raw_response": "CRITIQUE"}))
            if terminal == "complete":
                await session.complete()
            elif terminal == "cancelled":
                await session.request_cancel()
            else:
                await session.fail("fixture")
            store.save_session(session)
        for data in store.load_all():
            data["final_text"] = None
            restored = Session.from_persisted_state(data)
            self.assertEqual(restored.status, data["status"])
            if restored.status == "complete":
                self.assertEqual(restored.final.final_text, "fixture")
                data["final_text"] = "authoritative saved result"
                self.assertEqual(Session.from_persisted_state(data).final.final_text, "authoritative saved result")
            else:
                with self.assertRaises(RuntimeError):
                    await restored.complete()
            with self.assertRaises(RuntimeError):
                await restored.record_stroke(self.stroke(3))

    async def test_f06_excess_subjects_rejected_before_research(self):
        self.subject_count = 3
        sid = await self.create()
        await self.route(sid, "run-full-loop", {"max_subjects": 1})
        await until(lambda: self.registry.get(sid).status == "error")
        self.assertIn("selected limit is 1", self.registry.get(sid).error_message)
        self.assertFalse(any(role == "research" for role, _ in self.calls))
        self.calls.clear()
        self.subject_count = 1
        sid = await self.create()
        await self.route(sid, "run-full-loop", {"max_subjects": 1})
        await until(lambda: self.registry.get(sid).status == "complete")
        self.assertEqual(sum(role == "research" for role, _ in self.calls), 1)

    async def test_f07_bridge_obeys_shared_corpus_selection(self):
        root = Path(self.directory.name) / "corpus"
        root.mkdir()
        (root / "selected.md").write_text("SELECTED SENTINEL", encoding="utf-8")
        (root / "excluded.md").write_text("EXCLUDED SENTINEL", encoding="utf-8")
        (root / "extra.txt").write_text("EXCLUDED SENTINEL", encoding="utf-8")
        with patch.dict(os.environ, {"GANYMEDE_FOUNDATIONS_DIR": str(root), "GANYMEDE_CORPUS_FILES": "selected.md"}):
            runtime = ClaudeRuntimeService()
            orch = GanymedeOrchestrator(runtime)
            for enabled in (True, False):
                result = await orch.provision_bridge_notebook(truth_packets=[TruthPacket(**PACKETS[0])], include_foundations=enabled)
                await runtime.query_notebook(result["notebook_id"], "fixture")
                prompt = self.calls[-1][1]
                self.assertNotIn("EXCLUDED SENTINEL", prompt)
                self.assertEqual("SELECTED SENTINEL" in prompt, enabled)
            self.assertIn("SELECTED SENTINEL", runtime.engine.corpus)
            with patch.dict(os.environ, {"GANYMEDE_CORPUS_FILES": "missing.md"}):
                with self.assertRaises(RuntimeError):
                    await orch.provision_bridge_notebook(truth_packets=[TruthPacket(**PACKETS[0])])

    async def test_f14_provider_json_types_fall_back_without_http_500(self):
        valid = {"pathway": "cleanroom", "scenario": {"question": "classified"}, "confidence": 0.8,
                 "needs_external_knowledge": False, "rationale": "fixture", "clarifying_questions": []}
        for field, bad in (("scenario", 42), ("scenario", []), ("confidence", "certain"),
                           ("confidence", float("nan")), ("needs_external_knowledge", "false"),
                           ("clarifying_questions", "question"), ("clarifying_questions", [1])):
            self.dispatch_payload = dict(valid, **{field: bad})
            status, response = await self.http("POST", "/api/v2/dispatch", {"text": "original request"})
            self.assertEqual(status, 200, response)
            self.assertEqual(response["confidence"], 0)
            self.assertEqual(response["scenario"]["question"], "original request")
        self.dispatch_payload = valid
        status, response = await self.http("POST", "/api/v2/dispatch", {"text": "original request"})
        self.assertEqual(status, 200)
        self.assertEqual(response["scenario"]["question"], "classified")
        self.assertFalse(response["needs_external_knowledge"])


class ParserTests(unittest.TestCase):
    def test_f14_wrong_member_types_and_valid_alias(self):
        for field in ("name", "surgical_prompt"):
            for bad in (42, True, [], {}, ["text"]):
                row = {"name": "fixture", "surgical_prompt": "fixture query", field: bad}
                raw = "<HIT_LIST_JSON>" + json.dumps({"subjects": [row]}) + "</HIT_LIST_JSON>"
                self.assertEqual(parse_triage_hit_list(raw)[1], [])
        self.assertEqual(parse_triage_hit_list("invalid JSON")[1], [])
        raw = '<HIT_LIST_JSON>{"subjects":[{"name":" fixture ","prompt":" query "}]}</HIT_LIST_JSON>'
        self.assertEqual(parse_triage_hit_list(raw)[1], [{"name": "fixture", "surgical_prompt": "query"}])


class ProcessCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_f03_wrapper_exit_does_not_orphan_descendant(self):
        with tempfile.TemporaryDirectory(prefix="ganymede-wrapper-") as directory:
            marker = Path(directory) / "escaped.txt"
            child_code = f"import time,pathlib; time.sleep(1); pathlib.Path({str(marker)!r}).write_text('escaped')"
            code = (
                "import subprocess,sys,json; "
                f"subprocess.Popen([sys.executable,'-c',{child_code!r}], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
                "print(json.dumps({'result':'wrapper done'}))"
            )
            runner = ClaudeCliRunner()
            with patch.object(runner, "_base_command", return_value=[sys.executable, "-c", code]):
                result = await runner.invoke(prompt="fixture", system_file=Path(directory) / "unused")
            self.assertEqual(result.text, "wrapper done")
            await asyncio.sleep(1.3)
            self.assertFalse(marker.exists(), "An owned descendant survived wrapper completion")

    async def test_f03_cancel_reaps_real_harmless_parent_and_child(self):
        with tempfile.TemporaryDirectory(prefix="ganymede-child-") as directory:
            pid_file = Path(directory) / "child.pid"
            code = (
                "import subprocess,sys,time,pathlib; "
                "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                f"pathlib.Path({str(pid_file)!r}).write_text(str(child.pid)); "
                "time.sleep(30)"
            )
            processes = []
            original = subprocess.Popen
            def capture(*args, **kwargs):
                process = original(*args, **kwargs)
                if args[0][0] == sys.executable:
                    processes.append(process)
                return process
            runner = ClaudeCliRunner()
            with patch.object(runner, "_base_command", return_value=[sys.executable, "-c", code]), patch(
                "app.services.substrate.subprocess.Popen", side_effect=capture,
            ):
                work = asyncio.create_task(runner.invoke(prompt="fixture", system_file=Path(directory) / "unused"))
                await until(pid_file.exists)
                child_pid = int(pid_file.read_text())
                work.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await asyncio.wait_for(work, 10)
            self.assertEqual(len(processes), 1)  # cancellation must not retry
            self.assertIsNotNone(processes[0].poll())
            if os.name == "nt":
                # Holding a process handle avoids PID-reuse ambiguity.
                import ctypes
                kernel = ctypes.windll.kernel32
                kernel.OpenProcess.restype = ctypes.c_void_p
                handle = kernel.OpenProcess(0x1000, False, child_pid)
                if handle:
                    code = ctypes.c_ulong()
                    try:
                        self.assertTrue(kernel.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code)))
                        self.assertNotEqual(code.value, 259)  # STILL_ACTIVE
                    finally:
                        kernel.CloseHandle(ctypes.c_void_p(handle))
            else:
                # The killed descendant may briefly be a zombie until its adopter reaps it.
                stat = Path(f"/proc/{child_pid}/stat")
                if stat.exists():
                    self.assertEqual(stat.read_text().split()[2], "Z")

    async def test_f03_cancel_before_spawn_and_normal_output(self):
        stop = threading.Event()
        stop.set()
        with patch("app.services.substrate.subprocess.Popen") as popen:
            with self.assertRaisesRegex(RuntimeError, "before process creation"):
                ClaudeCliRunner._communicate(["unused"], "fixture", 1, stop)
            popen.assert_not_called()
        code = "import json,sys; print(json.dumps({'result':sys.stdin.read()}))"
        runner = ClaudeCliRunner()
        with patch.object(runner, "_base_command", return_value=[sys.executable, "-c", code]):
            result = await runner.invoke(prompt="valid control", system_file=Path("unused"))
        self.assertEqual(result.text, "valid control")

    async def test_f03_timeout_reaps_worker_and_retries_are_bounded(self):
        processes = []
        original = subprocess.Popen
        def capture(*args, **kwargs):
            result = original(*args, **kwargs)
            if args[0][0] == sys.executable:
                processes.append(result)
            return result
        runner = ClaudeCliRunner()
        runner.timeout = 0.1
        runner.max_attempts = 2
        with patch.object(runner, "_base_command", return_value=[sys.executable, "-c", "import time; time.sleep(30)"]), patch(
            "app.services.substrate.subprocess.Popen", side_effect=capture,
        ):
            with self.assertRaisesRegex(RuntimeError, "after 2 attempt"):
                await runner.invoke(prompt="fixture", system_file=Path("unused"))
        self.assertEqual(len(processes), 2)
        self.assertTrue(all(process.poll() is not None for process in processes))


if __name__ == "__main__":
    unittest.main()
