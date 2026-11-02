from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import subprocess
import json
import os
from pathlib import Path

PORT = 5000
REPO_DIR = Path(__file__).resolve().parent.parent
BRANCHLITE_EXE = REPO_DIR / "branchlite.exe"

class BranchLiteHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            html_path = REPO_DIR / "gui" / "index.html"
            if not html_path.exists():
                self.send_error(404, "index.html not found")
                return
            content = html_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        elif self.path == "/api/status":
            status_data = self.get_repo_status()
            payload = json.dumps(status_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/execute":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            payload = json.loads(body)
            args = payload.get("args", [])

            cmd = [str(BRANCHLITE_EXE)] + args
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(REPO_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                response = {
                    "returncode": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "status": self.get_repo_status()
                }
            except Exception as e:
                response = {
                    "returncode": 1,
                    "stdout": "",
                    "stderr": str(e),
                    "status": self.get_repo_status()
                }

            out_bytes = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out_bytes)))
            self.end_headers()
            self.wfile.write(out_bytes)
            return

        self.send_error(404, "Endpoint not found")

    def get_repo_status(self):
        vcs_dir = REPO_DIR / ".branchlite"
        if not vcs_dir.exists():
            return {
                "initialized": False,
                "currentBranch": None,
                "branches": [],
                "commits": [],
                "stagedFiles": [],
                "workingFiles": []
            }

        # Current branch from HEAD
        head_file = vcs_dir / "HEAD"
        current_branch = head_file.read_text(encoding="utf-8").strip() if head_file.exists() else "main"

        # All branches
        branches_dir = vcs_dir / "branches"
        branches = []
        if branches_dir.exists():
            for b in sorted(branches_dir.iterdir()):
                if b.is_file():
                    branches.append({
                        "name": b.name,
                        "tip": b.read_text(encoding="utf-8").strip()
                    })

        # Parse Commits
        commits_dir = vcs_dir / "commits"
        commits = []
        if commits_dir.exists():
            for c in sorted(commits_dir.iterdir(), key=os.path.getmtime, reverse=True):
                if c.is_file():
                    content = c.read_text(encoding="utf-8").splitlines()
                    commit_data = {
                        "id": c.name,
                        "parent": "-",
                        "parent2": "",
                        "time": "",
                        "message": "",
                        "files": []
                    }
                    in_files = False
                    for line in content:
                        if in_files:
                            parts = line.strip().split(" ", 1)
                            if len(parts) == 2:
                                commit_data["files"].append({"hash": parts[0], "file": parts[1]})
                        elif line.startswith("parent "):
                            commit_data["parent"] = line[7:].strip()
                        elif line.startswith("parent2 "):
                            commit_data["parent2"] = line[8:].strip()
                        elif line.startswith("time "):
                            commit_data["time"] = line[5:].strip()
                        elif line.startswith("message "):
                            commit_data["message"] = line[8:].strip()
                        elif line == "files":
                            in_files = True
                    commits.append(commit_data)

        # Staged files from index
        index_file = vcs_dir / "index"
        staged = []
        if index_file.exists():
            for line in index_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    parts = line.strip().split(" ", 1)
                    if len(parts) == 2:
                        staged.append({"hash": parts[0], "file": parts[1]})

        # Working directory files
        working = []
        for f in REPO_DIR.iterdir():
            if f.is_file() and not f.name.endswith(".exe") and f.name != "server.py":
                working.append(f.name)

        return {
            "initialized": True,
            "currentBranch": current_branch,
            "branches": branches,
            "commits": commits,
            "stagedFiles": staged,
            "workingFiles": sorted(working)
        }

if __name__ == "__main__":
    os.chdir(str(REPO_DIR))
    server = ThreadingHTTPServer(("", PORT), BranchLiteHandler)
    print(f"BranchLite GUI Server running at http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
