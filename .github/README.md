# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automating various tasks for the PR Review CLI project.

## Available Workflows

### 1. Build and Release Executables (`build.yml`)

This workflow builds standalone executables for Windows, macOS, and Linux.

**Triggers:**
- When a new tag is pushed (e.g., `v1.0.0`)
- Manually from the GitHub Actions tab

**What it does:**
- Builds executables for all platforms
- Uploads them as artifacts
- Creates a GitHub Release with the executables (only on tag push)

**How to use:**
```bash
# Create a new tag
git tag v1.0.0

# Push the tag to trigger the workflow
git push origin v1.0.0
```

### 2. Test Package (`test.yml`)

This workflow tests the package on multiple Python versions.

**Triggers:**
- On push to main/master/develop branches
- On pull requests to main/master

**What it does:**
- Installs the package 
- Runs basic import and CLI tests
- Tests on Python 3.8, 3.9, 3.10, and 3.11

### 3. Publish to PyPI (`publish.yml`)

This workflow publishes the package to PyPI.

**Triggers:**
- When a GitHub Release is created

**What it does:**
- Builds the package
- Uploads it to PyPI

**Setup required:**
1. Add PyPI credentials as GitHub secrets:
   - `PYPI_USERNAME` - Your PyPI username
   - `PYPI_PASSWORD` - Your PyPI API token

## Manual Usage

To manually trigger the build workflow:
1. Go to the "Actions" tab in your GitHub repository
2. Select "Build and Release Executables" workflow
3. Click "Run workflow"
4. Choose the branch and click "Run workflow"

## Sharing Executables

After a successful build:

1. **From a tagged release:**
   - Go to the "Releases" section of your repository
   - Download the appropriate executable for your platform

2. **From a manual workflow run:**
   - Go to the workflow run in the Actions tab
   - Download the artifacts from the Summary page 