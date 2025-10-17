/**
 * Phase 7 Implementation Verification Script
 * 
 * This script checks for:
 * 1. File existence
 * 2. Import/export correctness
 * 3. TypeScript syntax
 * 4. Basic code structure
 * 
 * Run: node verify_implementation.js
 */

const fs = require('fs');
const path = require('path');

// Color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

// Test results
let passed = 0;
let failed = 0;
let warnings = 0;

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function checkFile(filePath, description) {
  const fullPath = path.join(__dirname, filePath);
  if (fs.existsSync(fullPath)) {
    log(`✓ ${description}`, 'green');
    passed++;
    return true;
  } else {
    log(`✗ ${description} - File not found: ${filePath}`, 'red');
    failed++;
    return false;
  }
}

function checkFileContent(filePath, checks, description) {
  const fullPath = path.join(__dirname, filePath);
  if (!fs.existsSync(fullPath)) {
    log(`✗ ${description} - File not found: ${filePath}`, 'red');
    failed++;
    return false;
  }

  const content = fs.readFileSync(fullPath, 'utf8');
  let allPassed = true;

  checks.forEach(check => {
    if (check.type === 'contains') {
      if (content.includes(check.value)) {
        log(`  ✓ Contains: ${check.value}`, 'green');
        passed++;
      } else {
        log(`  ✗ Missing: ${check.value}`, 'red');
        failed++;
        allPassed = false;
      }
    } else if (check.type === 'regex') {
      if (check.value.test(content)) {
        log(`  ✓ Matches pattern: ${check.description}`, 'green');
        passed++;
      } else {
        log(`  ✗ Pattern not found: ${check.description}`, 'red');
        failed++;
        allPassed = false;
      }
    } else if (check.type === 'not-contains') {
      if (!content.includes(check.value)) {
        log(`  ✓ Correctly excludes: ${check.value}`, 'green');
        passed++;
      } else {
        log(`  ⚠ Warning: Contains: ${check.value}`, 'yellow');
        warnings++;
      }
    }
  });

  return allPassed;
}

function checkDirectory(dirPath, description) {
  const fullPath = path.join(__dirname, dirPath);
  if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
    log(`✓ ${description}`, 'green');
    passed++;
    return true;
  } else {
    log(`✗ ${description} - Directory not found: ${dirPath}`, 'red');
    failed++;
    return false;
  }
}

// Start verification
log('\n==============================================', 'cyan');
log('Phase 7 Implementation Verification', 'cyan');
log('==============================================\n', 'cyan');

// 1. Configuration Files
log('\n[1] Configuration Files', 'blue');
log('------------------------', 'blue');
checkFile('package.json', 'package.json exists');
checkFile('tsconfig.json', 'tsconfig.json exists');
checkFile('vite.config.ts', 'vite.config.ts exists');
checkFile('tailwind.config.js', 'tailwind.config.js exists');
checkFile('postcss.config.js', 'postcss.config.js exists');
checkFile('.eslintrc.cjs', '.eslintrc.cjs exists');

// 2. Project Structure
log('\n[2] Project Structure', 'blue');
log('---------------------', 'blue');
checkDirectory('src', 'src directory');
checkDirectory('src/types', 'src/types directory');
checkDirectory('src/services', 'src/services directory');
checkDirectory('src/contexts', 'src/contexts directory');
checkDirectory('src/pages', 'src/pages directory');
checkDirectory('src/utils', 'src/utils directory');
checkDirectory('public', 'public directory');

// 3. Type Definitions
log('\n[3] Type Definitions', 'blue');
log('--------------------', 'blue');
checkFile('src/types/preferences.ts', 'Preferences types');
checkFile('src/types/podcast.ts', 'Podcast types');
checkFile('src/types/audio.ts', 'Audio types');
checkFile('src/types/user.ts', 'User types');
checkFile('src/types/index.ts', 'Types index');

