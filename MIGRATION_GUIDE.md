# Repository Migration Guide

This guide covers migrating ignition-lint from WhiskeyHouse organization to TheThoughtagen personal account.

## Pre-Migration Checklist

Before transferring the repository:

- [x] Update all branding in code (LICENSE, pyproject.toml, action.yml)
- [x] Update all documentation URLs (README, docs/, website/)
- [x] Update GitHub Action references
- [x] Test that all changes work locally
- [ ] Commit and push all changes to main branch
- [ ] Create backup of repository (clone locally)

## Step 1: Transfer Repository on GitHub

### Option A: Transfer Repository (Recommended)

This preserves all issues, PRs, stars, and forks.

1. Go to repository Settings
2. Scroll to "Danger Zone"
3. Click "Transfer ownership"
4. Enter new owner: `TheThoughtagen`
5. Type repository name to confirm: `ignition-lint`
6. Click "I understand, transfer this repository"

### Option B: Create New Repository and Push

If you can't transfer (e.g., naming conflicts):

```bash
# Create new repo on GitHub: TheThoughtagen/ignition-lint

# Update remote
cd /path/to/ignition-lint
git remote remove origin
git remote add origin https://github.com/TheThoughtagen/ignition-lint.git

# Push all branches and tags
git push -u origin main
git push origin --all
git push origin --tags
```

## Step 2: Update Local Git Configuration

After transfer, update your local clone:

```bash
cd /Users/pmannion/whiskeyhouse/ignition-lint

# Update remote URL
git remote set-url origin https://github.com/TheThoughtagen/ignition-lint.git
git remote set-url main https://github.com/TheThoughtagen/ignition-lint.git
git remote set-url upstream https://github.com/TheThoughtagen/ignition-lint.git

# Verify
git remote -v

# Should show:
# main    https://github.com/TheThoughtagen/ignition-lint.git (fetch)
# main    https://github.com/TheThoughtagen/ignition-lint.git (push)
# origin  https://github.com/TheThoughtagen/ignition-lint.git (fetch)
# origin  https://github.com/TheThoughtagen/ignition-lint.git (push)

# Fetch to verify connection
git fetch origin
```

## Step 3: Verify GitHub Actions Workflows

After transfer, check that all workflows still work:

### 1. Check workflow files

All workflows should now reference the new repository:

```bash
# Verify no references to WhiskeyHouse remain
grep -r "WhiskeyHouse" .github/workflows/
# Should return no results
```

### 2. Test workflows

Trigger workflows to ensure they work:

```bash
# Make a small change to trigger CI
git commit --allow-empty -m "test: verify CI works after migration"
git push origin main
```

Check Actions tab: https://github.com/TheThoughtagen/ignition-lint/actions

Expected workflows to run:
- ✅ CI (tests on Python 3.10-3.13)
- ✅ Deploy Docs (if on main)

### 3. Verify GitHub Pages

If using GitHub Pages for documentation:

1. Go to Settings → Pages
2. Verify source is set correctly (usually `main` branch, `/website/build/` or gh-pages)
3. Check site loads: https://TheThoughtagen.github.io/ignition-lint/

## Step 4: Update PyPI Project (if published)

### Option A: Transfer Ownership on PyPI

1. Log in to PyPI: https://pypi.org/
2. Go to project: https://pypi.org/project/ignition-lint-toolkit/
3. Click "Manage" → "Collaborators"
4. Add `TheThoughtagen` as Maintainer
5. (Optional) Remove `WhiskeyHouse` collaborator

### Option B: Continue Publishing from Personal Account

No change needed if you're already publishing from your personal PyPI account. The package name (`ignition-lint-toolkit`) remains the same.

Verify with:
```bash
# Check current PyPI credentials
pip config list
```

## Step 5: Update GitHub Secrets and Settings

After transfer, verify repository secrets:

### Required Secrets (if publishing to PyPI)

GitHub Actions → Settings → Secrets and variables → Actions

Check for:
- `PYPI_API_TOKEN` (if using token auth)
- Or ensure OIDC publishing is configured for `pypi` environment

### Repository Settings

1. **Default branch:** Ensure `main` is default
2. **Branch protection:** Re-apply rules if needed:
   - Require PR reviews
   - Require status checks (CI)
   - No force pushes
3. **GitHub Pages:** Re-enable if it was disabled during transfer
4. **Environments:** Check `pypi` environment exists (for release workflow)

## Step 6: Update External References

### Documentation

Verify documentation site redirects work:
- Old: https://WhiskeyHouse.github.io/ignition-lint/
- New: https://TheThoughtagen.github.io/ignition-lint/

GitHub automatically redirects old URLs if you transferred (not recreated).

### Badges

