#!/usr/bin/env python3
"""
pass-browser Native Messaging Host

This native messaging host connects Chrome/Edge extensions to the 'pass' 
password manager. It handles communication via stdin/stdout using JSON messages.
"""

import sys
import json
import struct
import subprocess
import os
import re
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Configuration
DEFAULT_STORE_PATH = os.path.expanduser("~/.password-store")
PASS_EXECUTABLE_CANDIDATES = [
    "/opt/homebrew/bin/pass",
    "/usr/local/bin/pass",
    "/usr/bin/pass",
    "/bin/pass",
]

# Cache configuration
CACHE_DIR = Path.home() / ".cache" / "pass-browser"
URL_INDEX_CACHE_FILE = CACHE_DIR / "URLIndexCache.json"
URL_INDEX_LOCK_FILE = CACHE_DIR / "URLIndexRefresh.lock"


def log_message(message: str):
    """Log messages to stderr (since stdout is used for native messaging)"""
    print(f"[pass-browser-host] {message}", file=sys.stderr, flush=True)


def find_pass_executable() -> Optional[str]:
    """Find the pass executable"""
    # Try predefined locations first
    for candidate in PASS_EXECUTABLE_CANDIDATES:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    
    # Try to find in PATH
    try:
        result = subprocess.run(
            ["which", "pass"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            if path and os.path.isfile(path):
                return path
    except Exception:
        pass
    
    return None


def run_pass(args: List[str], env: Optional[Dict[str, str]] = None) -> str:
    """Execute pass command and return output"""
    pass_exec = find_pass_executable()
    if not pass_exec:
        raise RuntimeError("Unable to find the 'pass' executable")
    
    # Prepare environment
    cmd_env = os.environ.copy()
    
    # Fix PATH to include homebrew (Edge starts with limited PATH)
    if '/opt/homebrew/bin' not in cmd_env.get('PATH', ''):
        cmd_env['PATH'] = f"/opt/homebrew/bin:/usr/local/bin:{cmd_env.get('PATH', '/usr/bin:/bin')}"
    
    if env:
        cmd_env.update(env)
    
    # Set PASSWORD_STORE_DIR if not already set
    if "PASSWORD_STORE_DIR" not in cmd_env:
        cmd_env["PASSWORD_STORE_DIR"] = DEFAULT_STORE_PATH
    
    # Ensure GPG can find the agent
    if "GPG_AGENT_INFO" not in cmd_env:
        gpg_agent_socket = os.path.expanduser("~/.gnupg/S.gpg-agent")
        if os.path.exists(gpg_agent_socket):
            cmd_env["GPG_AGENT_INFO"] = f"{gpg_agent_socket}:0:1"
    
    # Set GPG_TTY to allow pinentry
    cmd_env["GPG_TTY"] = "/dev/tty"
    
    log_message(f"Running: {pass_exec} {' '.join(args)}")
    
    try:
        result = subprocess.run(
            [pass_exec] + args,
            capture_output=True,
            text=True,
            env=cmd_env,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Command failed"
            raise RuntimeError(f"pass command failed: {error_msg}")
        
        return result.stdout
    except subprocess.TimeoutExpired:
        raise RuntimeError("pass command timed out")
    except Exception as e:
        raise RuntimeError(f"Failed to execute pass: {str(e)}")


def parse_pass_entry(output: str, entry_name: str) -> Dict[str, Any]:
    """Parse pass entry output into structured data"""
    lines = output.split('\n')
    
    if not lines:
        return {
            "entry": entry_name,
            "password": "",
            "username": "",
            "url": "",
            "fields": [],
            "notes": ""
        }
    
    # First line is the password
    password = lines[0] if lines else ""
    
    # Parse metadata fields
    username = ""
    url = ""
    fields = []
    notes_lines = []
    in_notes = False
    
    for line in lines[1:]:
        line = line.rstrip()
        
        # Check for key: value format
        match = re.match(r'^([^:]+):\s*(.*)$', line)
        if match and not in_notes:
            key = match.group(1).strip().lower()
            value = match.group(2).strip()
            
            if key == "username" or key == "user" or key == "login":
                username = value
            elif key in ["url", "website", "site", "url2", "url3"]:
                if not url:  # Use first URL found
                    url = value
                # Also add to fields for additional URLs
                if value:
                    fields.append({"label": match.group(1).strip(), "value": value})
            else:
                if value:
                    fields.append({"label": match.group(1).strip(), "value": value})
        else:
            # Everything else goes to notes
            if not in_notes and line.strip():
                in_notes = True
            if in_notes:
                notes_lines.append(line)
    
    notes = '\n'.join(notes_lines).strip()
    
    return {
        "entry": entry_name,
        "password": password,
        "username": username,
        "url": url,
        "fields": fields,
        "notes": notes
    }


def get_otp_code(entry_name: str) -> Optional[Dict[str, Any]]:
    """Get OTP code for an entry using pass otp"""
    try:
        output = run_pass(["otp", entry_name])
        code = output.strip()
        
        if not code:
            return None
        
        # Try to get OTP URI to extract type and period
        otp_type = "totp"
        period = 30
        
        try:
            uri_output = run_pass(["otp", "uri", entry_name])
            uri = uri_output.strip()
            
            # Parse otpauth:// URI
            if uri.startswith("otpauth://"):
                if "totp" in uri.lower():
                    otp_type = "totp"
                elif "hotp" in uri.lower():
                    otp_type = "hotp"
                
                # Extract period parameter
                period_match = re.search(r'[?&]period=(\d+)', uri)
                if period_match:
                    period = int(period_match.group(1))
        except Exception:
            pass  # Use defaults if URI parsing fails
        
        return {
            "code": code,
            "type": otp_type,
            "period": period
        }
    except Exception as e:
        log_message(f"Failed to get OTP for {entry_name}: {e}")
        return None


def list_entries() -> List[str]:
    """List all password entries"""
    try:
        # Use find command which is more reliable than parsing tree output
        store_path = os.environ.get('PASSWORD_STORE_DIR', DEFAULT_STORE_PATH)
        store_path = os.path.expanduser(store_path)
        
        if not os.path.isdir(store_path):
            log_message(f"Password store not found at: {store_path}")
            return []
        
        entries = []
        
        # Walk through the password store directory
        for root, dirs, files in os.walk(store_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            for file in files:
                if file.endswith('.gpg'):
                    # Get the full path relative to store_path
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, store_path)
                    # Remove .gpg extension
                    entry_name = rel_path[:-4]
                    entries.append(entry_name)
        
        log_message(f"Found {len(entries)} entries")
        return sorted(entries)
    except Exception as e:
        log_message(f"Failed to list entries: {e}")
        return []


def update_entry(entry_name: str, content: str) -> None:
    """Create or update a pass entry"""
    try:
        # Use pass insert with --multiline and --force (to overwrite if exists)
        process = subprocess.Popen(
            [find_pass_executable(), "insert", "--multiline", "--force", entry_name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "PASSWORD_STORE_DIR": DEFAULT_STORE_PATH}
        )
        
        stdout, stderr = process.communicate(input=content, timeout=30)
        
        if process.returncode != 0:
            error_msg = stderr.strip() or stdout.strip() or "Command failed"
            raise RuntimeError(f"Failed to update entry: {error_msg}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("pass command timed out")
    except Exception as e:
        raise RuntimeError(f"Failed to update entry: {str(e)}")


def delete_entry(entry_name: str) -> None:
    """Delete a pass entry"""
    try:
        # Use pass rm with --force to skip confirmation
        run_pass(["rm", "--force", entry_name])
    except Exception as e:
        raise RuntimeError(f"Failed to delete entry: {str(e)}")


def sync_store() -> None:
    """Sync password store with git"""
    try:
        # Git pull
        run_pass(["git", "pull"])
        # Git push
        run_pass(["git", "push"])
    except Exception as e:
        raise RuntimeError(f"Failed to sync store: {str(e)}")


def copy_to_clipboard(text: str) -> None:
    """Copy text to clipboard using pass copy mechanism or pbcopy/xclip"""
    try:
        # Try pbcopy (macOS)
        if os.path.exists("/usr/bin/pbcopy"):
            subprocess.run(
                ["/usr/bin/pbcopy"],
                input=text.encode(),
                timeout=5
            )
            return
        
        # Try xclip (Linux)
        if subprocess.run(["which", "xclip"], capture_output=True).returncode == 0:
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text.encode(),
                timeout=5
            )
            return
        
        # Try xsel (Linux)
        if subprocess.run(["which", "xsel"], capture_output=True).returncode == 0:
            subprocess.run(
                ["xsel", "--clipboard", "--input"],
                input=text.encode(),
                timeout=5
            )
            return
        
        raise RuntimeError("No clipboard utility found (pbcopy, xclip, or xsel)")
    except Exception as e:
        raise RuntimeError(f"Failed to copy to clipboard: {str(e)}")


def extract_hostname(url_string: str) -> Optional[str]:
    """Extract normalized hostname from URL string"""
    if not url_string:
        return None
    
    try:
        from urllib.parse import urlparse
        
        # Add https:// if no protocol
        if '://' not in url_string:
            url_string = 'https://' + url_string
        
        parsed = urlparse(url_string)
        if parsed.hostname:
            hostname = parsed.hostname.lower()
            # Remove www. prefix
            if hostname.startswith('www.'):
                hostname = hostname[4:]
            return hostname
    except Exception:
        pass
    
    return None


def build_url_index() -> Dict[str, List[str]]:
    """Build URL index from password store entries"""
    try:
        # Load cache if it exists and is recent
        if URL_INDEX_CACHE_FILE.exists():
            cache_age = time.time() - URL_INDEX_CACHE_FILE.stat().st_mtime
            # Cache is valid for 1 hour
            if cache_age < 3600:
                with open(URL_INDEX_CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    log_message(f"Loaded URL index cache with {len(cache)} entries")
                    return cache
    except Exception as e:
        log_message(f"Failed to load URL index cache: {e}")
    
    # Build new index
    log_message("Building URL index...")
    url_index = {}  # hostname -> [entry_names]
    
    store_path = os.environ.get('PASSWORD_STORE_DIR', DEFAULT_STORE_PATH)
    store_path = os.path.expanduser(store_path)
    
    if not os.path.isdir(store_path):
        return url_index
    
    # Walk through entries
    for root, dirs, files in os.walk(store_path):
        if '.git' in dirs:
            dirs.remove('.git')
        
        for file in files:
            if file.endswith('.gpg'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, store_path)
                entry_name = rel_path[:-4]
                
                try:
                    # Get entry content
                    output = run_pass(["show", entry_name])
                    lines = output.split('\n')
                    
                    # Parse URL fields (skip first line which is the password)
                    for line in lines[1:]:
                        if ':' not in line:
                            continue
                        
                        parts = line.split(':', 1)
                        if len(parts) != 2:
                            continue
                        
                        label = parts[0].strip().lower()
                        value = parts[1].strip()
                        
                        # Check if it's a URL field
                        if any(label.startswith(prefix) for prefix in ['url', 'website', 'site']):
                            # Extract hostname
                            hostname = extract_hostname(value)
                            if hostname:
                                if hostname not in url_index:
                                    url_index[hostname] = []
                                if entry_name not in url_index[hostname]:
                                    url_index[hostname].append(entry_name)
                except Exception as e:
                    log_message(f"Failed to index {entry_name}: {e}")
                    continue
    
    # Save cache
    try:
        with open(URL_INDEX_CACHE_FILE, 'w') as f:
            json.dump(url_index, f)
        log_message(f"Saved URL index cache with {len(url_index)} hostnames")
    except Exception as e:
        log_message(f"Failed to save URL index cache: {e}")
    
    return url_index


def get_suggestions_for_url(page_url: str, all_entries: List[str]) -> List[str]:
    """Get password suggestions for a given URL"""
    if not page_url:
        return []
    
    # Extract hostname from page URL
    hostname = extract_hostname(page_url)
    if not hostname:
        return []
    
    log_message(f"Looking for suggestions for hostname: {hostname}")
    
    # Try to load URL index
    url_index = build_url_index()
    
    # Find entries for this hostname
    suggestions = []
    
    # Exact match
    if hostname in url_index:
        suggestions.extend(url_index[hostname])
    
    # Subdomain match (e.g., login.example.com matches example.com)
    for indexed_host, entries in url_index.items():
        if hostname.endswith('.' + indexed_host) or indexed_host.endswith('.' + hostname):
            suggestions.extend(entries)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for entry in suggestions:
        if entry not in seen and entry in all_entries:
            seen.add(entry)
            unique_suggestions.append(entry)
    
    log_message(f"Found {len(unique_suggestions)} suggestions")
    return unique_suggestions


def handle_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming message from extension"""
    command = message.get("command")
    
    log_message(f"Received command: {command}")
    
    try:
        if command == "listEntries":
            entries = list_entries()
            page_url = message.get("pageURL", "")
            
            # Get URL-based suggestions
            suggested_entries = get_suggestions_for_url(page_url, entries)
            
            return {
                "ok": True,
                "entries": entries,
                "suggestedEntries": suggested_entries,
                "urlIndexRefreshing": False
            }
        
        elif command == "getEntryDetails":
            entry_name = message.get("entry")
            if not entry_name:
                return {"ok": False, "error": "No entry specified"}
            
            # Get entry content
            output = run_pass(["show", entry_name])
            details = parse_pass_entry(output, entry_name)
            
            # Try to get OTP
            otp_info = get_otp_code(entry_name)
            if otp_info:
                details["otp"] = otp_info["code"]
                details["otpType"] = otp_info["type"]
                details["otpPeriod"] = otp_info["period"]
            else:
                details["otp"] = ""
                details["otpType"] = ""
                details["otpPeriod"] = 0
            
            return {
                "ok": True,
                **details
            }
        
        elif command == "getEntryOTP":
            entry_name = message.get("entry")
            if not entry_name:
                return {"ok": False, "error": "No entry specified"}
            
            otp_info = get_otp_code(entry_name)
            if not otp_info:
                return {"ok": False, "error": "No OTP configured for this entry"}
            
            return {
                "ok": True,
                "entry": entry_name,
                "otp": otp_info["code"],
                "otpType": otp_info["type"],
                "otpPeriod": otp_info["period"]
            }
        
        elif command == "updateEntry":
            entry_name = message.get("entry")
            content = message.get("content")
            
            if not entry_name:
                return {"ok": False, "error": "No entry specified"}
            if not content:
                return {"ok": False, "error": "No content provided"}
            
            update_entry(entry_name, content)
            
            return {
                "ok": True,
                "entry": entry_name
            }
        
        elif command == "deleteEntry":
            entry_name = message.get("entry")
            if not entry_name:
                return {"ok": False, "error": "No entry specified"}
            
            delete_entry(entry_name)
            
            return {
                "ok": True,
                "entry": entry_name
            }
        
        elif command == "syncStore":
            sync_store()
            return {"ok": True}
        
        elif command == "copyText":
            text = message.get("text")
            if not text:
                return {"ok": False, "error": "No text provided"}
            
            copy_to_clipboard(text)
            return {"ok": True}
        
        else:
            return {"ok": False, "error": f"Unknown command: {command}"}
    
    except Exception as e:
        log_message(f"Error handling command {command}: {e}")
        return {"ok": False, "error": str(e)}


def read_message():
    """Read a message from stdin (Chrome native messaging format)"""
    # Read the message length (4 bytes)
    raw_length = sys.stdin.buffer.read(4)
    
    if len(raw_length) == 0:
        return None
    
    # Unpack message length
    message_length = struct.unpack('=I', raw_length)[0]
    
    # Read the message
    message = sys.stdin.buffer.read(message_length).decode('utf-8')
    
    return json.loads(message)


def send_message(message: Dict[str, Any]):
    """Send a message to stdout (Chrome native messaging format)"""
    # Encode message
    encoded_message = json.dumps(message).encode('utf-8')
    
    # Write message length
    sys.stdout.buffer.write(struct.pack('=I', len(encoded_message)))
    
    # Write message
    sys.stdout.buffer.write(encoded_message)
    sys.stdout.buffer.flush()


def main():
    """Main loop for native messaging host"""
    log_message("Native messaging host started")
    
    # Ensure cache directory exists
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if pass is available
    pass_exec = find_pass_executable()
    if not pass_exec:
        log_message("ERROR: pass executable not found!")
        log_message(f"Searched in: {', '.join(PASS_EXECUTABLE_CANDIDATES)}")
        sys.exit(1)
    
    log_message(f"Found pass executable: {pass_exec}")
    
    # Main message loop
    while True:
        try:
            message = read_message()
            
            if message is None:
                log_message("No more messages, exiting")
                break
            
            response = handle_message(message)
            send_message(response)
            
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            try:
                send_message({"ok": False, "error": str(e)})
            except Exception:
                pass
            break
    
    log_message("Native messaging host stopped")


if __name__ == "__main__":
    main()
