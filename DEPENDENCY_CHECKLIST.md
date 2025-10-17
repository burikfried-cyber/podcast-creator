# 📦 Complete Dependency Checklist

## 🎯 Purpose
This checklist ensures you have all required dependencies installed before integration testing.

---

## ✅ System Requirements

### **Operating System**
- [x] Windows 10/11 (You're on Windows)
- [ ] macOS 10.15+ (Alternative)
- [ ] Linux (Ubuntu 20.04+) (Alternative)

### **Required Software**

#### **1. Node.js** ⭐ CRITICAL
- **Version Required:** 18.x or 20.x (LTS recommended)
- **Check Command:** `node --version`
- **Expected Output:** `v18.x.x` or `v20.x.x`
- **Download:** https://nodejs.org/
- **Installation:**
  1. Download Windows Installer (.msi)
  2. Run installer with default options
  3. Restart terminal after installation
  4. Verify: `node --version`

#### **2. npm** ⭐ CRITICAL
- **Version Required:** 9.x or 10.x
- **Check Command:** `npm --version`
- **Expected Output:** `9.x.x` or `10.x.x`
- **Note:** Comes automatically with Node.js
- **If missing:** Reinstall Node.js

#### **3. Python** ⭐ CRITICAL
- **Version Required:** 3.11 or 3.12
- **Check Command:** `python --version` or `python3 --version`
- **Expected Output:** `Python 3.11.x` or `Python 3.12.x`
- **Download:** https://www.python.org/downloads/
- **Installation:**
  1. Download Windows Installer
  2. ✅ CHECK "Add Python to PATH"
  3. Click "Install Now"
  4. Restart terminal
  5. Verify: `python --version`

#### **4. pip** ⭐ CRITICAL
- **Version Required:** 23.x+
- **Check Command:** `pip --version` or `pip3 --version`
- **Expected Output:** `pip 23.x.x`
- **Note:** Comes automatically with Python
- **If outdated:** `python -m pip install --upgrade pip`

---

## 📦 Backend Dependencies

### **Python Virtual Environment**
```powershell
# Navigate to backend
cd C:\Users\burik\podcastCreator2\backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Core Backend Packages**

#### **Web Framework** ⭐ CRITICAL
```
fastapi==0.104.0+
uvicorn[standard]==0.24.0+
```
**Purpose:** API server and ASGI server

#### **Database** ⭐ CRITICAL
```
sqlalchemy==2.0.0+
alembic==1.12.0+
```
**Purpose:** ORM and database migrations

#### **Data Validation** ⭐ CRITICAL
```
pydantic==2.4.0+
pydantic-settings==2.0.0+
```
**Purpose:** Data validation and settings management

#### **Authentication** ⭐ CRITICAL
```
python-jose[cryptography]==3.3.0+
passlib[bcrypt]==1.7.4+
```
**Purpose:** JWT tokens and password hashing

#### **File Handling**
```
python-multipart==0.0.6+
aiofiles==23.2.0+
```
**Purpose:** File uploads and async file operations

#### **HTTP Client**
```
httpx==0.25.0+
```
**Purpose:** Async HTTP requests

#### **Task Queue** (Optional)
```
redis==5.0.0+
celery==5.3.0+
```
**Purpose:** Background task processing

#### **Cloud Storage** (Optional)
```
boto3==1.28.0+
```
**Purpose:** AWS S3 integration

#### **TTS Providers** (Optional)
```
google-cloud-texttospeech==2.14.0+
azure-cognitiveservices-speech==1.31.0+
```
**Purpose:** Premium TTS services

#### **Audio Processing** ⭐ CRITICAL
```
pydub==0.25.1+
numpy==1.24.0+
scipy==1.11.0+
librosa==0.10.0+
soundfile==0.12.0+
```
**Purpose:** Audio manipulation and analysis

#### **Testing**
```
pytest==7.4.0+
pytest-asyncio==0.21.0+
pytest-cov==4.1.0+
```
**Purpose:** Unit and integration testing

### **Install All Backend Dependencies**
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Upgrade pip first
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### **Verify Backend Installation**
```powershell
# Should see all packages listed
pip list | Select-String "fastapi"
pip list | Select-String "sqlalchemy"
pip list | Select-String "pydantic"
pip list | Select-String "uvicorn"
```

---

## 🎨 Frontend Dependencies

### **Node Modules Directory**
```powershell
# Navigate to frontend
cd C:\Users\burik\podcastCreator2\frontend

# Install all dependencies
npm install

# OR clean install (recommended)
npm ci
```

### **Core Frontend Packages**

#### **React Framework** ⭐ CRITICAL
```json
{
  "react": "^18.3.1",
  "react-dom": "^18.3.1"
}
```
**Purpose:** UI library

#### **TypeScript** ⭐ CRITICAL
```json
{
  "typescript": "^5.3.3"
}
```
**Purpose:** Type safety

#### **Routing** ⭐ CRITICAL
```json
{
  "react-router-dom": "^6.20.0"
}
```
**Purpose:** Client-side routing

#### **State Management** ⭐ CRITICAL
```json
{
  "@tanstack/react-query": "^5.13.4",
  "zustand": "^4.4.7"
}
```
**Purpose:** Server state and client state management

#### **HTTP Client** ⭐ CRITICAL
```json
{
  "axios": "^1.6.2"
}
```
**Purpose:** API requests

#### **Styling** ⭐ CRITICAL
```json
{
  "tailwindcss": "^3.3.6",
  "postcss": "^8.4.32",
  "autoprefixer": "^10.4.16"
}
```
**Purpose:** CSS framework

#### **UI Utilities**
```json
{
  "clsx": "^2.0.0",
  "tailwind-merge": "^2.1.0",
  "lucide-react": "^0.294.0"
}
```
**Purpose:** Class name utilities and icons

#### **PWA** ⭐ CRITICAL
```json
{
  "vite-plugin-pwa": "^0.17.4",
  "workbox-window": "^7.0.0"
}
```
**Purpose:** Progressive Web App capabilities

#### **Build Tools** ⭐ CRITICAL
```json
{
  "vite": "^5.0.8",
  "@vitejs/plugin-react": "^4.2.1"
}
```
**Purpose:** Build and development server

#### **Development Tools**
```json
{
  "@types/node": "^20.10.5",
  "@types/react": "^18.2.45",
  "@types/react-dom": "^18.2.18",
  "@typescript-eslint/eslint-plugin": "^6.15.0",
  "@typescript-eslint/parser": "^6.15.0",
  "eslint": "^8.56.0",
  "eslint-plugin-react-hooks": "^4.6.0",
  "eslint-plugin-react-refresh": "^0.4.5"
}
```
**Purpose:** Type definitions and linting

### **Verify Frontend Installation**
```powershell
# Check if node_modules exists
Test-Path node_modules

# Check specific packages
Test-Path node_modules\react
Test-Path node_modules\typescript
Test-Path node_modules\vite
Test-Path node_modules\tailwindcss

# List all installed packages
npm list --depth=0
```

---

## 🔍 Verification Commands

### **Quick Verification Script**
```powershell
# Save this as check_dependencies.ps1

Write-Host "Checking System Dependencies..." -ForegroundColor Cyan

# Node.js
Write-Host "`n[1] Node.js:" -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "  ✓ Installed: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Not installed" -ForegroundColor Red
}

