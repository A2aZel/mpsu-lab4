"""Check the switch-selected program against an independent Python reference."""
from itertools import product
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
SOURCES = (
    "memory_pkg.sv", "alu_opcodes_pkg.sv", "fulladder.sv", "fulladder4.sv",
    "fulladder32.sv", "alu.sv", "instr_mem.sv", "register_file.sv",
    "CYBERcobra.sv",
)
IVERILOG = shutil.which("iverilog")
VVP = shutil.which("vvp")
PASS = re.compile(
    r"DEMO_PASS SW=([0-9a-fA-F]+) OUT=([0-9a-fA-F]+) "
    r"PC=([0-9a-fA-F]+) after (\d+) ordinary steps; "
    r"J0 stable for 2 extra steps; checks=(\d+)"
)


def expected_operation(opcode, a, b):
    signed_a = a - 64 if a & 32 else a
    signed_b = b - 64 if b & 32 else b
    shift = b & 31
    results = (
        a + b, a - b, a & b, a | b, a ^ b,
        a << shift, a >> shift, signed_a >> shift,
        signed_a < signed_b, a < b, a == b, a != b,
        signed_a < signed_b, signed_a >= signed_b, a < b, a >= b,
    )
    return int(results[opcode]) & 0xFFFFFFFF


@unittest.skipUnless(IVERILOG and VVP, "iverilog and vvp are required on PATH")
class OperationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.build.cleanup)
        cls.build_dir = Path(cls.build.name)
        cls.demo_source = (PROJECT / "walkthrough/tb_lab4_demo.sv").read_text()
        cls.image = cls.compile_demo(cls.demo_source, cls.build_dir)

    @staticmethod
    def compile_demo(source, directory):
        testbench = directory / "tb_lab4_demo.sv"
        image = directory / "operations.vvp"
        testbench.write_text(source, encoding="utf-8")
        result = subprocess.run(
            [IVERILOG, "-g2012", "-s", "tb_lab4_demo", "-o", str(image),
             *(str(PROJECT / name) for name in SOURCES), str(testbench)],
            cwd=directory, capture_output=True, text=True, timeout=30,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return image

    def setUp(self):
        self.run_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.run_dir.cleanup)
        self.directory = Path(self.run_dir.name)
        shutil.copyfile(PROJECT / "program_operations.mem", self.directory / "program.mem")

    def simulate(self, sw=None, image=None):
        args = [VVP, str(image or self.image), "+OPERATIONS=1"]
        if sw is not None:
            args.append(f"+SW={sw:04x}")
        return subprocess.run(
            args, cwd=self.directory, capture_output=True, text=True, timeout=10,
        )

    def assert_pass(self, result, opcode, a, b):
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertNotIn("DEMO_FAIL", output)
        matches = PASS.findall(output)
        self.assertEqual(len(matches), 1, output)
        actual_sw, actual_out, actual_pc, steps, checks = matches[0]
        expected = expected_operation(opcode, a, b)
        self.assertEqual(int(actual_sw, 16), (opcode << 12) | (a << 6) | b, output)
        self.assertEqual(int(actual_out, 16), expected, output)
        self.assertEqual(int(actual_pc, 16), 0x170, output)
        self.assertEqual(int(steps), 19 + 2 * opcode + int(opcode >= 10 and expected == 1), output)
        self.assertEqual(int(checks), 21, output)

    def test_every_operation_with_boundary_operands(self):
        # Covers signed -32/-1/0/1/31, shift 0/1/31/32/63, both branch
        # outcomes, subtraction underflow, and complementary bit patterns.
        pairs = list(product((0, 1, 31, 32, 63), repeat=2)) + [(21, 42), (42, 21)]
        for opcode, (a, b) in product(range(16), pairs):
            with self.subTest(opcode=f"{opcode:x}", a=a, b=b):
                sw = (opcode << 12) | (a << 6) | b
                self.assert_pass(self.simulate(sw), opcode, a, b)

    def test_editing_only_initial_sw_value(self):
        original = "logic [15:0] sw = 16'h03b8;"
        self.assertEqual(self.demo_source.count(original), 1)
        # Arithmetic right shift of -32 by one must retain its sign.
        sw = (7 << 12) | (32 << 6) | 1
        edited = self.demo_source.replace(original, f"logic [15:0] sw = 16'h{sw:04x};")
        image = self.compile_demo(edited, self.directory)
        self.assert_pass(self.simulate(image=image), 7, 32, 1)

    def test_wrong_result_is_rejected(self):
        memory = self.directory / "program.mem"
        words = memory.read_text().splitlines()
        self.assertEqual(len(words), 93)
        # Replace the ADD handler with LI r1, 0: execution still reaches HALT.
        words[48] = "00000001"
        memory.write_text("\n".join(words) + "\n", encoding="ascii")
        result = self.simulate((7 << 6) | 5)
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn("operation output", output)
        self.assertNotIn("DEMO_PASS", output)

    def test_resuming_after_finish_does_not_fail_or_run_forever(self):
        self.assertEqual(self.demo_source.count("$finish;"), 1)
        resumed = self.demo_source.replace("$finish;", ";")
        image = self.compile_demo(resumed, self.directory)
        sw = (15 << 12) | (63 << 6) | 32
        self.assert_pass(self.simulate(sw, image), 15, 63, 32)


if __name__ == "__main__":
    unittest.main()
