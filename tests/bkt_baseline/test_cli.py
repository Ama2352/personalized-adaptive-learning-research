from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from knowledge_tracing.bkt_baseline.cli import main


class CliTests(unittest.TestCase):
    def test_full_cv_requires_a_completed_pilot(self):
        parent = Path("artifacts/bkt_baseline/test_tmp")
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as root:
            with self.assertRaisesRegex(RuntimeError, "pilot"):
                main(["--artifacts", root, "cv"])

    def test_report_defaults_to_a_separate_generated_file(self):
        with patch("knowledge_tracing.bkt_baseline.cli.render_report", return_value=Path("generated.md")) as render:
            main(["report"])
        destination = render.call_args.args[1]
        self.assertEqual(destination.name, "bkt-baseline-artifact-report.md")
        self.assertNotEqual(destination.name, "bkt-baseline-results.md")


if __name__ == "__main__":
    unittest.main()
