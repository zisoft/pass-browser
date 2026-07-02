# pass-browser

A Chrome/Edge/Chromium extension for the [pass](https://www.passwordstore.org/) standard Unix password manager.

Ported from the Safari extension [pass-safari](https://github.com/yourusername/pass-safari).

## Features

- 🔐 Manage your pass password store from Chrome/Edge
- ➕ Create / update / delete entries
- 🎯 Auto-suggest passwords based on the current URL
- 🔢 Support for TOTP/OTP codes (requires pass-otp)
- 🎲 Integrated password generator
- 🔄 Sync the store with git
- 🔒 Secure architecture with native messaging
- 🌍 Cross-platform: Linux, macOS, Windows (where pass is available)

## Architecture

```
Browser Extension ←→ Native Messaging ←→ Python Host ←→ pass CLI
    (Sandboxed)         (JSON/stdio)      (Native)      (GPG)
```

The extension communicates with a native Python script that executes `pass` commands. This approach ensures:
- Security: Extension runs in browser sandbox
- Compatibility: Works with standard `pass` installation
- No network access required
- No telemetry or tracking

## Requirements

### All Platforms
- [pass](https://www.passwordstore.org/) password manager installed and configured
- Python 3.6 or later
- Chrome, Chromium, or Edge browser

### Optional
- [pass-otp](https://github.com/tadfisher/pass-otp) for OTP/2FA support
- git (for syncing password store)

### Installation of pass

**macOS:**
```bash
brew install pass
# Optional: OTP support
brew install pass-otp
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install pass
# Optional: OTP support
sudo apt-get install pass-extension-otp
```

**Linux (Fedora):**
```bash
sudo dnf install pass
```

**Windows:**
Pass is primarily designed for Unix-like systems. For Windows, consider using:
- WSL (Windows Subsystem for Linux)
- Or alternatives like [gopass](https://github.com/gopasspw/gopass)

## Installation

### 1. Clone or Download this Repository

```bash
git clone https://github.com/yourusername/pass-browser.git
cd pass-browser
```

### 2. Install the Native Messaging Host

**macOS/Linux:**
```bash
cd native-host
./install.sh
```

**Windows:**
```batch
cd native-host
install.bat
```

This will:
- Install the Python host script to `~/.local/share/pass-browser/`
- Install the native messaging manifest for Chrome/Edge

### 3. Load the Extension

1. Open your browser's extensions page:
   - **Chrome**: `chrome://extensions/`
   - **Edge**: `edge://extensions/`
   - **Chromium**: `chromium://extensions/`

2. Enable **Developer mode** (toggle in top-right corner)

3. Click **Load unpacked**

4. Select the `extension` folder from this repository

5. **Note the Extension ID** (something like `abcdefghijklmnopqrstuvwxyz123456`)

### 4. Configure Native Messaging Manifest

Edit the native messaging manifest file and replace `EXTENSION_ID` with your actual extension ID from step 3:

**macOS:**
```bash
# For Chrome:
nano ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/de.zisoft.pass_browser.json

# For Edge:
nano ~/Library/Application\ Support/Microsoft\ Edge/NativeMessagingHosts/de.zisoft.pass_browser.json
```

**Linux:**
```bash
# For Chrome:
nano ~/.config/google-chrome/NativeMessagingHosts/de.zisoft.pass_browser.json

# For Edge:
nano ~/.config/microsoft-edge/NativeMessagingHosts/de.zisoft.pass_browser.json
```

**Windows:**
```batch
# For Chrome:
notepad %LOCALAPPDATA%\Google\Chrome\User Data\NativeMessagingHosts\de.zisoft.pass_browser.json

# For Edge:
notepad %LOCALAPPDATA%\Microsoft\Edge\User Data\NativeMessagingHosts\de.zisoft.pass_browser.json
```

Change this line:
```json
"chrome-extension://EXTENSION_ID/"
```

To your actual extension ID:
```json
"chrome-extension://abcdefghijklmnopqrstuvwxyz123456/"
```

### 5. Restart Your Browser

After updating the manifest, completely restart your browser for the changes to take effect.

## Usage

### First Time Setup

1. Make sure you have a configured password store at `~/.password-store`
2. Click the pass-browser extension icon in your browser toolbar
3. The extension will load your password entries

### Daily Use

1. **Navigate to a website**
2. **Click the extension icon**
3. **Select a password entry** from the list
4. **Click to autofill** or use the autofill button

The extension will:
- Show suggested passwords based on the URL
- Autofill username and password fields
- Handle OTP codes if configured
- Copy credentials to clipboard

### Keyboard Shortcuts

- **Enter**: Autofill the selected entry
- **Arrow keys**: Navigate entries
- **Type to search**: Filter entries

### Creating New Entries

1. Click the **+** button in the extension popup
2. Fill in the details (title, password, username, URL)
3. Use the password generator if needed
4. Click **Save**

### Editing Entries

1. Click the **edit icon** next to an entry
2. Modify the fields
3. Click **Save**

### Syncing with Git

Click the **sync icon** (🔄) in the extension to pull and push changes to your git remote.

## URL Matching

The extension suggests passwords based on:
- Exact hostname matches
- Subdomain matches  
- URL fields in password entries

**Supported URL field formats in pass entries:**
```
password123
username: myuser
url: https://example.com
url2: https://login.example.com
website: https://example.com
site: https://example.com
```

All fields starting with `url`, `website`, or `site` are indexed for matching.

## Password Entry Format

pass-browser recognizes the standard pass format:

```
<password>
username: <username>
url: <url>
<custom-field>: <value>
<notes>
```

**Example:**
```
MySecurePassword123!
username: john.doe
url: https://example.com
email: john@example.com
This is a note about this password
```

## OTP/2FA Support

If you have `pass-otp` installed, the extension will automatically detect and display OTP codes.

**Add OTP to an entry:**
```bash
pass otp append example.com
```

The extension will:
- Display the current OTP code
- Auto-refresh codes every 30 seconds (for TOTP)
- Autofill OTP fields in web forms

## Troubleshooting

### Extension shows "Unable to connect to native messaging host"

1. **Check if the native host is installed:**
   ```bash
   ls ~/.local/share/pass-browser/pass_browser_host.py
   ```

2. **Check if Python is working:**
   ```bash
   python3 --version
   ```

3. **Check the manifest file exists and has correct path:**
   
   **macOS/Linux:**
   ```bash
   cat ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/de.zisoft.pass_browser.json
   # or
   cat ~/.config/google-chrome/NativeMessagingHosts/de.zisoft.pass_browser.json
   ```

4. **Check browser console for errors:**
   - Right-click extension icon → Inspect popup
   - Check Console tab for error messages

5. **Check native host logs:**
   
   The native host logs to stderr. To see logs:
   
   **Test the host manually:**
   ```bash
   echo '{"command":"listEntries","pageURL":""}' | python3 ~/.local/share/pass-browser/pass_browser_host.py
   ```

### Pass executable not found

Make sure `pass` is in your PATH:
```bash
which pass
```

The native host looks in these locations:
- `/opt/homebrew/bin/pass` (macOS with Homebrew)
- `/usr/local/bin/pass`
- `/usr/bin/pass`
- `/bin/pass`
- Or via `PATH`

### No entries showing up

1. **Check your password store:**
   ```bash
   pass ls
   ```

2. **Make sure `PASSWORD_STORE_DIR` is correct** (default: `~/.password-store`)

3. **Check permissions:**
   ```bash
   ls -la ~/.password-store
   ```

### OTP codes not working

1. **Make sure pass-otp is installed:**
   ```bash
   pass otp --version
   ```

2. **Check if OTP is configured for the entry:**
   ```bash
   pass otp uri example.com
   ```

## Development

### Project Structure

```
pass-browser/
├── extension/              # Browser extension
│   ├── manifest.json       # Extension manifest
│   ├── popup.html          # Popup UI
│   ├── popup.js            # Popup logic
│   ├── popup.css           # Popup styles
│   ├── background.js       # Background service worker
│   ├── content.js          # Content script for autofill
│   └── images/             # Icons
├── native-host/            # Native messaging host
│   ├── pass_browser_host.py           # Main host script
│   ├── de.zisoft.pass_browser.json    # Manifest (Unix)
│   ├── de.zisoft.pass_browser.windows.json  # Manifest (Windows)
│   ├── install.sh          # Install script (Unix)
│   └── install.bat         # Install script (Windows)
└── README.md
```

### Testing

1. **Test the native host directly:**
   ```bash
   python3 native-host/pass_browser_host.py
   ```
   
   Then type a JSON message:
   ```json
   {"command":"listEntries","pageURL":""}
   ```
   
   Press Ctrl+D to send EOF.

2. **Check browser console:**
   - Right-click extension icon → Inspect popup
   - Check for JavaScript errors

3. **Check background page:**
   - Go to `chrome://extensions/`
   - Click "Service worker" under your extension
   - Check console for errors

### Modifying the Extension

After making changes to the extension:
1. Go to `chrome://extensions/`
2. Click the refresh icon on your extension card
3. Test the changes

### Modifying the Native Host

After changing the Python script:
1. Test it directly (see Testing above)
2. No need to reinstall
3. Just restart the browser to reload the connection

## Security

- ✅ Extension runs in browser sandbox
- ✅ No network access required
- ✅ No telemetry or tracking
- ✅ Native messaging is restricted to specific extension ID
- ✅ All password operations go through native `pass` executable
- ✅ GPG encryption handled by `pass`

**Note:** The extension requires `nativeMessaging` permission to communicate with the Python host, which in turn executes `pass` commands.

## Comparison to pass-safari

| Feature | pass-safari | pass-browser |
|---------|-------------|--------------|
| Platform | macOS only | macOS, Linux, Windows |
| Browser | Safari | Chrome, Edge, Chromium |
| Backend | Swift + macOS App | Python script |
| Installation | Xcode build | Simple script |
| URL Cache | File-based | File-based |
| OTP Support | ✅ | ✅ |
| Autofill | ✅ | ✅ |
| Git Sync | ✅ | ✅ |

## License

MIT — see [LICENSE](../LICENSE).

## Credits

- Ported from [pass-safari](https://github.com/yourusername/pass-safari)
- Built for [pass](https://www.passwordstore.org/) by Jason A. Donenfeld
- Password generator based on work by Dania Usman

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Look for existing issues on GitHub
3. Create a new issue with:
   - Your OS and browser version
   - Steps to reproduce
   - Error messages from browser console
   - Native host logs (if available)
