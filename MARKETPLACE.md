# GitHub Marketplace Publication Guide

This guide covers how to publish ignition-lint to the GitHub Actions Marketplace.

## Prerequisites

- Repository must be public
- Repository must have at least one release/tag
- `action.yml` must be in repository root
- Repository must be under your personal account (TheThoughtagen) or organization

## Pre-Publication Checklist

- [x] action.yml has all required metadata
  - [x] name
  - [x] description
  - [x] author
  - [x] branding (icon, color)
  - [x] inputs documented
  - [x] outputs documented
- [x] ACTION_README.md created with examples
- [x] action.yml tested locally
- [ ] Create v1.0.0 tag
- [ ] Publish to marketplace

## Testing the Action Locally

Before publishing, test the action in a real workflow:

### 1. Create a test repository

```bash
mkdir test-ignition-project
cd test-ignition-project
git init
mkdir -p views
# Add a sample view.json
```

### 2. Create workflow file

```yaml
# .github/workflows/test-action.yml
name: Test Action
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Test local action before marketplace
      - uses: TheThoughtagen/ignition-lint@main
        with:
          files: "**/view.json"
          component_style: "PascalCase"
```

### 3. Push and verify

```bash
git add .
git commit -m "Test ignition-lint action"
git push
```

Check the Actions tab - the workflow should run successfully.

## Publishing to Marketplace

### Step 1: Create a Release Tag

```bash
# Ensure you're on main branch
git checkout main
git pull

# Create and push v1.0.0 tag
git tag -a v1.0.0 -m "Release v1.0.0 - Initial marketplace release"
git push origin v1.0.0

# Also create v1 tag that will track latest v1.x.x
git tag -fa v1 -m "Release v1"
git push origin v1 --force
```

### Step 2: Create GitHub Release

1. Go to https://github.com/TheThoughtagen/ignition-lint/releases/new
2. Choose tag: `v1.0.0`
3. Release title: `v1.0.0 - Initial Marketplace Release`
4. Description:

```markdown
## Initial Marketplace Release

Comprehensive linting toolkit for Ignition SCADA projects, now available on GitHub Marketplace!

### Features

- ✅ Perspective view validation (schema, bindings, expressions)
- ✅ Script linting (Jython inline + Python standalone)
- ✅ Naming convention enforcement (PascalCase, camelCase, custom regex)
- ✅ Expression validation (polling intervals, property refs)
- ✅ Unused property detection
- ✅ Flexible suppression (CLI, .ignition-lintignore, inline comments)

### Quick Start

```yaml
- uses: TheThoughtagen/ignition-lint@v1
  with:
    project_path: .
    lint_type: all
```

See [ACTION_README.md](https://github.com/TheThoughtagen/ignition-lint/blob/main/ACTION_README.md) for full documentation.

### Installation

```bash
pip install ignition-lint-toolkit
```

### What's Changed

- Initial public release
- Full CI/CD integration
- Comprehensive documentation
- Example projects and integrations

**Full Changelog**: https://github.com/TheThoughtagen/ignition-lint/commits/v1.0.0
```

5. Check "Set as the latest release"
6. Click "Publish release"

### Step 3: Publish to Marketplace

After creating the release:

1. GitHub will detect the `action.yml` in your repository
2. Go to the repository's main page
3. You should see a banner: **"Publish this Action to the GitHub Marketplace"**
4. Click the banner or go to: https://github.com/marketplace/new?action=TheThoughtagen/ignition-lint
5. Review the form:
   - **Name:** Ignition Lint (from action.yml)
   - **Description:** (from action.yml)
   - **Icon/Color:** (from action.yml branding)
   - **Categories:** Select relevant categories:
     - ✓ Code quality
     - ✓ Continuous integration
     - ✓ Utilities
6. Accept the marketplace terms
7. Click **"Publish this action to the GitHub Marketplace"**

### Step 4: Verify Publication

1. Navigate to: https://github.com/marketplace/actions/ignition-lint
2. Verify:
   - Action name and description display correctly
   - README (ACTION_README.md) renders properly
   - Examples are clear and functional
   - Badges show correct status

## Post-Publication

### Update README

Add marketplace badge to main README.md:

```markdown
[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-ignition--lint-blue?logo=github)](https://github.com/marketplace/actions/ignition-lint)
```

### Announce

