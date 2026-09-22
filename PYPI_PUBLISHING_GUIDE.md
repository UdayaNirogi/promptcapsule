# Publishing PromptCapsule to PyPI

**Goal**: Make PromptCapsule installable via `pip install promptcapsule`  
**Current Status**: Code is on GitHub and ready to publish  
**Version**: 0.1.0

---

## Step 1: Create a PyPI Account

### Option A: PyPI (Production)
1. Go to: https://pypi.org/account/register/
2. Fill in details:
   - **Username**: `UdayaNirogi` (or your PyPI username)
   - **Email**: Your email
   - **Password**: Strong password
3. Verify email
4. Go to Account Settings → API tokens
5. Create token for "Entire account"
6. Copy token (starts with `pypi-`)

### Option B: TestPyPI (Recommended First)
1. Go to: https://test.pypi.org/account/register/
2. Same process as above
3. This is a sandbox for testing before production

---

## Step 2: Install Build Tools

```bash
pip install build twine wheel setuptools
```

Verify installation:
```bash
python -m build --version
twine --version
```

---

## Step 3: Configure PyPI Credentials

Create a file: `~/.pypirc`

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_PYPI_TOKEN_HERE
```

**Security Note**: Never commit `.pypirc` to git! Add to `.gitignore`.

---

## Step 4: Build the Package

Navigate to your project:

```bash
cd /Users/udayanirogi/Documents/Ideas/Projects/PromptCapsule
```

Build distribution files:

```bash
python -m build
```

This creates:
- `dist/promptcapsule-0.1.0.tar.gz` (source distribution)
- `dist/promptcapsule-0.1.0-py3-none-any.whl` (wheel)

Verify build:
```bash
ls -lh dist/
```

---

## Step 5: Test Upload to TestPyPI (Optional but Recommended)

```bash
python -m twine upload --repository testpypi dist/*
```

When prompted:
- **Username**: `__token__`
- **Password**: Your TestPyPI token

Then test installation:
```bash
pip install -i https://test.pypi.org/simple/ promptcapsule
```

---

## Step 6: Upload to Production PyPI

```bash
python -m twine upload dist/*
```

When prompted:
- **Username**: `__token__`
- **Password**: Your PyPI token

---

## Step 7: Verify Publication

### Check on PyPI
1. Visit: https://pypi.org/project/promptcapsule/
2. Verify all information displays correctly

### Test Installation

```bash
pip install promptcapsule
```

Then test it works:

```python
from promptcapsule import PromptCapsule

pc = PromptCapsule()
capsule = pc.compress("Your prompt here")
result = pc.decompress(capsule)
print(result.text)
```

---

## Complete Checklist

- [ ] Create PyPI account (https://pypi.org/account/register/)
- [ ] Generate PyPI token
- [ ] Create `~/.pypirc` with token
- [ ] Install build tools: `pip install build twine wheel`
- [ ] Build package: `python -m build`
- [ ] (Optional) Test on TestPyPI: `python -m twine upload --repository testpypi dist/*`
- [ ] Upload to PyPI: `python -m twine upload dist/*`
- [ ] Verify on https://pypi.org/project/promptcapsule/
- [ ] Test installation: `pip install promptcapsule`
- [ ] Create GitHub Release for v0.1.0

---

## Troubleshooting

### Error: "Invalid distribution"
- Check `pyproject.toml` syntax
- Verify version number is valid

### Error: "Filename already exists"
- Increment version in `pyproject.toml`
- Rebuild with `python -m build`

### Error: "401 Unauthorized"
- Verify token is correct
- Check `~/.pypirc` format
- Try uploading to TestPyPI first

### Package doesn't install
- Verify PyPI page shows your package
- Check package name: `pip install promptcapsule`
- Try: `pip install --upgrade promptcapsule`

---

## Post-Publication

### 1. Create GitHub Release

1. Go to: https://github.com/UdayaNirogi/promptcapsule/releases
2. Click "Create a new release"
3. Fill in:
   - **Tag**: `v0.1.0`
   - **Title**: `PromptCapsule v0.1.0`
   - **Description**: Copy from README.md or changelog
4. Publish

### 2. Update README with Installation

Add to README.md:

```markdown
## Installation

```bash
pip install promptcapsule
```

Or from source:

```bash
git clone https://github.com/UdayaNirogi/promptcapsule.git
cd promptcapsule
pip install -e .
```
```

### 3. Announce on:
- GitHub Discussions
- Twitter/LinkedIn
- Dev.to
- Product Hunt

---

## Quick Command Reference

```bash
# Install build tools
pip install build twine wheel setuptools

# Build package
python -m build

# Upload to TestPyPI (test first)
python -m twine upload --repository testpypi dist/*

# Upload to production PyPI
python -m twine upload dist/*

# Install from PyPI
pip install promptcapsule

# Install in development mode (from local)
pip install -e .

# Check package info
python -m pip show promptcapsule
```

---

## Important Files

Your current `pyproject.toml` is already configured for PyPI:

```toml
[project]
name = "promptcapsule"
version = "0.1.0"
description = "Open-source prompt compression & retrieval library"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.8"
```

This is perfect for PyPI!

---

## Next Steps After Publishing

1. ✅ Publish to PyPI
2. Create GitHub Release
3. Set up GitHub Pages for documentation
4. Announce on social media
5. Monitor PyPI stats
6. Plan v0.2.0 features based on feedback

---

## Resources

- PyPI Help: https://pypi.org/help/
- Twine Documentation: https://twine.readthedocs.io/
- Python Packaging Guide: https://packaging.python.org/
- Semantic Versioning: https://semver.org/

---

**Status**: Ready to publish to PyPI! 🚀

**Next Command**: `python -m build`

---

*Guide created: September 21, 2024*  
*PromptCapsule v0.1.0*