# npm
Write-Host "`n[2] npm:" -ForegroundColor Yellow
try {
    $npmVersion = npm --version
    Write-Host "  ✓ Installed: v$npmVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Not installed" -ForegroundColor Red
}

# Python
Write-Host "`n[3] Python:" -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "  ✓ Installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Not installed" -ForegroundColor Red
}

# pip
Write-Host "`n[4] pip:" -ForegroundColor Yellow
try {
    $pipVersion = pip --version
    Write-Host "  ✓ Installed: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Not installed" -ForegroundColor Red
}

# Backend venv
Write-Host "`n[5] Backend Virtual Environment:" -ForegroundColor Yellow
if (Test-Path "backend\venv") {
    Write-Host "  ✓ Exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ Not found" -ForegroundColor Red
}

# Frontend node_modules
Write-Host "`n[6] Frontend Node Modules:" -ForegroundColor Yellow
if (Test-Path "frontend\node_modules") {
    Write-Host "  ✓ Exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ Not found" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Verification Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
```

### **Run Verification**
```powershell
cd C:\Users\burik\podcastCreator2
.\check_dependencies.ps1
```

---

## 🐛 Troubleshooting

### **Issue: "python is not recognized"**
**Solution:**
1. Reinstall Python with "Add to PATH" checked
2. OR manually add to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\Users\burik\AppData\Local\Programs\Python\Python311`
   - Add: `C:\Users\burik\AppData\Local\Programs\Python\Python311\Scripts`
3. Restart terminal

### **Issue: "node is not recognized"**
**Solution:**
1. Reinstall Node.js
2. Restart terminal
3. Verify: `node --version`

### **Issue: "Cannot activate virtual environment"**
**Solution:**
```powershell
# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Try activating again
.\venv\Scripts\Activate.ps1
```

### **Issue: "pip install fails with SSL error"**
**Solution:**
```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Try with --trusted-host
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### **Issue: "npm install fails"**
**Solution:**
```powershell
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json

# Reinstall
npm install
```

### **Issue: "Port already in use"**
**Solution:**
```powershell
# Find process using port 8000 (backend)
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Find process using port 5173 (frontend)
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

---

## ✅ Final Checklist

### **Before Integration Testing**
- [ ] Node.js 18.x or 20.x installed
- [ ] npm 9.x or 10.x installed
- [ ] Python 3.11+ installed
- [ ] pip 23.x+ installed
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed (pip list shows 30+ packages)
- [ ] Frontend node_modules installed (folder exists)
- [ ] Frontend dependencies installed (npm list shows 50+ packages)
- [ ] No installation errors
- [ ] All verification commands pass

### **Installation Commands Summary**
```powershell
# Backend
cd C:\Users\burik\podcastCreator2\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Frontend
cd C:\Users\burik\podcastCreator2\frontend
npm install

# Verify
cd C:\Users\burik\podcastCreator2\frontend
node verify_implementation.js
```

---

## 🚀 Ready to Test!

Once all checkboxes are checked, you're ready to:
1. ✅ Start backend server
2. ✅ Start frontend server
3. ✅ Run integration tests

**See INTEGRATION_TESTING_GUIDE.md for detailed testing instructions!**

---

## 📞 Need Help?

If you encounter issues:
1. Check this checklist again
2. Review error messages carefully
3. Search for specific error online
4. Check official documentation:
   - Node.js: https://nodejs.org/docs/
   - Python: https://docs.python.org/
   - React: https://react.dev/
   - FastAPI: https://fastapi.tiangolo.com/

**You've got this! 💪**
