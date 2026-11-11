"""Converter contract tests; run: python -m unittest discover -s tests -v."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(os.environ.get("CYBERCONVERT_MODULE", Path(__file__).resolve().parents[1] / "cyberconvert.py"))
SPEC = importlib.util.spec_from_file_location("cyberconvert", MODULE_PATH)
converter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(converter)


class ConverterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.txt"
        self.output = self.root / "output.mem"

    def convert(self, source):
        self.source.write_text(source, encoding="utf-8")
        return converter.convert(self.source, self.output)

    def assert_rejected_without_overwrite(self, source):
        self.output.write_text("preserve-me\n", encoding="ascii")
        with self.assertRaises(ValueError):
            self.convert(source)
        self.assertEqual(self.output.read_text(encoding="ascii"), "preserve-me\n")

    def test_comments_spaces_tabs_and_zero_word(self):
        words = self.convert("// comment101\n 00000000\t00000000 00000000 00000000 // zero\n" + "1" * 32 + "\n")
        self.assertEqual(words, ["00000000", "ffffffff"])
        self.assertEqual(self.output.read_text(encoding="ascii"), "00000000\nffffffff\n")

    def test_illegal_characters_do_not_get_silently_discarded(self):
        for illegal in ("x", "2", "_", ";", "r", "０", "\ufeff"):
            with self.subTest(illegal=illegal):
                self.assert_rejected_without_overwrite("0" * 32 + illegal + "\n")

    def test_exactly_32_bits_required(self):
        for length in (1, 31, 33, 64):
            with self.subTest(length=length):
                self.assert_rejected_without_overwrite("0" * length)

    def test_empty_and_comments_only_rejected(self):
        for source in ("", " \n\t", "// nothing101\n"):
            with self.subTest(source=source):
                self.assert_rejected_without_overwrite(source)

    def test_parse_error_does_not_leave_new_partial_file(self):
        self.source.write_text("0" * 32 + "\n" + "1" * 31, encoding="ascii")
        with self.assertRaises(ValueError):
            converter.convert(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_same_input_and_output_rejected(self):
        original = "0" * 32 + "\n"
        self.source.write_text(original, encoding="ascii")
        with self.assertRaises(ValueError):
            converter.convert(self.source, self.source)
        self.assertEqual(self.source.read_text(encoding="ascii"), original)

    def test_program_size_fits_actual_128_word_rom(self):
        self.assertEqual(len(self.convert(("0" * 32 + "\n") * 128)), 128)
        self.assert_rejected_without_overwrite(("0" * 32 + "\n") * 129)

    def test_supplied_programs_reproduce_checked_in_images(self):
        project = Path(__file__).resolve().parents[1]
        for source_name, image_name in (("program_var12.txt", "program.mem"), ("program_low16.txt", "program_low16.mem"), ("program_operations.txt", "program_operations.mem")):
            with self.subTest(source=source_name):
                words = converter.convert(project / source_name, self.output)
                self.assertEqual("\n".join(words) + "\n", (project / image_name).read_text(encoding="ascii"))


if __name__ == "__main__":
    unittest.main()