All badges in README.md should already point to new URLs (updated in previous steps):
- ✅ PyPI badge
- ✅ CI badge
- ✅ GitHub Marketplace badge

### Links

Verify external links work:
```bash
# Check all markdown files for broken links
find . -name "*.md" -type f -exec grep -l "github.com" {} \;
```

## Step 7: Announce Migration (Optional)

If the project had users under the old organization:

### Create a migration announcement

```markdown
## 📦 Repository Migration

ignition-lint has moved to https://github.com/TheThoughtagen/ignition-lint

### What Changed

- Repository location: `WhiskeyHouse/ignition-lint` → `TheThoughtagen/ignition-lint`
- Documentation: `WhiskeyHouse.github.io/ignition-lint` → `TheThoughtagen.github.io/ignition-lint`
- Ownership: Whiskey House Labs → Patrick Mannion

### What Didn't Change

- ✅ Package name: `ignition-lint-toolkit` (same on PyPI)
- ✅ GitHub Action: `TheThoughtagen/ignition-lint@v1` (updated from `whiskeyhouse/...`)
- ✅ All features, APIs, and functionality

### Action Required for Users

If you use the GitHub Action, update your workflows:

```diff
- uses: whiskeyhouse/ignition-lint@v1
+ uses: TheThoughtagen/ignition-lint@v1
```

If you cloned the repository, update your remote:

```bash
git remote set-url origin https://github.com/TheThoughtagen/ignition-lint.git
```

If you installed from PyPI, no changes needed - the package name is unchanged.

### Questions?

Open an issue: https://github.com/TheThoughtagen/ignition-lint/issues
```

Post this in:
- GitHub Discussions
- Old repository (if still accessible - pin as announcement)
- Ignition forums (if you posted there previously)

## Step 8: Verify Everything Works

### Final Checklist

Run through this checklist to ensure migration is complete:

- [ ] Repository transferred to TheThoughtagen
- [ ] Local git remotes updated
- [ ] All workflows passing on new repository
- [ ] GitHub Pages documentation loading
- [ ] PyPI package still accessible
- [ ] GitHub Action tested with new reference
- [ ] No broken links in documentation
- [ ] CI/CD pipelines working (test + release)
- [ ] Secrets and settings configured
- [ ] README badges showing correct status

### Test the Full Stack

```bash
# 1. Clone from new location
cd /tmp
git clone https://github.com/TheThoughtagen/ignition-lint.git
cd ignition-lint

# 2. Run tests
uv sync
uv run pytest

# 3. Build package
uv build

# 4. Install and test CLI
pip install dist/*.whl
ignition-lint --help

# 5. Test GitHub Action (create test workflow in a separate repo)
# See MARKETPLACE.md for testing guide
```

## Troubleshooting

### "Repository not found" after transfer

**Problem:** Git commands fail with 404.

**Solution:**
```bash
# Update remote URL
git remote set-url origin https://github.com/TheThoughtagen/ignition-lint.git
git fetch origin
```

### Old URLs still show in documentation

**Problem:** Some docs still reference WhiskeyHouse.

**Solution:**
```bash
# Find and replace
grep -r "WhiskeyHouse" docs/ website/ README.md
# Manually update any remaining references
```

### GitHub Pages not loading

**Problem:** Documentation site returns 404.

**Solution:**
1. Go to Settings → Pages
2. Re-select source branch (main or gh-pages)
3. Wait 1-2 minutes for deployment
4. Check Actions tab for deployment workflow

### PyPI releases failing

**Problem:** Release workflow fails with authentication error.

**Solution:**
1. Check `PYPI_API_TOKEN` secret is set
2. Or verify Trusted Publishing is configured:
   - Go to PyPI project settings
   - Add GitHub Actions publisher:
     - Owner: `TheThoughtagen`
     - Repository: `ignition-lint`
     - Workflow: `release.yml`
     - Environment: `pypi`

### Marketplace Action not found

**Problem:** `uses: TheThoughtagen/ignition-lint@v1` fails.

**Solution:**
```bash
# Ensure v1 tag exists and points to valid commit
git tag -fa v1 -m "Update v1 tag"
git push origin v1 --force
```

---

## Post-Migration Cleanup

After migration is complete and verified:

1. **Archive old repository** (if it still exists under WhiskeyHouse)
   - Add README notice about migration
   - Archive the repository (Settings → Archive)

2. **Update local workspace path** (optional)
   ```bash
   # Move from whiskeyhouse to your preferred location
   mv /Users/pmannion/whiskeyhouse/ignition-lint ~/projects/ignition-lint
   ```

3. **Clean up old remotes**
   ```bash
   # If you have duplicate remotes
   git remote remove upstream  # If it's a duplicate
   ```

---

**Migration complete!** 🎉

Repository now lives at: https://github.com/TheThoughtagen/ignition-lint
