# Quick Start Guide

Get pass-browser up and running in 5 minutes!

## Prerequisites

1. **Install pass:**
   ```bash
   # macOS
   brew install pass pass-otp
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install pass pass-extension-otp
   ```

2. **Set up your password store** (if not already done):
   ```bash
   pass init your-gpg-key-id
   ```

## Installation Steps

### 1. Install Native Host

```bash
cd native-host
./install.sh
```

### 2. Load Extension

1. Open Chrome/Edge
2. Go to `chrome://extensions/` (or `edge://extensions/`)
3. Enable **Developer mode**
4. Click **Load unpacked**
5. Select the `extension` folder
6. **Copy the Extension ID** (looks like: `abcdefghijklmnopqrstuvwxyz123456`)

### 3. Update Native Messaging Manifest

**macOS:**
```bash
# Edit the file
nano ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/de.zisoft.pass_browser.json

# Replace EXTENSION_ID with your actual ID from step 2
```

**Linux:**
```bash
# Edit the file
nano ~/.config/google-chrome/NativeMessagingHosts/de.zisoft.pass_browser.json

# Replace EXTENSION_ID with your actual ID from step 2
```

### 4. Restart Browser

Completely close and reopen your browser.

### 5. Test

1. Click the pass-browser extension icon
2. You should see your password entries
3. Try searching and autofilling on a website

## Troubleshooting

### "Unable to connect to native messaging host"

1. Check if Python 3 is installed:
   ```bash
   python3 --version
   ```

2. Check if the manifest has the correct extension ID:
   ```bash
   # macOS
   cat ~/Library/Application\ Support/Google/Chrome/NativeMessagingHosts/de.zisoft.pass_browser.json
   
   # Linux
   cat ~/.config/google-chrome/NativeMessagingHosts/de.zisoft.pass_browser.json
   ```

3. Check browser console for errors:
   - Right-click extension icon → Inspect popup
   - Look for error messages in Console

### No entries showing

1. Verify pass is working:
   ```bash
   pass ls
   ```

2. Check password store location:
   ```bash
   echo $PASSWORD_STORE_DIR
   # Should show ~/.password-store or your custom location
   ```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Set up git sync for your password store
- Configure OTP for two-factor authentication
- Customize keyboard shortcuts in the browser

## Quick Commands

**Add a new password:**
```bash
pass insert websites/example.com
```

**Add with OTP:**
```bash
pass otp append websites/example.com
```

**Sync with git:**
```bash
pass git pull
pass git push
```

Or use the sync button (🔄) in the extension!
