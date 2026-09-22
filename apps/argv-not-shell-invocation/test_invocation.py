import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from invocation import InvocationDenied, build_invocation, run

# A real child process: this interpreter, echoing its own argv back.
ECHO_ARGV = "import sys, json; print(json.dumps(sys.argv[1:]))"


class ArgvNotShellInvocationTests(unittest.TestCase):
    def test_arguments_reach_the_child_exactly_as_given(self):
        invocation = build_invocation(sys.executable, ["-c", ECHO_ARGV, "plain", "two words"])

        result = run(invocation)

        self.assertEqual(result.returncode, 0)
        self.assertIn('"two words"', result.stdout)

    def test_shell_metacharacters_arrive_as_literal_text(self):
        hostile = "toy; rm -rf /tmp/nothing && echo pwned | cat > /tmp/out"
        invocation = build_invocation(sys.executable, ["-c", ECHO_ARGV, hostile])

        result = run(invocation)

        # The whole string came back as one argument. Nothing was split on ';'
        # or '|', because nothing ever parsed it.
        self.assertIn("rm -rf", result.stdout)
        self.assertEqual(result.stdout.count("["), 1)

    def test_an_argument_that_looks_like_a_flag_is_still_an_argument(self):
        invocation = build_invocation(sys.executable, ["-c", ECHO_ARGV, "--allow-unisolated"])

        result = run(invocation)

        self.assertIn("--allow-unisolated", result.stdout)

    def test_a_relative_program_name_is_refused(self):
        with self.assertRaises(InvocationDenied) as ctx:
            build_invocation("python", ["-c", "print(1)"])

        self.assertEqual(ctx.exception.reason, "relative_program")

    def test_a_single_command_line_string_is_refused(self):
        with self.assertRaises(InvocationDenied) as ctx:
            build_invocation(sys.executable, "-c 'print(1)' && echo pwned")

        self.assertEqual(ctx.exception.reason, "shell_string_argument")

    def test_an_empty_program_is_refused(self):
        with self.assertRaises(InvocationDenied) as ctx:
            build_invocation("   ", ["-c", "print(1)"])

        self.assertEqual(ctx.exception.reason, "empty_program")

    def test_a_non_string_argument_is_refused(self):
        with self.assertRaises(InvocationDenied) as ctx:
            build_invocation(sys.executable, ["-c", ECHO_ARGV, 42])

        self.assertEqual(ctx.exception.reason, "non_string_argument")

    def test_a_path_lookalike_on_path_cannot_be_selected_by_name(self):
        # An attacker drops an executable named like a trusted tool into a
        # directory on PATH. An absolute program path cannot select it.
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PATH"] = tmp + os.pathsep + os.environ["PATH"]
            with self.assertRaises(InvocationDenied) as ctx:
                build_invocation("codex-acp", [])
            self.assertEqual(ctx.exception.reason, "relative_program")

    def test_this_module_never_calls_a_shell(self):
        # Parsed, not grepped: the prose in this module mentions shell=True to
        # say it is never used, and a substring search cannot tell the
        # difference between describing a thing and doing it.
        import ast

        tree = ast.parse(Path("invocation.py").read_text(encoding="utf-8"))

        shell_true, system_calls = [], []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if keyword.arg == "shell" and getattr(keyword.value, "value", None) is True:
                    shell_true.append(node.lineno)
            name = ".".join(
                part for part in (
                    getattr(getattr(node.func, "value", None), "id", None),
                    getattr(node.func, "attr", None),
                ) if part
            )
            if name in {"os.system", "os.popen", "subprocess.getoutput"}:
                system_calls.append(name)

        self.assertEqual(shell_true, [])
        self.assertEqual(system_calls, [])

    def test_the_child_really_ran(self):
        invocation = build_invocation(sys.executable, ["-c", "raise SystemExit(3)"])

        result = run(invocation)

        self.assertEqual(result.returncode, 3)
        self.assertIsInstance(result, subprocess.CompletedProcess)


if __name__ == "__main__":
    unittest.main()
