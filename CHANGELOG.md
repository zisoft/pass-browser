# Changelog

All notable changes to pass-browser will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-07-02

### Added
- Initial release of pass-browser
- Ported from pass-safari to Chrome/Edge/Chromium
- Python-based native messaging host
- Support for all pass-safari features:
  - List and search password entries
  - Create/edit/delete entries
  - Autofill credentials on websites
  - OTP/TOTP support (requires pass-otp)
  - Password generator
  - Git sync integration
  - URL-based password suggestions
- Cross-platform support (macOS, Linux, Windows with WSL)
- Installation scripts for Unix and Windows
- Comprehensive documentation

### Changed
- Replaced Swift-based native messaging with Python
- Simplified installation process
- Improved cross-platform compatibility

### Technical Details
- Extension ID: To be assigned at installation
- Native host ID: de.zisoft.pass_browser
- Manifest version: 3
- Python version: 3.6+

## Differences from pass-safari

### Architecture Changes
- **Backend**: Swift/macOS App → Python script
- **Communication**: File-based → Native messaging (stdin/stdout)
- **Platform**: Safari/macOS only → Chrome/Edge on macOS/Linux/Windows

### Compatibility
- All core features from pass-safari maintained
- Same UI and user experience
- Compatible with same pass entry format
- Same URL matching algorithm

### Installation
- **pass-safari**: Requires Xcode build, macOS App Bundle
- **pass-browser**: Simple script installation, no compilation needed

## Known Limitations

- URL index caching not yet implemented (coming in v1.1.0)
- Windows support requires WSL or alternative pass implementation
- Some Linux distributions may need additional clipboard utilities

## Planned Features

### Version 1.1.0
- [ ] URL index caching for faster suggestions
- [ ] Background URL index refresh
- [ ] Improved error messages
- [ ] Optional browser-specific customizations

### Version 1.2.0
- [ ] Import/export functionality
- [ ] Backup and restore
- [ ] Password strength indicator
- [ ] Duplicate password detection

### Future
- [ ] Firefox support
- [ ] Native Windows pass alternative support
- [ ] Cloud sync options (beyond git)
- [ ] Biometric authentication integration

## Migration from pass-safari

If you're switching from pass-safari to pass-browser:

1. Your password store remains unchanged (same `~/.password-store`)
2. No data migration needed
3. Install pass-browser following the Quick Start guide
4. Both extensions can coexist if needed

## Support

For issues, feature requests, or questions:
- GitHub Issues: [Create an issue](https://github.com/yourusername/pass-browser/issues)
- Documentation: See [README.md](README.md)