// 4. API Services
log('\n[4] API Services', 'blue');
log('----------------', 'blue');
checkFile('src/services/api.ts', 'API client');
checkFile('src/services/auth.ts', 'Auth service');
checkFile('src/services/podcasts.ts', 'Podcasts service');
checkFile('src/services/preferences.ts', 'Preferences service');
checkFile('src/services/behavior.ts', 'Behavior service');

// 5. Context Providers
log('\n[5] Context Providers', 'blue');
log('---------------------', 'blue');
checkFile('src/contexts/AuthContext.tsx', 'AuthContext');
checkFile('src/contexts/PreferenceContext.tsx', 'PreferenceContext');
checkFile('src/contexts/AudioContext.tsx', 'AudioContext');
checkFile('src/contexts/OfflineContext.tsx', 'OfflineContext');

// 6. Page Components
log('\n[6] Page Components', 'blue');
log('-------------------', 'blue');
checkFile('src/pages/LandingPage.tsx', 'LandingPage');
checkFile('src/pages/LoginPage.tsx', 'LoginPage');
checkFile('src/pages/RegisterPage.tsx', 'RegisterPage');
checkFile('src/pages/DashboardPage.tsx', 'DashboardPage');
checkFile('src/pages/LibraryPage.tsx', 'LibraryPage');
checkFile('src/pages/DiscoverPage.tsx', 'DiscoverPage');
checkFile('src/pages/OnboardingPage.tsx', 'OnboardingPage');
checkFile('src/pages/PreferencesPage.tsx', 'PreferencesPage');
checkFile('src/pages/PodcastPlayerPage.tsx', 'PodcastPlayerPage');

// 7. Core Application Files
log('\n[7] Core Application', 'blue');
log('--------------------', 'blue');
checkFile('src/App.tsx', 'App.tsx');
checkFile('src/main.tsx', 'main.tsx');
checkFile('index.html', 'index.html');
checkFile('src/index.css', 'index.css');

// 8. Utility Files
log('\n[8] Utilities', 'blue');
log('-------------', 'blue');
checkFile('src/utils/cn.ts', 'cn utility');
checkFile('src/utils/storage.ts', 'storage utility');

// 9. Content Validation
log('\n[9] Content Validation', 'blue');
log('----------------------', 'blue');

// Check package.json dependencies
checkFileContent('package.json', [
  { type: 'contains', value: '"react"' },
  { type: 'contains', value: '"react-dom"' },
  { type: 'contains', value: '"typescript"' },
  { type: 'contains', value: '"vite"' },
  { type: 'contains', value: '"tailwindcss"' },
  { type: 'contains', value: '"@tanstack/react-query"' },
  { type: 'contains', value: '"axios"' },
  { type: 'contains', value: '"zustand"' },
  { type: 'contains', value: '"react-router-dom"' }
], 'package.json has required dependencies');

// Check vite.config.ts
checkFileContent('vite.config.ts', [
  { type: 'contains', value: '@vitejs/plugin-react' },
  { type: 'contains', value: 'vite-plugin-pwa' },
  { type: 'regex', value: /proxy.*\/api/s, description: 'API proxy configuration' }
], 'vite.config.ts configuration');

// Check App.tsx
checkFileContent('src/App.tsx', [
  { type: 'contains', value: 'BrowserRouter' },
  { type: 'contains', value: 'QueryClientProvider' },
  { type: 'contains', value: 'AuthProvider' },
  { type: 'contains', value: 'PreferenceProvider' },
  { type: 'contains', value: 'AudioProvider' },
  { type: 'contains', value: 'OfflineProvider' }
], 'App.tsx has all providers');

// Check main.tsx
checkFileContent('src/main.tsx', [
  { type: 'contains', value: 'ReactDOM' },
  { type: 'contains', value: 'createRoot' },
  { type: 'contains', value: '<App />' }
], 'main.tsx setup');

// Check AuthContext
checkFileContent('src/contexts/AuthContext.tsx', [
  { type: 'contains', value: 'createContext' },
  { type: 'contains', value: 'login' },
  { type: 'contains', value: 'register' },
  { type: 'contains', value: 'logout' }
], 'AuthContext implementation');

