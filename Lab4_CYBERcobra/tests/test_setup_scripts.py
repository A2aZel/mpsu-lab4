"""Check Tcl program selection and staged files without requiring Vivado."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
TCLSH = shutil.which("tclsh")
MOCK_VIVADO = """
proc current_project {args} {return ""}
proc create_project {name directory args} {file mkdir $directory}
proc set_property {args} {puts "TEST_PROPERTY=$args"}
proc get_files {args} {return [lindex $args end]}
proc get_filesets {name} {return $name}
proc add_files {args} {}
proc update_compile_order {args} {}
"""


@unittest.skipUnless(TCLSH, "tclsh is required on PATH")
class SetupScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Spaces exercise the quoting used by the actual Windows/Linux scripts.
        self.root = Path(self.temp.name) / "Lab4 with spaces"
        shutil.copytree(PROJECT, self.root,
                        ignore=shutil.ignore_patterns("build", "gui_build", "__pycache__"))

    def run_script(self, mode, gui=True):
        target = self.root / ("walkthrough/setup_gui.tcl" if gui else "lab4_common.tcl")
        script = MOCK_VIVADO + """
set ::lab4_walkthrough_program_mode $env(TEST_MODE)
if {[catch {source $env(TEST_SCRIPT)} message]} {
    puts stderr $message
    exit 1
}
"""
        if gui:
            script += 'puts "TEST_STAGED=$staged_program"\n'
        else:
            script += 'lab4::prepare test $env(TEST_MODE)\nputs "TEST_STAGED=$lab4::memory"\n'
        return subprocess.run(
            [TCLSH], input=script, text=True, capture_output=True, timeout=10,
            env={**os.environ, "TEST_MODE": mode, "TEST_SCRIPT": str(target)},
        )

    def assert_staged(self, result, source_name):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        staged = next(line.removeprefix("TEST_STAGED=")
                      for line in result.stdout.splitlines() if line.startswith("TEST_STAGED="))
        self.assertEqual(Path(staged).read_bytes(), (self.root / source_name).read_bytes())

    def test_gui_default_program(self):
        result = self.run_script("default")
        self.assert_staged(result, "program.mem")
        self.assertIn("WALKTHROUGH_PROGRAM=default", result.stdout)
        self.assertNotIn("OPERATIONS=1", result.stdout)

    def test_gui_operations_program_and_testbench_mode(self):
        result = self.run_script("operations")
        self.assert_staged(result, "program_operations.mem")
        self.assertIn("WALKTHROUGH_PROGRAM=operations", result.stdout)
        self.assertIn("xsim.simulate.xsim.more_options {-testplusarg OPERATIONS=1}", result.stdout)

    def test_gui_rejects_an_unsupported_program(self):
        result = self.run_script("low16")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GUI program must be default or operations", result.stderr)

    def test_batch_selects_each_memory_image(self):
        for mode, filename in (("default", "program.mem"), ("low16", "program_low16.mem"),
                               ("operations", "program_operations.mem")):
            with self.subTest(mode=mode):
                self.assert_staged(self.run_script(mode, gui=False), filename)


if __name__ == "__main__":
    unittest.main()
