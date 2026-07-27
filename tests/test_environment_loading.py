import os
import tempfile
import unittest
from pathlib import Path

from rag_engine import load_environment_config


class EnvironmentLoadingTests(unittest.TestCase):
    def test_load_environment_config_reads_dotenv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text("GEMINI_API_KEY=test-key-from-env\n", encoding="utf-8")

            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                os.environ.pop("GEMINI_API_KEY", None)

                load_environment_config()

                self.assertEqual(os.environ.get("GEMINI_API_KEY"), "test-key-from-env")
            finally:
                os.chdir(original_cwd)
                os.environ.pop("GEMINI_API_KEY", None)


if __name__ == "__main__":
    unittest.main()
