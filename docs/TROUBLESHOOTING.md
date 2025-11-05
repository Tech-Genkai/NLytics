# NLytics Troubleshooting Guide

**Note**: NLytics is a proof-of-concept tool for demonstrating AI-powered code generation. These troubleshooting tips help you get it running for personal use and demos.

## Common Issues & Solutions

### 🚨 Installation Issues

#### "Python version too old"
**Problem:** Python 3.9+ is required

**Solution:**
```bash
# Check your Python version
python --version

# If < 3.9, download from python.org
# Then use the new Python explicitly:
python3.9 start.py
```

#### "pip install fails"
**Problem:** Missing dependencies or pip issues

**Solution:**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Then install requirements
cd backend
pip install -r requirements.txt
```

#### "venv creation fails"
**Problem:** venv module not installed

**Solution:**
```bash
# On Ubuntu/Debian:
sudo apt-get install python3-venv

# On Windows, reinstall Python with "Add Python to PATH" checked
```

---

### 🌐 Server Issues

#### "Address already in use" (Port 5000)
**Problem:** Another application is using port 5000

**Solution:**
```bash
# Option 1: Kill the process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:5000 | xargs kill -9

# Option 2: Change the port in main.py
# Edit backend/main.py, last line:
app.run(debug=True, port=5001, host='0.0.0.0')
```

#### "Cannot connect to server"
**Problem:** Server not running or firewall blocking

**Solution:**
1. Check if server is running (look for "Running on http://...")
2. Try http://127.0.0.1:5000 instead of localhost
3. Check firewall settings
4. Restart the server

#### "404 Not Found"
**Problem:** Wrong URL or routing issue

**Solution:**
- Use http://localhost:5000 (not http://localhost:5000/index.html)
- Clear browser cache
- Check server console for errors

---

### 📁 File Upload Issues

#### "File type not supported"
**Problem:** File extension not allowed

**Supported formats:**
- .csv
- .xlsx (Excel 2007+)
- .xls (Excel 97-2003)

**Solution:**
- Save your file as CSV or Excel format
- Check file extension is correct
- Don't use .txt or other formats

#### "File too large"
**Problem:** File exceeds 50MB limit

**Solution:**
```python
# Increase limit in backend/main.py:
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Or split your data into smaller files
```

#### "Could not read file"
**Problem:** Encoding or format issues

**Common causes:**
- Non-UTF-8 encoding
- Corrupted file
- Wrong delimiter in CSV

**Solution:**
1. Open in Excel and "Save As" → CSV (UTF-8)
2. Check for special characters
3. Verify the file opens in Excel/Numbers

---

### 💬 Query Issues

#### "I don't understand"
**Problem:** Query too vague or column names incorrect

**Solution:**
- Use exact column names from upload confirmation
- Be specific: "average salary" not just "average"
- Mention one thing at a time

#### "Please specify which column"
**Problem:** Missing column name in query

**Solution:**
Include the column name explicitly:
- ❌ "What's the average?"
- ✅ "What's the average salary?"

#### "Column not found"
**Problem:** Column name doesn't match

**Solution:**
- Check exact spelling in upload message
- Remember preprocessing normalizes names:
  - "Employee Name" becomes "employee_name"
  - "Salary ($)" becomes "salary"
- Use underscores instead of spaces

#### "No dataset loaded"
**Problem:** Trying to query before uploading data

**Solution:**
1. Click "📤 Upload Data"
2. Select a file
3. Wait for confirmation
4. Then ask questions

---

### 🎨 UI Issues

#### "Messages not appearing"
**Problem:** JavaScript error or connection issue

**Solution:**
1. Open browser console (F12)
2. Look for errors (red text)
3. Refresh the page
4. Clear browser cache
5. Try a different browser

#### "Upload button doesn't work"
**Problem:** JavaScript not loading

**Solution:**
- Check browser console for errors
- Verify static files are loading (check Network tab in F12)
- Make sure Flask is serving static files correctly

#### "Chat not scrolling"
**Problem:** CSS or JavaScript issue

**Solution:**
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Clear browser cache
- Check browser console for errors

---

### 🧪 Testing Issues

#### "pytest command not found"
**Problem:** pytest not installed or not in PATH

**Solution:**
```bash
# Make sure virtual environment is activated
# Windows:
.\venv\Scripts\Activate.ps1

