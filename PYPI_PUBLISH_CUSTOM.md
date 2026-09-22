# Publishing PromptCapsule to PyPI

**Your PyPI Username**: `Data.PyCap-1`  
**Package Name**: `promptcapsule`  
**Version**: 0.1.0  
**Status**: Ready to publish

---

## 🚀 Step-by-Step Publishing Guide

### Step 1: Log in to PyPI

Go to: https://pypi.org

- **Username**: `Data.PyCap-1`
- **Password**: Your PyPI password

### Step 2: Create API Token

1. Once logged in, go to Account Settings → API tokens
2. Click "Create new token"
3. Name it: `promptcapsule-publish`
4. Scope: "Entire account"
5. Copy the token (starts with `pypi-`)
6. **Save it securely** - you won't see it again!

Example token format:
```
pypi-AgEIcHlwaS5vcmc...
```

### Step 3: Configure .pypirc (Local Authentication)

Create or edit `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi

[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE_DATA_PYCAP-1
```

**Security**: Never commit this file to git! Add to `.gitignore`.

### Step 4: Install Build Tools

```bash
pip install build twine wheel setuptools
```

### Step 5: Build Your Package

Navigate to your project:

```bash
cd /Users/udayanirogi/Documents/Ideas/Projects/PromptCapsule
```

Build distribution files:

```bash
python -m build
```

This creates:
- `dist/promptcapsule-0.1.0.tar.gz`
- `dist/promptcapsule-0.1.0-py3-none-any.whl`

Verify:
```bash
ls -lh dist/
```

### Step 6: Upload to PyPI

```bash
python -m twine upload dist/*
```

When prompted:
- **Username**: `__token__`
- **Password**: Your PyPI token (paste from Step 2)

### Step 7: Verify on PyPI

1. Visit: https://pypi.org/project/promptcapsule/
2. Check that all information displays correctly
3. Version should show: 0.1.0
4. Author: Udaya Nirogi

### Step 8: Test Installation

```bash
pip install promptcapsule
```

Test it works:

```python
from promptcapsule import PromptCapsule

pc = PromptCapsule()
capsule = pc.compress("Test prompt")
result = pc.decompress(capsule)
print(result.text)  # Should print: Test prompt
```

---

## 📋 Pre-Publish Checklist

- [ ] Have your PyPI account: `Data.PyCap-1`
- [ ] Generated API token from PyPI
- [ ] Created/updated `~/.pypirc` with token
- [ ] Installed build tools: `pip install build twine`
- [ ] Current directory: `/Users/udayanirogi/Documents/Ideas/Projects/PromptCapsule`
- [ ] Built package: `python -m build`
- [ ] Verified dist/ contains `.tar.gz` and `.whl` files

---

## 🎯 Quick Command Summary

```bash
# Install tools
pip install build twine wheel setuptools

# Navigate to project
cd /Users/udayanirogi/Documents/Ideas/Projects/PromptCapsule

# Build
python -m build

# Upload (will prompt for username/token)
python -m twine upload dist/*

# Test
pip install promptcapsule

# Verify
python -c "from promptcapsule import PromptCapsule; print('✅ Success!')"
```

---

## 💡 Optional: Test on TestPyPI First (Recommended)

Before publishing to production PyPI:

1. Create TestPyPI account: https://test.pypi.org/account/register/
2. Generate TestPyPI API token
3. Test upload:

```bash
python -m twine upload --repository testpypi dist/*
```

4. Test installation:

```bash
pip install -i https://test.pypi.org/simple/ promptcapsule
```

This lets you verify everything works before production!

---

## 🔐 Security Notes

✓ Use API tokens, not passwords  
✓ Store `.pypirc` securely (not in git)  
✓ Use unique tokens for each project if possible  
✓ Regenerate tokens periodically  
✓ TestPyPI is good for testing before production  

---

## 📊 After Publishing

1. **Create GitHub Release**:
   - Go to: https://github.com/UdayaNirogi/promptcapsule/releases
   - Create release for v0.1.0
   - Link to PyPI page

2. **Update README**:
   ```markdown
   ## Installation

   ```bash
   pip install promptcapsule
   ```
   ```

3. **Announce**:
   - Twitter/LinkedIn
   - Dev.to
   - Reddit (r/Python, r/opensource)
   - Product Hunt

4. **Monitor**:
   - PyPI stats: https://pypi.org/project/promptcapsule/
   - GitHub issues/discussions

---

## ✨ You're Ready!

Everything is set up. When you're ready:

1. Generate your PyPI token
2. Configure ~/.pypirc
3. Run `python -m build`
4. Run `python -m twine upload dist/*`

That's it! 🚀

---

**PyPI Username**: `Data.PyCap-1`  
**Package**: `promptcapsule` v0.1.0  
**Status**: READY FOR PUBLICATION  
**Location**: /Users/udayanirogi/Documents/Ideas/Projects/PromptCapsule

---

*Last updated: September 22, 2026*
