# Contributing to pass-browser

Thank you for your interest in contributing to pass-browser! This document provides guidelines and information for contributors.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment

## How to Contribute

### Reporting Bugs

When reporting bugs, please include:

1. **Environment details:**
   - OS and version (macOS 13.0, Ubuntu 22.04, etc.)
   - Browser and version (Chrome 120, Edge 119, etc.)
   - Python version (`python3 --version`)
   - pass version (`pass --version`)

2. **Steps to reproduce:**
   - Clear, numbered steps
   - Expected behavior
   - Actual behavior

3. **Logs and errors:**
   - Browser console errors (right-click extension → Inspect)
   - Native host stderr output
   - Any relevant screenshots

4. **Additional context:**
   - Does it happen consistently?
   - Did it work before?
   - Any recent changes to your system?

### Suggesting Features

Feature requests are welcome! Please:

1. Check if the feature already exists
2. Search existing issues to avoid duplicates
3. Describe the use case
4. Explain why this would be useful
5. Consider implementation complexity

### Submitting Pull Requests

#### Before You Start

1. Check existing issues and PRs
2. Discuss major changes in an issue first
3. Fork the repository
4. Create a feature branch

#### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/pass-browser.git
cd pass-browser

# Create a feature branch
git checkout -b feature/your-feature-name
```

#### Making Changes

**For Extension (JavaScript):**
- Follow existing code style
- Test in both Chrome and Edge
- Keep popup.js focused and modular
- Add comments for complex logic

**For Native Host (Python):**
- Follow PEP 8 style guide
- Add type hints where appropriate
- Include docstrings for functions
- Test with different pass configurations

#### Testing Your Changes

**Extension:**
```bash
# Load unpacked extension from extension/ folder
# Test all major features:
- List entries
- Search/filter
- Autofill
- Create/edit/delete
- OTP codes
- Git sync
```

**Native Host:**
```bash
# Test the host directly
cd test
./test_host.py

# Test with real browser:
# 1. Update manifest with your extension ID
# 2. Reload extension
# 3. Test thoroughly
```

#### Commit Guidelines

- Use clear, descriptive commit messages
- Start with a verb: "Add", "Fix", "Update", "Remove"
- Keep commits focused and atomic
- Reference issues when applicable

**Good examples:**
```
Add support for HOTP codes
Fix clipboard copy on Linux
Update README installation instructions
Remove deprecated password format
```

**Bad examples:**
```
Fixed stuff
WIP
More changes
asdf
```

#### Pull Request Process

1. **Update documentation:**
   - Update README.md if needed
   - Update CHANGELOG.md
   - Add comments to code

2. **Test thoroughly:**
   - Test on multiple platforms if possible
   - Verify no regressions
   - Check browser console for errors

3. **Create the PR:**
   - Clear title describing the change
   - Detailed description of what and why
   - Link to related issues
   - Include screenshots if UI changes

4. **Respond to feedback:**
   - Address review comments
   - Update code as needed
   - Keep discussion focused and constructive

## Development Guidelines

### Code Style

**JavaScript:**
```javascript
// Use const/let, not var
const entries = [];

// Async/await preferred over callbacks
async function loadEntries() {
    const response = await sendNativeMessage({
        command: "listEntries"
    });
    return response.entries;
}

// Clear function names
function filterEntriesBySearchTerm(entries, term) {
    return entries.filter(entry => 
        entry.toLowerCase().includes(term.toLowerCase())
    );
}
```

**Python:**
```python
# Type hints
def parse_entry(output: str, name: str) -> Dict[str, Any]:
    """Parse pass entry output into structured data"""
    pass

# Error handling
try:
    result = run_pass(["show", entry])
except subprocess.CalledProcessError as e:
    raise RuntimeError(f"Failed to get entry: {e}")

# Clear variable names
password_entries = list_entries()
```

### Testing Checklist

Before submitting a PR, verify:

- [ ] Extension loads without errors
- [ ] All commands work (list, get, update, delete, sync)
- [ ] Autofill works on test sites
- [ ] Search/filter works correctly
- [ ] Password generator works
- [ ] OTP codes display and refresh (if available)
- [ ] Error messages are clear and helpful
- [ ] No console errors or warnings
- [ ] Works in both Chrome and Edge
- [ ] README/docs updated if needed

### Common Pitfalls

1. **Native messaging format:**
   - Messages must use Chrome's native messaging protocol
   - Length prefix is 4 bytes, little-endian
   - Message is UTF-8 encoded JSON

2. **Extension ID:**
   - Must be updated in manifest after loading
   - Different for each installation
   - Changes when extension is reloaded in dev mode

3. **Async operations:**
   - Most browser APIs are async
   - Always handle errors
   - Don't block the UI

4. **Cross-platform issues:**
   - Path separators differ (/ vs \)
   - Clipboard tools vary by OS
   - Test on multiple platforms if possible

## Project Structure

```
pass-browser/
├── extension/              # Browser extension
│   ├── manifest.json       # Extension configuration
│   ├── popup.{html,js,css} # Main UI
│   ├── background.js       # Service worker
│   ├── content.js          # Autofill logic
│   └── images/             # Icons
├── native-host/            # Native messaging host
│   ├── pass_browser_host.py    # Main host script
│   ├── *.json              # Native messaging manifests
│   └── install.*           # Installation scripts
├── test/                   # Test utilities
└── docs/                   # Documentation
```

## Communication

- **Issues:** For bug reports and feature requests
- **Pull Requests:** For code contributions
- **Discussions:** For questions and general discussion

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

If you're unsure about anything:
- Check existing issues and PRs
- Read the README and documentation
- Ask in a GitHub issue

Thank you for contributing! 🎉
