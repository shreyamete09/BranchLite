import sqlite3
import os
import hashlib
import secrets
import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "collab_data"
STORAGE_DIR = DATA_DIR / "storage"
DB_PATH = DATA_DIR / "collaborate.db"

def get_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        avatar_color TEXT DEFAULT '#6366f1',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id1 TEXT NOT NULL,
        user_id2 TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id1, user_id2),
        FOREIGN KEY (user_id1) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id2) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS friend_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id TEXT NOT NULL,
        receiver_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', -- pending, accepted, rejected
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(sender_id, receiver_id),
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS repositories (
        id TEXT PRIMARY KEY,
        owner_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS files (
        id TEXT PRIMARY KEY,
        owner_id TEXT NOT NULL,
        repo_id TEXT,
        filename TEXT NOT NULL,
        current_blob_hash TEXT NOT NULL,
        content TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        is_private INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_updated_by TEXT NOT NULL,
        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE SET NULL,
        FOREIGN KEY (last_updated_by) REFERENCES users(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS file_shares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        shared_with_id TEXT NOT NULL,
        permission TEXT NOT NULL DEFAULT 'view', -- 'view' or 'edit'
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(file_id, shared_with_id),
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (shared_with_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS commits (
        id TEXT PRIMARY KEY,
        file_id TEXT NOT NULL,
        author_id TEXT NOT NULL,
        author_name TEXT NOT NULL,
        message TEXT NOT NULL,
        blob_hash TEXT NOT NULL,
        parent_id TEXT,
        diff_summary TEXT DEFAULT '',
        timestamp TEXT NOT NULL,
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        type TEXT NOT NULL,
        message TEXT NOT NULL,
        sender_id TEXT,
        related_id TEXT,
        is_read INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    conn.commit()
    conn.close()

# Password Security
def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    # PBKDF2 with SHA-256, 100,000 iterations
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    return key.hex(), salt

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    return secrets.compare_digest(key.hex(), expected_hash)

# Content Hashing (FNV-1a 64-bit to match BranchLite engine, plus SHA256 fallback)
def fnv1a64_hash(content: str) -> str:
    h = 14695981039346656037
    prime = 1099511628211
    mask = 0xFFFFFFFFFFFFFFFF
    for b in content.encode('utf-8'):
        h = (h ^ b) & mask
        h = (h * prime) & mask
    return f"{h:016x}"

# User Accounts
def register_user(username: str, display_name: str, password: str):
    username = username.strip().lower()
    display_name = display_name.strip()
    if not username or len(username) < 3:
        raise ValueError("Username must be at least 3 characters long.")
    if not password or len(password) < 4:
        raise ValueError("Password must be at least 4 characters long.")
    if not display_name:
        display_name = username

    # Generate user ID
    user_id = f"usr_{secrets.token_hex(6)}"
    pwd_hash, salt = hash_password(password)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    colors = ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"]
    avatar_color = colors[len(username) % len(colors)]

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (id, username, display_name, password_hash, salt, avatar_color, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, display_name, pwd_hash, salt, avatar_color, now)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Username '{username}' is already taken.")
    conn.close()

    return {
        "id": user_id,
        "username": username,
        "display_name": display_name,
        "avatar_color": avatar_color,
        "created_at": now
    }

def login_user(username: str, password: str):
    username = username.strip().lower()
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        conn.close()
        raise ValueError("Invalid username or password.")

    if not verify_password(password, row["salt"], row["password_hash"]):
        conn.close()
        raise ValueError("Invalid username or password.")

    token = secrets.token_hex(24)
    now = datetime.datetime.now(datetime.timezone.utc)
    expires = (now + datetime.timedelta(days=7)).isoformat()
    now_str = now.isoformat()

    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, row["id"], now_str, expires)
    )
    conn.commit()
    user_data = {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "avatar_color": row["avatar_color"],
        "created_at": row["created_at"]
    }
    conn.close()
    return {"token": token, "user": user_data}

def get_user_from_token(token: str):
    if not token:
        return None
    conn = get_db()
    row = conn.execute("""
        SELECT u.id, u.username, u.display_name, u.avatar_color, u.created_at, s.expires_at
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
    """, (token,)).fetchone()
    conn.close()
    if not row:
        return None
    
    # check expiry
    expires = datetime.datetime.fromisoformat(row["expires_at"])
    if datetime.datetime.now(datetime.timezone.utc) > expires:
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "avatar_color": row["avatar_color"],
        "created_at": row["created_at"]
    }

def logout_user(token: str):
    if not token:
        return
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def search_users(query: str, current_user_id: str):
    query = f"%{query.strip().lower()}%"
    conn = get_db()
    rows = conn.execute("""
        SELECT id, username, display_name, avatar_color
        FROM users
        WHERE id != ? AND (username LIKE ? OR display_name LIKE ?)
        LIMIT 20
    """, (current_user_id, query, query)).fetchall()

    # check friendship status
    results = []
    for r in rows:
        target_id = r["id"]
        # check if already friends
        friend_row = conn.execute("""
            SELECT id FROM friends 
            WHERE (user_id1 = ? AND user_id2 = ?) OR (user_id1 = ? AND user_id2 = ?)
        """, (current_user_id, target_id, target_id, current_user_id)).fetchone()

        # check if request pending
        req_row = conn.execute("""
            SELECT id, sender_id, status FROM friend_requests
            WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
        """, (current_user_id, target_id, target_id, current_user_id)).fetchone()

        relation = "none"
        if friend_row:
            relation = "friends"
        elif req_row:
            if req_row["status"] == "pending":
                relation = "outgoing_pending" if req_row["sender_id"] == current_user_id else "incoming_pending"
            elif req_row["status"] == "accepted":
                relation = "friends"

        results.append({
            "id": r["id"],
            "username": r["username"],
            "display_name": r["display_name"],
            "avatar_color": r["avatar_color"],
            "relation": relation,
            "requestId": req_row["id"] if req_row else None
        })

    conn.close()
    return results

# Friend Management
def send_friend_request(sender_id: str, receiver_username_or_id: str):
    conn = get_db()
    # Resolve target user
    receiver = conn.execute(
        "SELECT id, username FROM users WHERE id = ? OR username = ?",
        (receiver_username_or_id, receiver_username_or_id.lower())
    ).fetchone()

    if not receiver:
        conn.close()
        raise ValueError("User not found.")

    receiver_id = receiver["id"]
    if sender_id == receiver_id:
        conn.close()
        raise ValueError("You cannot send a friend request to yourself.")

    # Check if already friends
    friend = conn.execute("""
        SELECT id FROM friends 
        WHERE (user_id1 = ? AND user_id2 = ?) OR (user_id1 = ? AND user_id2 = ?)
    """, (sender_id, receiver_id, receiver_id, sender_id)).fetchone()
    if friend:
        conn.close()
        raise ValueError("You are already friends with this user.")

    # Check existing request
    existing = conn.execute("""
        SELECT id, sender_id, status FROM friend_requests
        WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
    """, (sender_id, receiver_id, receiver_id, sender_id)).fetchone()

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if existing:
        if existing["status"] == "pending":
            conn.close()
            if existing["sender_id"] == sender_id:
                raise ValueError("Friend request is already pending.")
            else:
                raise ValueError("This user has already sent you a request. Please accept it.")
        elif existing["status"] == "rejected":
            # Allow resending if previously rejected
            conn.execute("""
                UPDATE friend_requests SET sender_id = ?, receiver_id = ?, status = 'pending', updated_at = ?
                WHERE id = ?
            """, (sender_id, receiver_id, now, existing["id"]))
            req_id = existing["id"]
        else:
            conn.close()
            raise ValueError("Already friends.")
    else:
        cur = conn.execute("""
            INSERT INTO friend_requests (sender_id, receiver_id, status, created_at, updated_at)
            VALUES (?, ?, 'pending', ?, ?)
        """, (sender_id, receiver_id, now, now))
        req_id = cur.lastrowid

    # Create notification for receiver
    sender_info = conn.execute("SELECT username, display_name FROM users WHERE id = ?", (sender_id,)).fetchone()
    conn.execute("""
        INSERT INTO notifications (user_id, type, message, sender_id, related_id, is_read, created_at)
        VALUES (?, 'friend_request', ?, ?, ?, 0, ?)
    """, (receiver_id, f"{sender_info['display_name']} (@{sender_info['username']}) sent you a friend request.", sender_id, str(req_id), now))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Friend request sent successfully."}

def get_friend_requests(user_id: str):
    conn = get_db()
    # Incoming pending
    incoming = conn.execute("""
        SELECT r.id, r.sender_id, r.created_at, u.username, u.display_name, u.avatar_color
        FROM friend_requests r
        JOIN users u ON r.sender_id = u.id
        WHERE r.receiver_id = ? AND r.status = 'pending'
        ORDER BY r.created_at DESC
    """, (user_id,)).fetchall()

    # Outgoing pending
    outgoing = conn.execute("""
        SELECT r.id, r.receiver_id, r.created_at, u.username, u.display_name, u.avatar_color
        FROM friend_requests r
        JOIN users u ON r.receiver_id = u.id
        WHERE r.sender_id = ? AND r.status = 'pending'
        ORDER BY r.created_at DESC
    """, (user_id,)).fetchall()

    conn.close()
    return {
        "incoming": [dict(r) for r in incoming],
        "outgoing": [dict(r) for r in outgoing]
    }

def respond_friend_request(request_id: int, user_id: str, action: str):
    conn = get_db()
    req = conn.execute("SELECT * FROM friend_requests WHERE id = ?", (request_id,)).fetchone()
    if not req or req["receiver_id"] != user_id:
        conn.close()
        raise ValueError("Friend request not found or not authorized.")

    if req["status"] != "pending":
        conn.close()
        raise ValueError(f"Request is already {req['status']}.")

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if action == "accept":
        conn.execute("UPDATE friend_requests SET status = 'accepted', updated_at = ? WHERE id = ?", (now, request_id))
        # Add to friends table
        conn.execute("""
            INSERT OR IGNORE INTO friends (user_id1, user_id2, created_at)
            VALUES (?, ?, ?)
        """, (req["sender_id"], req["receiver_id"], now))

        # Notify sender
        user_info = conn.execute("SELECT username, display_name FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.execute("""
            INSERT INTO notifications (user_id, type, message, sender_id, related_id, is_read, created_at)
            VALUES (?, 'friend_accepted', ?, ?, ?, 0, ?)
        """, (req["sender_id"], f"{user_info['display_name']} accepted your friend request!", user_id, str(request_id), now))

    elif action == "reject":
        conn.execute("UPDATE friend_requests SET status = 'rejected', updated_at = ? WHERE id = ?", (now, request_id))
    else:
        conn.close()
        raise ValueError("Invalid action. Must be 'accept' or 'reject'.")

    conn.commit()
    conn.close()
    return {"success": True, "message": f"Friend request {action}ed."}

def get_friends(user_id: str):
    conn = get_db()
    rows = conn.execute("""
        SELECT u.id, u.username, u.display_name, u.avatar_color, f.created_at as friendship_date
        FROM friends f
        JOIN users u ON (u.id = CASE WHEN f.user_id1 = ? THEN f.user_id2 ELSE f.user_id1 END)
        WHERE f.user_id1 = ? OR f.user_id2 = ?
        ORDER BY u.display_name ASC
    """, (user_id, user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def remove_friend(user_id: str, friend_id: str):
    conn = get_db()
    conn.execute("""
        DELETE FROM friends 
        WHERE (user_id1 = ? AND user_id2 = ?) OR (user_id1 = ? AND user_id2 = ?)
    """, (user_id, friend_id, friend_id, user_id))
    # Also clean up friend requests
    conn.execute("""
        DELETE FROM friend_requests
        WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
    """, (user_id, friend_id, friend_id, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Friend removed."}

# Repositories & File Management
def create_repository(owner_id: str, name: str, description: str = ""):
    repo_id = f"repo_{secrets.token_hex(6)}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db()
    conn.execute("""
        INSERT INTO repositories (id, owner_id, name, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (repo_id, owner_id, name.strip(), description.strip(), now, now))
    conn.commit()
    conn.close()
    return {"id": repo_id, "name": name, "description": description, "created_at": now}

def get_user_repositories(owner_id: str):
    conn = get_db()
    rows = conn.execute("""
        SELECT r.*, COUNT(f.id) as file_count
        FROM repositories r
        LEFT JOIN files f ON r.id = f.repo_id
        WHERE r.owner_id = ?
        GROUP BY r.id
        ORDER BY r.updated_at DESC
    """, (owner_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def publish_file(owner_id: str, filename: str, content: str, repo_id: str = None):
    filename = Path(filename).name
    blob_hash = fnv1a64_hash(content)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    file_id = f"fil_{secrets.token_hex(6)}"

    conn = get_db()
    # Check if file with same name already exists for this owner and repo
    existing = conn.execute("""
        SELECT id FROM files WHERE owner_id = ? AND filename = ? AND (repo_id = ? OR (repo_id IS NULL AND ? IS NULL))
    """, (owner_id, filename, repo_id, repo_id)).fetchone()

    if existing:
        file_id = existing["id"]
        conn.execute("""
            UPDATE files 
            SET content = ?, current_blob_hash = ?, version = version + 1, updated_at = ?, last_updated_by = ?
            WHERE id = ?
        """, (content, blob_hash, now, owner_id, file_id))
    else:
        conn.execute("""
            INSERT INTO files (id, owner_id, repo_id, filename, current_blob_hash, content, version, is_private, created_at, updated_at, last_updated_by)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?)
        """, (file_id, owner_id, repo_id, filename, blob_hash, content, now, now, owner_id))

        # Initial commit
        commit_id = f"c_{blob_hash[:8]}"
        user_info = conn.execute("SELECT username FROM users WHERE id = ?", (owner_id,)).fetchone()
        conn.execute("""
            INSERT INTO commits (id, file_id, author_id, author_name, message, blob_hash, parent_id, diff_summary, timestamp)
            VALUES (?, ?, ?, ?, 'Initial commit', ?, NULL, 'Added file', ?)
        """, (commit_id, file_id, owner_id, user_info["username"], blob_hash, now))

    conn.commit()
    conn.close()
    return {"id": file_id, "filename": filename, "blob_hash": blob_hash}

def get_my_files(owner_id: str):
    conn = get_db()
    rows = conn.execute("""
        SELECT f.id, f.filename, f.current_blob_hash, f.version, f.is_private, f.created_at, f.updated_at,
               f.repo_id, r.name as repo_name,
               (SELECT COUNT(*) FROM file_shares fs WHERE fs.file_id = f.id) as share_count
        FROM files f
        LEFT JOIN repositories r ON f.repo_id = r.id
        WHERE f.owner_id = ?
        ORDER BY f.updated_at DESC
    """, (owner_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Selective Sharing and Permissions
# Permissions: 'private', 'view', 'edit'
def share_file(owner_id: str, file_id: str, friend_id: str, permission: str):
    if permission not in ('view', 'edit'):
        raise ValueError("Permission must be 'view' or 'edit'.")

    conn = get_db()
    # Check ownership
    f = conn.execute("SELECT * FROM files WHERE id = ? AND owner_id = ?", (file_id, owner_id)).fetchone()
    if not f:
        conn.close()
        raise ValueError("File not found or you are not the owner.")

    # Check friendship
    friend = conn.execute("""
        SELECT id FROM friends 
        WHERE (user_id1 = ? AND user_id2 = ?) OR (user_id1 = ? AND user_id2 = ?)
    """, (owner_id, friend_id, friend_id, owner_id)).fetchone()
    if not friend:
        conn.close()
        raise ValueError("You can only share files with your friends.")

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    # Upsert share
    conn.execute("""
        INSERT INTO file_shares (file_id, owner_id, shared_with_id, permission, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(file_id, shared_with_id) DO UPDATE SET permission = ?, updated_at = ?
    """, (file_id, owner_id, friend_id, permission, now, now, permission, now))

    # Mark file as not private anymore (it is shared)
    conn.execute("UPDATE files SET is_private = 0 WHERE id = ?", (file_id,))

    # Notify friend
    owner_info = conn.execute("SELECT username, display_name FROM users WHERE id = ?", (owner_id,)).fetchone()
    perm_label = "Can Edit" if permission == 'edit' else "View Only"
    conn.execute("""
        INSERT INTO notifications (user_id, type, message, sender_id, related_id, is_read, created_at)
        VALUES (?, 'file_shared', ?, ?, ?, 0, ?)
    """, (friend_id, f"{owner_info['display_name']} shared '{f['filename']}' with you ({perm_label}).", owner_id, file_id, now))

    conn.commit()
    conn.close()
    return {"success": True, "message": f"File shared with {permission} permission."}

def revoke_share(owner_id: str, file_id: str, shared_with_id: str):
    conn = get_db()
    conn.execute("""
        DELETE FROM file_shares WHERE file_id = ? AND owner_id = ? AND shared_with_id = ?
    """, (file_id, owner_id, shared_with_id))

    # If no more shares, mark file as private
    remaining = conn.execute("SELECT COUNT(*) as count FROM file_shares WHERE file_id = ?", (file_id,)).fetchone()["count"]
    if remaining == 0:
        conn.execute("UPDATE files SET is_private = 1 WHERE id = ?", (file_id,))

    # Notify user that access was revoked
    f = conn.execute("SELECT filename FROM files WHERE id = ?", (file_id,)).fetchone()
    if f:
        owner_info = conn.execute("SELECT display_name FROM users WHERE id = ?", (owner_id,)).fetchone()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn.execute("""
            INSERT INTO notifications (user_id, type, message, sender_id, related_id, is_read, created_at)
            VALUES (?, 'permission_revoked', ?, ?, ?, 0, ?)
        """, (shared_with_id, f"{owner_info['display_name']} revoked your access to '{f['filename']}'.", owner_id, file_id, now))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Access revoked successfully."}

def get_file_shares(owner_id: str, file_id: str):
    conn = get_db()
    rows = conn.execute("""
        SELECT fs.id as share_id, fs.permission, fs.created_at, fs.updated_at,
               u.id as user_id, u.username, u.display_name, u.avatar_color
        FROM file_shares fs
        JOIN users u ON fs.shared_with_id = u.id
        WHERE fs.file_id = ? AND fs.owner_id = ?
        ORDER BY fs.created_at DESC
    """, (file_id, owner_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_shared_by_me(owner_id: str):
    conn = get_db()
    rows = conn.execute("""
        SELECT fs.id as share_id, fs.permission, fs.created_at, fs.updated_at,
               f.id as file_id, f.filename, f.version, f.current_blob_hash,
               u.id as shared_with_id, u.username as shared_with_username,
               u.display_name as shared_with_display_name, u.avatar_color as shared_with_avatar
        FROM file_shares fs
        JOIN files f ON fs.file_id = f.id
        JOIN users u ON fs.shared_with_id = u.id
        WHERE fs.owner_id = ?
        ORDER BY fs.updated_at DESC
    """, (owner_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_shared_with_me(user_id: str):
    conn = get_db()
    rows = conn.execute("""
        SELECT fs.id as share_id, fs.permission, fs.created_at as shared_at,
               f.id as file_id, f.filename, f.version, f.current_blob_hash, f.updated_at,
               u.id as owner_id, u.username as owner_username,
               u.display_name as owner_display_name, u.avatar_color as owner_avatar,
               last_u.username as last_contributor_username
        FROM file_shares fs
        JOIN files f ON fs.file_id = f.id
        JOIN users u ON f.owner_id = u.id
        LEFT JOIN users last_u ON f.last_updated_by = last_u.id
        WHERE fs.shared_with_id = ?
        ORDER BY f.updated_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_file_permission(user_id: str, file_id: str):
    conn = get_db()
    f = conn.execute("SELECT owner_id FROM files WHERE id = ?", (file_id,)).fetchone()
    if not f:
        conn.close()
        return None
    if f["owner_id"] == user_id:
        conn.close()
        return "owner"

    share = conn.execute("SELECT permission FROM file_shares WHERE file_id = ? AND shared_with_id = ?", (file_id, user_id)).fetchone()
    conn.close()
    if share:
        return share["permission"] # 'view' or 'edit'
    return None

def get_file_details(user_id: str, file_id: str):
    perm = get_file_permission(user_id, file_id)
    if not perm:
        raise PermissionError("Access denied. You do not have permission to access this file.")

    conn = get_db()
    row = conn.execute("""
        SELECT f.*, u.username as owner_username, u.display_name as owner_display_name,
               last_u.username as last_editor_username
        FROM files f
        JOIN users u ON f.owner_id = u.id
        LEFT JOIN users last_u ON f.last_updated_by = last_u.id
        WHERE f.id = ?
    """, (file_id,)).fetchone()
    conn.close()

    data = dict(row)
    data["user_permission"] = perm
    return data

# Collaborative Commit, Conflict Detection & Version Control
def record_collaborative_commit(user_id: str, file_id: str, message: str, new_content: str, base_blob_hash: str):
    perm = get_file_permission(user_id, file_id)
    if perm not in ("owner", "edit"):
        raise PermissionError("Access denied. You must have 'Can Edit' or 'Owner' permission to commit changes.")

    message = message.strip()
    if not message:
        message = "Update shared file"

    conn = get_db()
    file_row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    if not file_row:
        conn.close()
        raise ValueError("File not found.")

    current_hash = file_row["current_blob_hash"]
    # CONFLICT DETECTION:
    # If the base hash provided by the contributor doesn't match the current blob hash on the server,
    # another user committed changes in the meantime!
    if base_blob_hash and base_blob_hash != current_hash:
        conn.close()
        return {
            "conflict": True,
            "message": "Conflict detected! The file has been modified by another contributor since you last synced.",
            "server_blob_hash": current_hash,
            "server_content": file_row["content"],
            "your_base_hash": base_blob_hash
        }

    new_hash = fnv1a64_hash(new_content)
    if new_hash == current_hash:
        conn.close()
        return {
            "conflict": False,
            "unchanged": True,
            "message": "No changes detected.",
            "blob_hash": current_hash,
            "version": file_row["version"]
        }

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_version = file_row["version"] + 1
    commit_id = f"c_{new_hash[:8]}_{secrets.token_hex(3)}"

    # Get author user details
    author = conn.execute("SELECT username, display_name FROM users WHERE id = ?", (user_id,)).fetchone()
    author_name = author["username"]

    # Compute a quick line-diff summary
    old_lines = file_row["content"].splitlines()
    new_lines = new_content.splitlines()
    added = max(0, len(new_lines) - len(old_lines))
    diff_summary = f"+{added} lines, v{new_version}"

    # Get parent commit
    parent_commit = conn.execute("""
        SELECT id FROM commits WHERE file_id = ? ORDER BY timestamp DESC LIMIT 1
    """, (file_id,)).fetchone()
    parent_id = parent_commit["id"] if parent_commit else None

    # Update file record
    conn.execute("""
        UPDATE files 
        SET content = ?, current_blob_hash = ?, version = ?, updated_at = ?, last_updated_by = ?
        WHERE id = ?
    """, (new_content, new_hash, new_version, now, user_id, file_id))

    # Insert commit record
    conn.execute("""
        INSERT INTO commits (id, file_id, author_id, author_name, message, blob_hash, parent_id, diff_summary, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (commit_id, file_id, user_id, author_name, message, new_hash, parent_id, diff_summary, now))

    # Notify file owner if someone else committed
    if file_row["owner_id"] != user_id:
        conn.execute("""
            INSERT INTO notifications (user_id, type, message, sender_id, related_id, is_read, created_at)
            VALUES (?, 'file_committed', ?, ?, ?, 0, ?)
        """, (file_row["owner_id"], f"{author['display_name']} (@{author_name}) committed changes to '{file_row['filename']}': \"{message}\"", user_id, file_id, now))

    # Notify other shared users with edit permissions
    shares = conn.execute("SELECT shared_with_id FROM file_shares WHERE file_id = ? AND shared_with_id != ? AND shared_with_id != ?", 
                          (file_id, user_id, file_row["owner_id"])).fetchall()
    for s in shares:
        conn.execute("""
            INSERT INTO notifications (user_id, type, message, sender_id, related_id, is_read, created_at)
            VALUES (?, 'file_committed', ?, ?, ?, 0, ?)
        """, (s["shared_with_id"], f"{author['display_name']} updated shared file '{file_row['filename']}'.", user_id, file_id, now))

    conn.commit()
    conn.close()

    return {
        "conflict": False,
        "success": True,
        "commit_id": commit_id,
        "blob_hash": new_hash,
        "version": new_version,
        "author": author_name,
        "message": message,
        "timestamp": now
    }

def get_file_commits(user_id: str, file_id: str):
    perm = get_file_permission(user_id, file_id)
    if not perm:
        raise PermissionError("Access denied.")

    conn = get_db()
    commits = conn.execute("""
        SELECT c.*, u.display_name as author_display_name, u.avatar_color as author_avatar
        FROM commits c
        JOIN users u ON c.author_id = u.id
        WHERE c.file_id = ?
        ORDER BY c.timestamp DESC
    """, (file_id,)).fetchall()
    conn.close()
    return [dict(c) for r in commits for c in [dict(r)]]

def get_contributors_summary(user_id: str):
    conn = get_db()
    # Find all files owned by user or shared with user
    rows = conn.execute("""
        SELECT c.author_id, u.username, u.display_name, u.avatar_color,
               COUNT(c.id) as commit_count,
               MAX(c.timestamp) as last_active,
               GROUP_CONCAT(DISTINCT f.filename) as files_contributed
        FROM commits c
        JOIN users u ON c.author_id = u.id
        JOIN files f ON c.file_id = f.id
        WHERE f.owner_id = ? OR f.id IN (SELECT file_id FROM file_shares WHERE shared_with_id = ?)
        GROUP BY c.author_id
        ORDER BY commit_count DESC
    """, (user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Notifications
def get_user_notifications(user_id: str):
    conn = get_db()
    rows = conn.execute("""
        SELECT n.*, u.username as sender_username, u.display_name as sender_display_name, u.avatar_color as sender_avatar
        FROM notifications n
        LEFT JOIN users u ON n.sender_id = u.id
        WHERE n.user_id = ?
        ORDER BY n.created_at DESC
        LIMIT 50
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_notification_read(user_id: str, notif_id: int):
    conn = get_db()
    if notif_id == -1:
        # Mark all as read
        conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    else:
        conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notif_id, user_id))
    conn.commit()
    conn.close()
    return {"success": True}

# Initialize database on module load
init_db()
