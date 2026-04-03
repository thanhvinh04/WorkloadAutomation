import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from config import PYTHON_EXE, PDF_TO_SQL_SCRIPT, SQL_TO_SHEET_SCRIPT, DESIGNCHART_SCRIPT, BASE_DIR

def run_cmd_and_log(cmd: List[str], log_file: Path, env: Optional[dict] = None) -> int:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8", errors="replace") as f:
        f.write("\n=== RUN ===\n")
        f.write("CMD: " + " ".join(cmd) + "\n")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

        assert proc.stdout is not None
        for line in proc.stdout:
            f.write(line)
            f.flush()

        return proc.wait()


def safe_rmtree(p: Path) -> None:
    """Delete a folder safely (ignore errors)."""
    try:
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    except Exception:
        pass


def run_pipeline(input_dir: Path, log_file: Path, cleanup_input_dir: bool = True) -> int:
    """
    Run:
      1) DesignChart (main image + Colorways)
      2) PDF -> SQL
      3) SQL -> Sheet

    Then cleanup input_dir (delete uploaded PDFs) if cleanup_input_dir=True.
    """
    try:
        # Step1 DesignChart (use -m to run as module for relative imports)
        designchart_env = os.environ.copy()
        designchart_env["PYTHONPATH"] = str(BASE_DIR.parent)

        pdf_files = list(input_dir.glob("*.pdf"))
        for pdf_file in pdf_files:
            c1 = run_cmd_and_log(
                [PYTHON_EXE, "-m", "designchart_parser.main", "--pdf", str(pdf_file)],
                log_file,
                env=designchart_env,
            )
            if c1 != 0:
                return c1

        # Step2 PDF -> SQL (delete+append by file already inside your script)
        c2 = run_cmd_and_log(
            [PYTHON_EXE, PDF_TO_SQL_SCRIPT, "--input-dir", str(input_dir)],
            log_file,
        )
        if c2 != 0:
            return c2

        # Step3 SQL -> Sheet (pass input-dir so it knows which files to replace)
        c3 = run_cmd_and_log(
            [PYTHON_EXE, SQL_TO_SHEET_SCRIPT, "--input-dir", str(input_dir)],
            log_file,
        )
        return c3

    finally:
        # ALWAYS cleanup uploaded PDFs folder after processing (success/fail)
        if cleanup_input_dir:
            # safe_rmtree(input_dir)
            pass