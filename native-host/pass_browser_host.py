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
    if env:
        cmd_env.update(env)
    
    # Set PASSWORD_STORE_DIR if not already set
    if "PASSWORD_STORE_DIR" not in cmd_env:
        cmd_env["PASSWORD_STORE_DIR"] = DEFAULT_STORE_PATH
    
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
        output = run_pass(["ls"])
        
        # Parse the tree output to extract entry names
        entries = []
        lines = output.split('\n')
        
        for line in lines:
            # Remove tree characters and colors
            cleaned = re.sub(r'^[│├└─\s]+', '', line)
            cleaned = re.sub(r'\x1b\[[0-9;]*m', '', cleaned)  # Remove ANSI colors
            cleaned = cleaned.strip()
            
            # Skip empty lines and the store path line
            if not cleaned or cleaned.startswith('Password Store'):
                continue
            
            # Remove .gpg extension if present
            if cleaned.endswith('.gpg'):
                cleaned = cleaned[:-4]
            
            # Skip directory entries (they don't end with .gpg in the output)
            if cleaned and not cleaned.endswith('/'):
                entries.append(cleaned)
        
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


def handle_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming message from extension"""
    command = message.get("command")
    
    log_message(f"Received command: {command}")
    
    try:
        if command == "listEntries":
            entries = list_entries()
            page_url = message.get("pageURL", "")
            
            # TODO: Implement URL-based suggestions from cache
            suggested_entries = []
            
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
