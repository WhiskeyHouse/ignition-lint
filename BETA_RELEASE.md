# Beta Release Guide

Test releases on TestPyPI before publishing to production PyPI.

## Setup (One-Time)

### 1. Create TestPyPI Account

1. Go to https://test.pypi.org/account/register/
2. Create account (separate from production PyPI)
3. Verify email

### 2. Configure Trusted Publishing on TestPyPI

1. Go to https://test.pypi.org/manage/account/publishing/
2. Add a new publisher:
   - **PyPI Project Name:** `ignition-lint-toolkit`
   - **Owner:** `TheThoughtagen`
   - **Repository:** `ignition-lint`
   - **Workflow name:** `release-beta.yml`
   - **Environment name:** `testpypi`
3. Save

### 3. Create GitHub Environment

1. Go to https://github.com/TheThoughtagen/ignition-lint/settings/environments
2. Click "New environment"
3. Name: `testpypi`
4. Click "Configure environment"
5. (Optional) Add protection rules:
   - Required reviewers
   - Wait timer
6. Save

Note: The `pypi` environment should already exist for production releases.

## Beta Release Workflow

### Step 1: Create Beta Tag

Beta releases use tags like `v1.0.0-beta1`, `v1.0.0-rc1`, `v1.0.0-alpha1`:

```bash
# Example: v1.0.0 beta 1
git tag -a v1.0.0-beta1 -m "Release v1.0.0-beta1 - Test release"
git push origin v1.0.0-beta1
```

Tag patterns that trigger TestPyPI:
- `v*-beta*` (e.g., v1.0.0-beta1)
- `v*-rc*` (e.g., v1.0.0-rc1)
- `v*-alpha*` (e.g., v1.0.0-alpha1)

### Step 2: Monitor Release Workflow

1. Go to https://github.com/TheThoughtagen/ignition-lint/actions
2. Watch "Beta Release (TestPyPI)" workflow
3. Workflow will:
   - ✅ Run CI tests
   - ✅ Build package
   - ✅ Publish to TestPyPI
   - ✅ Create GitHub pre-release

### Step 3: Test Installation from TestPyPI

```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple \
            ignition-lint-toolkit==1.0.0b1

# Verify installation
ignition-lint --version
ignition-lint --help

# Test on real project
ignition-lint -t /path/to/test/project
```

**Note:** The `--extra-index-url` is needed because dependencies (jsonschema, pathspec) are on production PyPI, not TestPyPI.

### Step 4: Test GitHub Action with Beta

Create a test workflow in another repo:

```yaml
name: Test Beta Action
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: TheThoughtagen/ignition-lint@v1.0.0-beta1
        with:
          files: "**/view.json"
```

### Step 5: Verify and Iterate

If issues found:
1. Fix the issues
2. Create new beta tag: `v1.0.0-beta2`
3. Repeat testing

Once satisfied, proceed to production release.

## Production Release

After beta testing is successful:

```bash
# Remove beta suffix for production
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Update v1 tracking tag
git tag -fa v1 -m "Release v1"
git push origin v1 --force
```

This triggers the production `release.yml` workflow which publishes to PyPI (not TestPyPI).

## Beta vs Production Workflows

| Aspect | Beta (release-beta.yml) | Production (release.yml) |
|--------|-------------------------|--------------------------|
| **Trigger** | `v*-beta*`, `v*-rc*`, `v*-alpha*` | `v*` (without suffix) |
| **PyPI** | TestPyPI | Production PyPI |
| **Environment** | `testpypi` | `pypi` |
| **GitHub Release** | Pre-release | Release |
| **Availability** | Test users only | Public |

## Version Numbering

### Beta Versions

Follow PEP 440 for pre-release versions:

| Tag | PyPI Version | Use Case |
|-----|--------------|----------|
| `v1.0.0-alpha1` | `1.0.0a1` | Early testing, unstable |
| `v1.0.0-beta1` | `1.0.0b1` | Feature complete, testing |
| `v1.0.0-rc1` | `1.0.0rc1` | Release candidate, stable |
| `v1.0.0` | `1.0.0` | Production release |

**Note:** hatch-vcs automatically converts git tags to PEP 440 format.

### Incrementing Beta Versions

```bash
# First beta
git tag -a v1.0.0-beta1 -m "Beta 1"

# After fixes
git tag -a v1.0.0-beta2 -m "Beta 2"

# Release candidate
git tag -a v1.0.0-rc1 -m "Release candidate 1"

# Final release
git tag -a v1.0.0 -m "Production release"
```

## Testing Checklist

Before promoting beta to production:

- [ ] Install from TestPyPI succeeds
- [ ] CLI works (`ignition-lint --help`, `--version`)
- [ ] Lint test project successfully
- [ ] All rule codes work as expected
- [ ] GitHub Action works with beta tag
- [ ] Documentation is accurate
- [ ] Examples run without errors
- [ ] No regressions from previous version

## Troubleshooting

### "Package not found on TestPyPI"

**Problem:** `pip install` fails immediately after publishing.

**Solution:** TestPyPI can take 1-2 minutes to index. Wait and retry.

### "Could not find a version that satisfies the requirement"

**Problem:** Version number mismatch.

**Solution:** Check the actual version on TestPyPI:
- Go to https://test.pypi.org/project/ignition-lint-toolkit/
- Note the version number (might be `1.0.0b1` not `1.0.0-beta1`)
- Use the exact version: `pip install ... ignition-lint-toolkit==1.0.0b1`

### "Environment 'testpypi' not found"

**Problem:** GitHub environment not configured.

**Solution:**
1. Create `testpypi` environment in repo settings
2. Re-run the workflow

### "Trusted publishing not configured"

**Problem:** TestPyPI doesn't have the publisher configured.

**Solution:**
1. Go to https://test.pypi.org/manage/account/publishing/
2. Add publisher for this repository + workflow
3. Re-run the workflow

## Cleanup

After successful production release, you can delete beta releases from GitHub:

1. Go to https://github.com/TheThoughtagen/ignition-lint/releases
2. Find beta/rc releases
3. Click "Delete" (tags remain)

Or keep them for reference.

## Quick Reference

```bash
# Create beta release
git tag -a v1.0.0-beta1 -m "Beta 1"
git push origin v1.0.0-beta1

# Test installation
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple \
            ignition-lint-toolkit

# Promote to production
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
git tag -fa v1 -m "Release v1"
git push origin v1 --force
```

---

**Ready to test?** Create a beta tag and monitor the workflow!
