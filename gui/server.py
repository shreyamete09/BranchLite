from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import subprocess
import json
import os
import shutil
import base64
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
        if self.path == "/api/wipe_all":
            # Deletes .branchlite and demo working files to give a completely clean slate
            vcs_dir = REPO_DIR / ".branchlite"
            if vcs_dir.exists():
                for root, dirs, files in os.walk(vcs_dir, topdown=False):
                    for f in files:
                        try:
                            (Path(root) / f).unlink(missing_ok=True)
                        except Exception:
                            pass
                    for d in dirs:
                        try:
                            (Path(root) / d).rmdir()
                        except Exception:
                            pass
                try:
                    vcs_dir.rmdir()
                except Exception:
                    pass

            # Clean test created files
            test_files = ["auth.cpp", "db.cpp", "feature.txt", "main_notes.txt", "test.txt", "sample.txt", "attendance.txt"]
            for tf in test_files:
                p = REPO_DIR / tf
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass

            # Ensure clean empty repository structure with HEAD pointing to main
            (vcs_dir / "branches").mkdir(parents=True, exist_ok=True)
            (vcs_dir / "commits").mkdir(parents=True, exist_ok=True)
            (vcs_dir / "objects").mkdir(parents=True, exist_ok=True)
            (vcs_dir / "HEAD").write_text("main", encoding="utf-8")
            (vcs_dir / "branches" / "main").write_text("", encoding="utf-8")
            (vcs_dir / "index").write_text("", encoding="utf-8")

            response = {
                "success": True,
                "message": "Repository wiped clean and reinitialized to empty state.",
                "status": self.get_repo_status()
            }
            out_bytes = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out_bytes)))
            self.end_headers()
            self.wfile.write(out_bytes)
            return

        elif self.path == "/api/upload":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            payload = json.loads(body)

            filename = payload.get("filename", "").strip()
            content_b64 = payload.get("content_b64", "")

            safe_filename = Path(filename).name
            if not safe_filename:
                safe_filename = "uploaded_file.txt"

            target_path = REPO_DIR / safe_filename
            try:
                file_bytes = base64.b64decode(content_b64)
                target_path.write_bytes(file_bytes)
                response = {
                    "success": True,
                    "filename": safe_filename,
                    "message": f"Successfully uploaded {safe_filename} to repository workspace.",
                    "status": self.get_repo_status()
                }
            except Exception as e:
                response = {
                    "success": False,
                    "filename": safe_filename,
                    "message": f"Upload failed: {str(e)}",
                    "status": self.get_repo_status()
                }

            out_bytes = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out_bytes)))
            self.end_headers()
            self.wfile.write(out_bytes)
            return

        elif self.path == "/api/unstage":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            payload = json.loads(body)
            filename = payload.get("filename", "").strip()
            index_file = REPO_DIR / ".branchlite" / "index"
            if index_file.exists() and filename:
                lines = index_file.read_text(encoding="utf-8").splitlines()
                new_lines = [l for l in lines if not l.strip().endswith(" " + filename)]
                index_file.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
            response = {
                "success": True,
                "message": f"Unstaged {filename}",
                "status": self.get_repo_status()
            }
            out_bytes = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out_bytes)))
            self.end_headers()
            self.wfile.write(out_bytes)
            return

        elif self.path == "/api/snapshot":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            payload = json.loads(body) if body else {}
            files = self.get_snapshot_files(payload)
            label = self.get_source_label(payload)
            response = {
                "success": True,
                "source": payload,
                "label": label,
                "files": files
            }
            out_bytes = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out_bytes)))
            self.end_headers()
            self.wfile.write(out_bytes)
            return

        elif self.path == "/api/file_content":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            payload = json.loads(body) if body else {}
            filename = payload.get("file", "")
            content, blob_hash = self.get_file_content(payload, filename)
            if content is not None:
                lines = content.splitlines()
                response = {
                    "success": True,
                    "filename": filename,
                    "hash": blob_hash or "",
                    "size": len(content.encode("utf-8")),
                    "lines": len(lines),
                    "content": content
                }
            else:
                response = {
                    "success": False,
                    "filename": filename,
                    "message": f"File '{filename}' not found in specified source",
                    "content": ""
                }
            out_bytes = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out_bytes)))
            self.end_headers()
            self.wfile.write(out_bytes)
            return

        elif self.path == "/api/diff":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            payload = json.loads(body) if body else {}
            sourceA = payload.get("sourceA", {"type": "commit", "id": "HEAD"})
            sourceB = payload.get("sourceB", {"type": "working", "id": ""})
            target_file = payload.get("file")
            diff_data = self.compute_diff(sourceA, sourceB, target_file)
            out_bytes = json.dumps(diff_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out_bytes)))
            self.end_headers()
            self.wfile.write(out_bytes)
            return

        elif self.path == "/api/execute":
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
        ignored_names = {
            ".branchlite", ".git", ".vscode", "demo", "demo_branches", "include", "src", "gui", "ARCHITECTURE.png", ".gitignore"
        }
        working = []
        for f in REPO_DIR.iterdir():
            if f.name not in ignored_names and not f.name.endswith(".exe"):
                if f.is_file():
                    working.append(f.name)

        return {
            "initialized": True,
            "currentBranch": current_branch,
            "branches": branches,
            "commits": commits,
            "stagedFiles": staged,
            "workingFiles": sorted(working)
        }

    def get_source_label(self, source):
        stype = source.get("type", "working")
        sid = source.get("id", "")
        if stype == "branch":
            return f"Branch: {sid}"
        elif stype == "commit":
            return f"Commit: {sid[:7]}"
        elif stype == "staged":
            return "Staging Area (.branchlite/index)"
        elif stype == "working":
            return "Working Directory"
        elif stype == "blob":
            return f"Blob: {sid[:8]}"
        return f"{stype} {sid}"

    def get_snapshot_files(self, source):
        vcs_dir = REPO_DIR / ".branchlite"
        stype = source.get("type", "working")
        sid = source.get("id", "")

        files = []
        if stype == "blob":
            return []

        elif stype == "commit":
            commit_id = sid
            if commit_id == "HEAD":
                head_file = vcs_dir / "HEAD"
                curr_branch = head_file.read_text(encoding="utf-8").strip() if head_file.exists() else "main"
                branch_file = vcs_dir / "branches" / curr_branch
                commit_id = branch_file.read_text(encoding="utf-8").strip() if branch_file.exists() else ""
            if commit_id:
                commit_file = vcs_dir / "commits" / commit_id
                if commit_file.exists():
                    lines = commit_file.read_text(encoding="utf-8").splitlines()
                    in_files = False
                    for line in lines:
                        if in_files:
                            parts = line.strip().split(" ", 1)
                            if len(parts) == 2:
                                blob_path = vcs_dir / "objects" / parts[0]
                                sz = blob_path.stat().st_size if blob_path.exists() else 0
                                files.append({"file": parts[1], "hash": parts[0], "size": sz})
                        elif line.strip() == "files":
                            in_files = True

        elif stype == "branch":
            branch_file = vcs_dir / "branches" / sid
            if branch_file.exists():
                tip = branch_file.read_text(encoding="utf-8").strip()
                if tip:
                    return self.get_snapshot_files({"type": "commit", "id": tip})

        elif stype == "staged":
            index_file = vcs_dir / "index"
            if index_file.exists():
                for line in index_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        parts = line.strip().split(" ", 1)
                        if len(parts) == 2:
                            blob_path = vcs_dir / "objects" / parts[0]
                            sz = blob_path.stat().st_size if blob_path.exists() else 0
                            files.append({"file": parts[1], "hash": parts[0], "size": sz})

        elif stype == "working":
            ignored_names = {".branchlite", ".git", ".vscode", "demo", "demo_branches", "include", "src", "gui", "ARCHITECTURE.png", ".gitignore"}
            for f in sorted(REPO_DIR.iterdir()):
                if f.name not in ignored_names and not f.name.endswith(".exe") and f.is_file():
                    files.append({"file": f.name, "hash": "working", "size": f.stat().st_size})

        return files

    def read_file_safe(self, path):
        raw = path.read_bytes()
        if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
            try:
                return raw.decode('utf-16')
            except Exception:
                pass
        try:
            return raw.decode('utf-8')
        except Exception:
            return raw.decode('latin1', errors='replace')

    def get_file_content(self, source, filename):
        vcs_dir = REPO_DIR / ".branchlite"
        stype = source.get("type", "working")
        sid = source.get("id", "")

        if stype == "blob":
            p = vcs_dir / "objects" / sid
            if p.exists():
                content = self.read_file_safe(p)
                return content, sid
            return None, None

        elif stype == "commit":
            commit_id = sid
            if commit_id == "HEAD":
                head_file = vcs_dir / "HEAD"
                curr_branch = head_file.read_text(encoding="utf-8").strip() if head_file.exists() else "main"
                branch_file = vcs_dir / "branches" / curr_branch
                commit_id = branch_file.read_text(encoding="utf-8").strip() if branch_file.exists() else ""
            if commit_id:
                commit_file = vcs_dir / "commits" / commit_id
                if commit_file.exists():
                    lines = commit_file.read_text(encoding="utf-8").splitlines()
                    in_files = False
                    for line in lines:
                        if in_files:
                            parts = line.strip().split(" ", 1)
                            if len(parts) == 2 and parts[1] == filename:
                                blob_path = vcs_dir / "objects" / parts[0]
                                if blob_path.exists():
                                    return self.read_file_safe(blob_path), parts[0]
                        elif line.strip() == "files":
                            in_files = True
            return None, None

        elif stype == "branch":
            branch_file = vcs_dir / "branches" / sid
            if branch_file.exists():
                tip = branch_file.read_text(encoding="utf-8").strip()
                if tip:
                    return self.get_file_content({"type": "commit", "id": tip}, filename)
            return None, None

        elif stype == "staged":
            index_file = vcs_dir / "index"
            if index_file.exists():
                for line in index_file.read_text(encoding="utf-8").splitlines():
                    parts = line.strip().split(" ", 1)
                    if len(parts) == 2 and parts[1] == filename:
                        blob_path = vcs_dir / "objects" / parts[0]
                        if blob_path.exists():
                            return self.read_file_safe(blob_path), parts[0]
            return None, None

        elif stype == "working":
            p = REPO_DIR / filename
            if p.exists() and p.is_file():
                return self.read_file_safe(p), "working"
            return None, None

        return None, None

    def compute_diff(self, sourceA, sourceB, target_file=None):
        import difflib
        filesA = {f["file"]: f["hash"] for f in self.get_snapshot_files(sourceA)}
        filesB = {f["file"]: f["hash"] for f in self.get_snapshot_files(sourceB)}

        if target_file:
            all_files = [target_file]
        else:
            all_files = sorted(set(filesA.keys()) | set(filesB.keys()))

        diff_results = []
        for filename in all_files:
            contentA, hashA = self.get_file_content(sourceA, filename)
            contentB, hashB = self.get_file_content(sourceB, filename)

            if contentA is None and contentB is None:
                continue

            if contentA is not None and contentB is not None and contentA == contentB:
                if not target_file:
                    continue

            if contentA is None:
                status = "added"
            elif contentB is None:
                status = "deleted"
            elif contentA != contentB:
                status = "modified"
            else:
                status = "unchanged"

            linesA = (contentA or "").splitlines()
            linesB = (contentB or "").splitlines()

            matcher = difflib.SequenceMatcher(None, linesA, linesB)
            chunks = []
            added_cnt = 0
            deleted_cnt = 0

            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    for idx, line in enumerate(linesA[i1:i2]):
                        chunks.append({"type": "same", "line": line, "oldNum": i1 + idx + 1, "newNum": j1 + idx + 1})
                elif tag == 'delete':
                    for idx, line in enumerate(linesA[i1:i2]):
                        deleted_cnt += 1
                        chunks.append({"type": "del", "line": line, "oldNum": i1 + idx + 1, "newNum": None})
                elif tag == 'insert':
                    for idx, line in enumerate(linesB[j1:j2]):
                        added_cnt += 1
                        chunks.append({"type": "add", "line": line, "oldNum": None, "newNum": j1 + idx + 1})
                elif tag == 'replace':
                    for idx, line in enumerate(linesA[i1:i2]):
                        deleted_cnt += 1
                        chunks.append({"type": "del", "line": line, "oldNum": i1 + idx + 1, "newNum": None})
                    for idx, line in enumerate(linesB[j1:j2]):
                        added_cnt += 1
                        chunks.append({"type": "add", "line": line, "oldNum": None, "newNum": j1 + idx + 1})

            diff_results.append({
                "filename": filename,
                "status": status,
                "stats": {"added": added_cnt, "deleted": deleted_cnt},
                "hashA": hashA or "",
                "hashB": hashB or "",
                "chunks": chunks
            })

        return {
            "success": True,
            "sourceA_label": self.get_source_label(sourceA),
            "sourceB_label": self.get_source_label(sourceB),
            "files": diff_results
        }

if __name__ == "__main__":
    os.chdir(str(REPO_DIR))
    server = ThreadingHTTPServer(("", PORT), BranchLiteHandler)
    print(f"BranchLite GUI Server running at http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
