# pass-browser for Firefox

This is the Firefox version of pass-browser.

## Differences from Chrome/Edge Version

### Manifest
- Uses Manifest v2 (Firefox doesn't fully support v3 yet)
- `browser_action` instead of `action`
- `background.scripts` instead of `background.service_worker`
- `permissions` includes `<all_urls>` (no separate `host_permissions`)
- Added `browser_specific_settings.gecko` for Firefox Add-ons

### Native Messaging
- Uses `allowed_extensions` instead of `allowed_origins`
- Extension ID: `pass-browser@zisoft.de`
- Same Python host, same wrapper script

## Installation

### 1. Install Native Host

Same as Chrome/Edge version:

```bash
cd ../native-host
./install.sh
```

This will now also install the Firefox manifest to:
- **macOS**: `~/Library/Application Support/Mozilla/NativeMessagingHosts/`
- **Linux**: `~/.mozilla/native-messaging-hosts/`

### 2. Load Extension in Firefox

**For Testing (Temporary):**

1. Open Firefox
2. Navigate to `about:debugging`
3. Click "This Firefox"
4. Click "Load Temporary Add-on..."
5. Select `manifest.json` from this directory
6. Extension ID will be `pass-browser@zisoft.de`

**Note:** Temporary extensions are removed when Firefox closes.

**For Permanent Installation:**

You need to sign the extension via Mozilla Add-ons (AMO) or use Firefox Developer Edition/Nightly with `xpinstall.signatures.required` set to `false`.

### 3. Verify

1. Click the extension icon
2. Your password entries should load
3. Navigate to a website with saved passwords
4. Badge should show number of suggestions

## Testing

Without Firefox installed, you can still verify:

1. The manifest is valid:
   ```bash
   python3 -m json.tool manifest.json
   ```

2. The native host works (same as Chrome/Edge):
   ```bash
   cd ../test
   ./test_host.py
   ```

## Known Differences

### Firefox-Specific APIs

The extension code already uses the `browser` API which is Firefox's preferred API:

```javascript
const tabsAPI = typeof browser !== 'undefined' ? browser.tabs : chrome.tabs;
```

This means the same code works in both Firefox and Chrome/Edge!

### Badge Behavior

Firefox's badge API is slightly different but compatible:
- Uses `browser.browserAction.setBadgeText()`
- Supports `setBadgeBackgroundColor()` and `setBadgeTextColor()`
- Same visual result as Chrome/Edge

### Native Messaging

Firefox uses the same native messaging protocol as Chrome:
- JSON messages via stdin/stdout
- Same binary length-prefixed format
- Python host works identically

## Distribution

### Firefox Add-ons (AMO)

To publish on addons.mozilla.org:

1. Create a `.zip` of this directory:
   ```bash
   zip -r pass-browser-firefox.zip *
   ```

2. Submit to https://addons.mozilla.org/developers/

3. Mozilla will review and sign it

### Self-Hosting

For personal use or enterprise deployment:
1. Sign with your own certificate
2. Or use Firefox Developer/Nightly with disabled signature requirement

## Compatibility

- **Minimum Firefox Version**: 109.0
- **Tested**: Not yet tested (no Firefox available)
- **Expected to work**: Yes, code is compatible

## Differences from pass-safari

Like the Chrome/Edge version, this replaces the Swift native messaging with Python.

## Support

Same Python host as Chrome/Edge version, so debugging is identical.

Check:
1. `about:debugging` → Extension console
2. Native host logs (if debug wrapper is enabled)
3. `~/.mozilla/native-messaging-hosts/de.zisoft.pass_browser.json`

## License

MIT - Same as main project
