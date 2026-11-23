from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import subprocess
import json
import os
import sys
import shutil
import base64
import urllib.parse
from pathlib import Path

# Add gui directory to path so collaborate_db can be imported directly
sys.path.insert(0, str(Path(__file__).resolve().parent))
import collaborate_db as db

PORT = 5000
REPO_DIR = Path(__file__).resolve().parent.parent
BRANCHLITE_EXE = REPO_DIR / "branchlite.exe"

class BranchLiteHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Collab-Token')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        out_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out_bytes)))
        self.end_headers()
        self.wfile.write(out_bytes)

    def read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length <= 0:
            return {}
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            return json.loads(body)
        except Exception:
            return {}

    def get_auth_user(self):
        token = None
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
        if not token:
            token = self.headers.get('X-Collab-Token', '').strip()
        if not token:
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'token' in qs:
                token = qs['token'][0].strip()
        if not token:
            return None
        return db.get_user_from_token(token)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        # ─── EXISTING ROUTES ───────────────────────────────────────────
        if path == "/" or path == "/index.html":
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

        elif path == "/api/status":
            status_data = self.get_repo_status()
            self.send_json(status_data)
            return

        # ─── COLLABORATE GET ROUTES ────────────────────────────────────
        elif path == "/api/auth/me":
            user = self.get_auth_user()
            if not user:
                self.send_json({"authenticated": False, "user": None})
            else:
                self.send_json({"authenticated": True, "user": user})
            return

        elif path == "/api/friends/search":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            q = qs.get("q", [""])[0]
            results = db.search_users(q, user["id"])
            self.send_json({"success": True, "users": results})
            return

        elif path == "/api/friends/list":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            friends = db.get_friends(user["id"])
            self.send_json({"success": True, "friends": friends})
            return

        elif path == "/api/friends/requests":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            reqs = db.get_friend_requests(user["id"])
            self.send_json({"success": True, "requests": reqs})
            return

        elif path == "/api/collab/my_files":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            files = db.get_my_files(user["id"])
            self.send_json({"success": True, "files": files})
            return

        elif path == "/api/collab/shared_with_me":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            files = db.get_shared_with_me(user["id"])
            self.send_json({"success": True, "files": files})
            return

        elif path == "/api/collab/shared_by_me":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            shares = db.get_shared_by_me(user["id"])
            self.send_json({"success": True, "shares": shares})
            return

        elif path == "/api/collab/file_detail":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            file_id = qs.get("file_id", [""])[0]
            if not file_id:
                self.send_json({"error": "Missing file_id"}, 400)
                return
            try:
                details = db.get_file_details(user["id"], file_id)
                self.send_json({"success": True, "file": details})
            except PermissionError as pe:
                self.send_json({"error": str(pe)}, 403)
            except Exception as e:
                self.send_json({"error": str(e)}, 400)
            return

        elif path == "/api/collab/shares":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            file_id = qs.get("file_id", [""])[0]
            if not file_id:
                self.send_json({"error": "Missing file_id"}, 400)
                return
            shares = db.get_file_shares(user["id"], file_id)
            self.send_json({"success": True, "shares": shares})
            return

        elif path == "/api/collab/history":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            file_id = qs.get("file_id", [""])[0]
            if not file_id:
                self.send_json({"error": "Missing file_id"}, 400)
                return
            try:
                commits = db.get_file_commits(user["id"], file_id)
                self.send_json({"success": True, "commits": commits})
            except PermissionError as pe:
                self.send_json({"error": str(pe)}, 403)
            except Exception as e:
                self.send_json({"error": str(e)}, 400)
            return

        elif path == "/api/collab/repos":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            repos = db.get_user_repositories(user["id"])
            self.send_json({"success": True, "repositories": repos})
            return

        elif path == "/api/collab/contributors":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            contributors = db.get_contributors_summary(user["id"])
            self.send_json({"success": True, "contributors": contributors})
            return

        elif path == "/api/notifications/list":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            notifs = db.get_user_notifications(user["id"])
            unread_count = sum(1 for n in notifs if not n["is_read"])
            self.send_json({"success": True, "notifications": notifs, "unread_count": unread_count})
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

        # ─── COLLABORATE POST ROUTES ───────────────────────────────────
        elif self.path == "/api/auth/register":
            payload = self.read_json_body()
            username = payload.get("username", "").strip()
            display_name = payload.get("display_name", "").strip()
            password = payload.get("password", "")
            try:
                user = db.register_user(username, display_name, password)
                login_info = db.login_user(username, password)
                self.send_json({"success": True, "token": login_info["token"], "user": login_info["user"]})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/auth/login":
            payload = self.read_json_body()
            username = payload.get("username", "").strip()
            password = payload.get("password", "")
            try:
                login_info = db.login_user(username, password)
                self.send_json({"success": True, "token": login_info["token"], "user": login_info["user"]})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/auth/logout":
            payload = self.read_json_body()
            token = payload.get("token") or self.headers.get("Authorization", "").replace("Bearer ", "").strip()
            if token:
                db.logout_user(token)
            self.send_json({"success": True, "message": "Logged out."})
            return

        elif self.path == "/api/friends/request":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            target_user = payload.get("target_user", "").strip()
            try:
                res = db.send_friend_request(user["id"], target_user)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/friends/respond":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            request_id = payload.get("request_id")
            action = payload.get("action", "")
            try:
                res = db.respond_friend_request(int(request_id), user["id"], action)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/friends/remove":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            friend_id = payload.get("friend_id", "")
            try:
                res = db.remove_friend(user["id"], friend_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/collab/repo_create":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            name = payload.get("name", "").strip()
            description = payload.get("description", "").strip()
            if not name:
                self.send_json({"success": False, "error": "Repository name is required"}, 400)
                return
            res = db.create_repository(user["id"], name, description)
            self.send_json({"success": True, "repository": res})
            return

        elif self.path == "/api/collab/publish_local":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            filename = payload.get("filename", "").strip()
            repo_id = payload.get("repo_id")
            target_path = REPO_DIR / filename
            if not target_path.exists() or not target_path.is_file():
                self.send_json({"success": False, "error": f"Local file '{filename}' does not exist."}, 404)
                return
            try:
                content = self.read_file_safe(target_path)
                res = db.publish_file(user["id"], filename, content, repo_id)
                self.send_json({"success": True, "file": res, "message": f"Published '{filename}' to BranchLite Collaborate!"})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/collab/publish_new":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            filename = payload.get("filename", "").strip()
            content = payload.get("content", "")
            repo_id = payload.get("repo_id")
            if not filename:
                self.send_json({"success": False, "error": "Filename is required"}, 400)
                return
            try:
                res = db.publish_file(user["id"], filename, content, repo_id)
                self.send_json({"success": True, "file": res, "message": f"Created '{filename}' in BranchLite Collaborate."})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/collab/share":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            file_id = payload.get("file_id")
            friend_id = payload.get("friend_id")
            permission = payload.get("permission", "view")
            try:
                res = db.share_file(user["id"], file_id, friend_id, permission)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/collab/revoke":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            file_id = payload.get("file_id")
            shared_with_id = payload.get("shared_with_id")
            try:
                res = db.revoke_share(user["id"], file_id, shared_with_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/collab/commit":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            file_id = payload.get("file_id")
            message = payload.get("message", "Collaborator commit")
            content = payload.get("content", "")
            base_blob_hash = payload.get("base_blob_hash", "")
            try:
                res = db.record_collaborative_commit(user["id"], file_id, message, content, base_blob_hash)
                self.send_json(res)
            except PermissionError as pe:
                self.send_json({"success": False, "error": str(pe)}, 403)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/collab/sync_to_local":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            file_id = payload.get("file_id")
            try:
                details = db.get_file_details(user["id"], file_id)
                filename = details["filename"]
                safe_name = Path(filename).name
                dest = REPO_DIR / safe_name
                dest.write_text(details["content"], encoding="utf-8")
                self.send_json({
                    "success": True,
                    "filename": safe_name,
                    "message": f"Successfully synced '{safe_name}' to local BranchLite workspace.",
                    "status": self.get_repo_status()
                })
            except PermissionError as pe:
                self.send_json({"success": False, "error": str(pe)}, 403)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        elif self.path == "/api/notifications/read":
            user = self.get_auth_user()
            if not user:
                self.send_json({"error": "Unauthorized"}, 401)
                return
            payload = self.read_json_body()
            notif_id = payload.get("notif_id", -1)
            res = db.mark_notification_read(user["id"], int(notif_id))
            self.send_json(res)
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