# Install pytest
pip install pytest

# Run tests
cd backend
pytest tests/ -v
```

#### "Tests failing"
**Problem:** Dependencies or code changes

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Run specific test
pytest tests/test_schema_inspector.py -v

# See detailed output
pytest tests/ -v -s
```

---

### 📊 Data Processing Issues

#### "Preprocessing takes too long"
**Problem:** Large dataset

**Normal processing times:**
- <1,000 rows: <1 second
- 1,000-10,000 rows: 1-3 seconds
- 10,000-100,000 rows: 3-10 seconds
- >100,000 rows: 10-30 seconds

**Solution:**
- This is expected for large datasets
- Consider sampling if you just want to explore
- Upgrade to more powerful hardware for huge datasets

#### "Wrong column types detected"
**Problem:** Type inference issues

**Solution:**
- Check the health report for detected types
- Preprocessing does its best but isn't perfect
- Some ambiguous data may need manual specification (Phase 4+)

#### "Missing data not detected"
**Problem:** Different null representations

**pandas recognizes:**
- Empty cells
- NaN
- None
- "" (empty strings may not be counted)

**Solution:**
- Standardize null values in your source data
- Use empty cells or "NaN" for missing data

---

### 🔧 Development Issues

#### "Changes not showing"
**Problem:** Cache or not reloading

**Solution:**
```bash
# For backend changes:
# Stop server (Ctrl+C) and restart
python main.py

# For frontend changes:
# Hard refresh browser: Ctrl+Shift+R

# For Python code changes with debug mode:
# Flask auto-reloads in debug mode
```

#### "Import errors"
**Problem:** Module not found or circular imports

**Solution:**
```bash
# Make sure you're in the right directory
cd backend

# And __init__.py files exist in all packages
# Check: services/__init__.py, models/__init__.py exist
```

---

### 💾 Data Persistence Issues

#### "Sessions lost after restart"
**Problem:** Sessions stored in memory

**Current behavior:** Sessions are in-memory only

**Solution:**
- This is by design for Phase 1-3
- Phase 6+ will add persistent storage
- For now, sessions reset when server restarts

#### "Uploaded files disappear"
**Problem:** Files not in correct directory

**Solution:**
- Check data/uploads/ directory
- Verify permissions on the folder
- Files are named with UUID prefix

---

## 🆘 Still Having Issues?

### Debug Checklist:

1. ✅ Python 3.9+ installed
2. ✅ Virtual environment activated
3. ✅ All dependencies installed (`pip install -r requirements.txt`)
4. ✅ Server running without errors
5. ✅ Browser console shows no errors (F12)
6. ✅ Correct URL: http://localhost:5000
7. ✅ File format is CSV or Excel
8. ✅ File size under 50MB

### Getting More Information:

**Backend debugging:**
```python
# backend/main.py already has debug=True

# For more details, add logging:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend debugging:**
```javascript
# In browser console (F12):
# Check Network tab for failed requests
# Check Console tab for JavaScript errors
```

### Server Logs

Check the terminal where you ran `python start.py` for:
- Error messages
- Stack traces
- Request logs

---

## 📞 Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Can't start server | Check Python version, install dependencies |
| Can't upload file | Check file format and size |
| Query not working | Upload data first, use exact column names |
| No results showing | Check browser console, refresh page |
| Server crash | Check error in terminal, restart server |
| Tests failing | Reinstall dependencies, check test files |

---

## 🎯 Best Practices

To avoid issues:

1. **Always use the virtual environment**
2. **Keep dependencies updated**
3. **Use supported file formats**
4. **Check column names in upload confirmation**
5. **One query at a time**
6. **Clear browser cache if UI issues**
7. **Check terminal for server errors**
8. **Run tests before making changes**

---

**Need more help?** Check the other documentation:
- **README.md** - Overview, features & quick start
- **AI_SETUP.md** - Groq API key setup guide
- **PROJECT_COMPLETE.md** - Technical architecture

**Happy analyzing! 📊**