- Post in Ignition forums
- Share on relevant Slack/Discord communities
- Tweet about the release
- Update documentation site

### Monitor

Watch for:
- GitHub issues from users
- Questions in Discussions
- Stars/forks/usage stats
- Marketplace reviews

## Versioning Strategy

### Semantic Versioning

Follow SemVer: `MAJOR.MINOR.PATCH`

- **MAJOR (v2, v3):** Breaking changes to inputs/outputs
- **MINOR (v1.1, v1.2):** New features, backward compatible
- **PATCH (v1.0.1, v1.0.2):** Bug fixes, backward compatible

### Tag Strategy

Maintain two types of tags:

**1. Specific version tags** (immutable)
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git tag -a v1.0.1 -m "Release v1.0.1"
git tag -a v1.1.0 -m "Release v1.1.0"
```

**2. Moving major version tags** (updated with each minor/patch)
```bash
# When releasing v1.0.1:
git tag -fa v1 -m "Update v1 to v1.0.1"
git push origin v1 --force

# When releasing v1.1.0:
git tag -fa v1 -m "Update v1 to v1.1.0"
git push origin v1 --force
```

Users referencing `@v1` automatically get latest v1.x.x patches, while `@v1.0.0` pins to exact version.

### Release Checklist

For each new release:

- [ ] Update CHANGELOG.md
- [ ] Bump version if using explicit version field
- [ ] Run tests: `pytest`
- [ ] Build and test package: `uv build && pip install dist/*.whl`
- [ ] Create version tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- [ ] Push tag: `git push origin vX.Y.Z`
- [ ] Update major version tag: `git tag -fa vX -m "Update vX to vX.Y.Z" && git push origin vX --force`
- [ ] Create GitHub Release with changelog
- [ ] Verify marketplace updates automatically
- [ ] Test action with new tag: `uses: TheThoughtagen/ignition-lint@vX.Y.Z`

## Updating the Action

### Minor Updates (v1.1.0, v1.2.0)

For new features that are backward compatible:

```bash
# Make changes, commit
git add .
git commit -m "feat: add new input for custom schema path"
git push

# Create new version tag
git tag -a v1.1.0 -m "Release v1.1.0 - Add custom schema support"
git push origin v1.1.0

# Update v1 to point to v1.1.0
git tag -fa v1 -m "Update v1 to v1.1.0"
git push origin v1 --force

# Create GitHub Release
# Marketplace updates automatically
```

### Patch Updates (v1.0.1, v1.0.2)

For bug fixes:

```bash
# Fix bug, commit
git add .
git commit -m "fix: handle edge case in naming validator"
git push

# Create patch tag
git tag -a v1.0.1 -m "Release v1.0.1 - Fix naming validator bug"
git push origin v1.0.1

# Update v1 to point to v1.0.1
git tag -fa v1 -m "Update v1 to v1.0.1"
git push origin v1 --force

# Create GitHub Release
```

### Breaking Changes (v2.0.0)

For breaking changes:

1. Update action.yml with new inputs/outputs
2. Update ACTION_README.md with migration guide
3. Create v2.0.0 and v2 tags
4. Document breaking changes in release notes
5. Keep v1 tags for users who need old behavior

## Marketplace Guidelines

### Do's

✅ Provide clear, tested examples
✅ Document all inputs and outputs
✅ Include troubleshooting section
✅ Respond to issues promptly
✅ Keep action.yml metadata current
✅ Test before releasing
✅ Use semantic versioning

### Don'ts

❌ Break backward compatibility in minor/patch versions
❌ Force users to update to get bug fixes (maintain v1 tag)
❌ Leave issues unanswered
❌ Publish untested releases
❌ Change action name after publication
❌ Remove old versions (users may depend on them)

## Support

After publishing, direct users to:

- **Issues:** https://github.com/TheThoughtagen/ignition-lint/issues
- **Discussions:** https://github.com/TheThoughtagen/ignition-lint/discussions
- **Documentation:** https://TheThoughtagen.github.io/ignition-lint/

## Analytics

Monitor action usage via:

- GitHub Insights → Traffic (stars, forks, clones)
- Marketplace listing (views, unique visitors)
- Issues and Discussions activity
- PyPI downloads (pip installs)

---

**Ready to publish?** Follow the steps above and join the GitHub Marketplace!
