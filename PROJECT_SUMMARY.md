# pass-browser - Project Summary

## 📦 What is this?

pass-browser is a **Chrome/Edge extension** that integrates with the **pass** Unix password manager. It's a port of the Safari-only pass-safari extension, now available for Chrome, Edge, and Chromium browsers on macOS, Linux, and Windows.

## 🎯 Key Features

✅ Full pass integration (list, create, edit, delete passwords)  
✅ Auto-fill credentials on websites  
✅ OTP/TOTP support (2FA codes)  
✅ Password generator  
✅ Git sync integration  
✅ URL-based password suggestions  
✅ Cross-platform (macOS, Linux, Windows)  
✅ Secure native messaging architecture  
✅ No network access, no telemetry  

## 📁 Project Structure

```
pass-browser/
│
├── 📄 README.md              # Main documentation
├── 📄 QUICKSTART.md          # 5-minute setup guide
├── 📄 CHANGELOG.md           # Version history
├── 📄 CONTRIBUTING.md        # Contributor guidelines
├── 📄 LICENSE                # MIT License
│
├── 🧩 extension/             # Browser Extension
│   ├── manifest.json         # Extension config
│   ├── popup.html/js/css     # Main UI
│   ├── background.js         # Service worker
│   ├── content.js            # Autofill logic
│   ├── images/               # Icons
│   └── _locales/             # i18n messages
│
├── 🐍 native-host/           # Python Native Messaging Host
│   ├── pass_browser_host.py  # Main host script (458 lines)
│   ├── de.zisoft.pass_browser.json          # Manifest (Unix)
│   ├── de.zisoft.pass_browser.windows.json  # Manifest (Windows)
│   ├── install.sh            # Unix installer
│   └── install.bat           # Windows installer
│
└── 🧪 test/                  # Testing utilities
    └── test_host.py          # Host test script
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (Chrome/Edge)                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Extension (Sandboxed)                 │    │
│  │  • popup.js    - UI logic                          │    │
│  │  • background.js - Service worker                  │    │
│  │  • content.js  - Autofill                          │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                 │
│                           │ Native Messaging                │
│                           │ (JSON via stdin/stdout)         │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          Python Native Host (pass_browser_host.py)          │
│  • Receives JSON messages from extension                    │
│  • Executes pass commands                                   │
│  • Handles OTP generation                                   │
│  • Manages clipboard operations                             │
│  • Returns JSON responses                                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   pass CLI (password-store)                 │
│  • Stores passwords in ~/.password-store                    │
│  • GPG encryption                                           │
│  • Git integration                                          │
│  • OTP support (pass-otp extension)                         │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Communication Flow

1. **User clicks extension** → Opens popup.html
2. **popup.js requests data** → Sends JSON message via native messaging
3. **background.js forwards** → To native host via stdin
4. **Python host receives** → Parses JSON message
5. **Host executes pass** → Runs appropriate pass command
6. **Host returns result** → JSON response via stdout
7. **Extension receives** → Updates UI with data

## 📋 Installation Summary

### Quick Install (3 steps)

```bash
# 1. Install native host
cd native-host && ./install.sh

# 2. Load extension in browser
# chrome://extensions/ → Load unpacked → select extension/

# 3. Update manifest with extension ID
# Edit ~/.config/google-chrome/NativeMessagingHosts/de.zisoft.pass_browser.json
# Replace EXTENSION_ID with actual ID from step 2
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## 🛠️ Technologies Used

| Component | Technology |
|-----------|------------|
| Extension | JavaScript (ES6+), HTML5, CSS3 |
| Native Host | Python 3.6+ |
| Backend | pass (standard Unix password manager) |
| Encryption | GPG (via pass) |
| Communication | Chrome Native Messaging Protocol |
| UI Framework | Vanilla JS (no frameworks) |

## 📊 Code Statistics

| File | Lines | Description |
|------|-------|-------------|
| popup.js | ~1,500 | Main UI logic |
| content.js | ~800 | Autofill functionality |
| background.js | ~200 | Service worker |
| pass_browser_host.py | ~450 | Python native host |
| **Total** | ~3,000 | Lines of code |

## 🆚 Comparison to pass-safari

| Feature | pass-safari | pass-browser |
|---------|-------------|--------------|
| Platform | macOS only | macOS, Linux, Windows |
| Browser | Safari | Chrome, Edge, Chromium |
| Backend Language | Swift | Python |
| Installation | Xcode build | Script (no compilation) |
| App Bundle | Required | Not required |
| Communication | File-based | Native messaging |
| Dependencies | Xcode, Swift | Python 3, pass |

## 🎓 For Developers

### Extension Development
- Standard WebExtensions API
- Manifest v3
- Service worker background script
- Browser action popup

### Native Host Development
- Implements Chrome Native Messaging Protocol
- Reads/writes messages in binary format (length-prefixed JSON)
- Executes subprocess commands to pass
- Handles JSON serialization/deserialization

### Testing
```bash
# Test native host directly
python3 test/test_host.py

# Manual testing
echo '{"command":"listEntries","pageURL":""}' | python3 native-host/pass_browser_host.py
```

## 📝 Documentation Files

- **README.md** - Main documentation (comprehensive)
- **QUICKSTART.md** - Fast setup guide
- **CHANGELOG.md** - Version history and changes
- **CONTRIBUTING.md** - Guidelines for contributors
- **LICENSE** - MIT License

## 🔗 Dependencies

### Required
- Python 3.6+
- pass (password-store)
- GPG
- Chrome/Edge/Chromium browser

### Optional
- pass-otp (for OTP/2FA support)
- git (for syncing password store)
- pbcopy/xclip/xsel (for clipboard support)

## 🐛 Known Issues

- URL index caching not yet implemented
- Windows support limited (requires WSL or alternative)
- Some Linux distros need additional clipboard utilities

See [CHANGELOG.md](CHANGELOG.md) for planned features.

## 📄 License

MIT License - See [LICENSE](LICENSE) file

Copyright (c) 2026 Mario Zimmermann

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: This repository
- **Questions**: GitHub Discussions

## 🎉 Credits

- Ported from [pass-safari](https://github.com/yourusername/pass-safari)
- Built for [pass](https://www.passwordstore.org/) by Jason A. Donenfeld
- Password generator based on work by Dania Usman

---

**Status**: ✅ Ready for testing and use  
**Version**: 1.0.0  
**Last Updated**: 2026-07-02
