import subprocess
from pathlib import Path
from config import PYTHON_EXE, BASE_DIR


class PipelineService:
    def execute(self, input_dir: Path, log_file: Path) -> int:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with log_file.open("a", encoding="utf-8") as f:
            f.write("\n=== RUN PHOTO8 PIPELINE ===\n")
            
            # Step 1: DesignChart
            pdf_files = list(input_dir.glob("*.pdf"))
            for pdf_file in pdf_files:
                f.write(f"Processing: {pdf_file.name}\n")
                f.flush()
                
                cmd = [PYTHON_EXE, "-m", "tasks.photo8.designchart_parser.main", "--pdf", str(pdf_file)]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env={"PYTHONPATH": str(BASE_DIR.parent)})
                
                for line in proc.stdout:
                    f.write(line)
                    f.flush()
                
                if proc.wait() != 0:
                    f.write("DesignChart failed\n")
                    return 1
            
            # Step 2: PDF to SQL
            f.write("Running PDF to SQL...\n")
            f.flush()
            cmd = [PYTHON_EXE, str(BASE_DIR / "tasks" / "photo8" / "pdf_to_sql.py"), "--input-dir", str(input_dir)]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            for line in proc.stdout:
                f.write(line)
                f.flush()
            
            if proc.wait() != 0:
                f.write("PDF to SQL failed\n")
                return 1
            
            # Step 3: SQL to Sheet
            f.write("Running SQL to Sheet...\n")
            f.flush()
            cmd = [PYTHON_EXE, str(BASE_DIR / "tasks" / "photo8" / "sql_to_sheet.py"), "--input-dir", str(input_dir)]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            for line in proc.stdout:
                f.write(line)
                f.flush()
            
            return proc.wait()