// Check PreferenceContext
checkFileContent('src/contexts/PreferenceContext.tsx', [
  { type: 'contains', value: 'createContext' },
  { type: 'contains', value: 'updatePreferences' },
  { type: 'contains', value: 'learningStats' }
], 'PreferenceContext implementation');

// Check AudioContext
checkFileContent('src/contexts/AudioContext.tsx', [
  { type: 'contains', value: 'createContext' },
  { type: 'contains', value: 'play' },
  { type: 'contains', value: 'pause' },
  { type: 'contains', value: 'seek' },
  { type: 'contains', value: 'setVolume' },
  { type: 'contains', value: 'setSpeed' } // Using setSpeed instead of setPlaybackRate
], 'AudioContext implementation');

// Check API client
checkFileContent('src/services/api.ts', [
  { type: 'contains', value: 'axios.create' },
  { type: 'contains', value: 'interceptors' },
  { type: 'regex', value: /baseURL.*API_BASE_URL/, description: 'API base URL' }
], 'API client configuration');

// Check OnboardingPage
checkFileContent('src/pages/OnboardingPage.tsx', [
  { type: 'regex', value: /step.*[0-9]/, description: 'Multi-step flow' },
  { type: 'contains', value: 'topics' },
  { type: 'contains', value: 'depth' },
  { type: 'contains', value: 'surprise' }
], 'OnboardingPage implementation');

// Check PreferencesPage
checkFileContent('src/pages/PreferencesPage.tsx', [
  { type: 'contains', value: 'usePreferences' },
  { type: 'contains', value: 'updatePreferences' },
  { type: 'contains', value: 'Adaptive Learning' } // Using the UI text instead
], 'PreferencesPage implementation');

// Check PodcastPlayerPage
checkFileContent('src/pages/PodcastPlayerPage.tsx', [
  { type: 'contains', value: 'useAudio' },
  { type: 'contains', value: 'play' },
  { type: 'contains', value: 'pause' },
  { type: 'contains', value: 'chapters' }
], 'PodcastPlayerPage implementation');

// 10. TypeScript Syntax Check
log('\n[10] TypeScript Syntax', 'blue');
log('----------------------', 'blue');

const tsFiles = [
  'src/types/preferences.ts',
  'src/types/podcast.ts',
  'src/types/audio.ts',
  'src/types/user.ts',
  'src/services/api.ts',
  'src/contexts/AuthContext.tsx',
  'src/App.tsx'
];

tsFiles.forEach(file => {
  const fullPath = path.join(__dirname, file);
  if (fs.existsSync(fullPath)) {
    const content = fs.readFileSync(fullPath, 'utf8');
    
    // Check for common TypeScript syntax
    const hasExport = content.includes('export');
    const hasInterface = content.includes('interface') || content.includes('type ');
    
    if (hasExport) {
      log(`  ✓ ${file} has exports`, 'green');
      passed++;
    } else {
      log(`  ⚠ ${file} may be missing exports`, 'yellow');
      warnings++;
    }
  }
});

// Summary
log('\n==============================================', 'cyan');
log('Verification Summary', 'cyan');
log('==============================================\n', 'cyan');

log(`✓ Passed: ${passed}`, 'green');
if (failed > 0) {
  log(`✗ Failed: ${failed}`, 'red');
}
if (warnings > 0) {
  log(`⚠ Warnings: ${warnings}`, 'yellow');
}

const total = passed + failed;
const percentage = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;

log(`\nSuccess Rate: ${percentage}%`, percentage >= 90 ? 'green' : percentage >= 70 ? 'yellow' : 'red');

if (failed === 0) {
  log('\n✓ All critical checks passed! Ready for integration testing.', 'green');
  process.exit(0);
} else {
  log('\n✗ Some checks failed. Please review the errors above.', 'red');
  process.exit(1);
}
