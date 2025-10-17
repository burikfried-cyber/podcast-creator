# Location Podcast Generator - Frontend

Modern React 18 + TypeScript frontend application with PWA capabilities.

## 🚀 Features

- **React 18** with TypeScript
- **Progressive Web App (PWA)** with offline support
- **Advanced Audio Player** with behavioral tracking
- **User Preference Management** with adaptive learning
- **Responsive Design** with Tailwind CSS
- **Accessibility** WCAG 2.1 AA compliant
- **Code Splitting** for optimal performance

## 📦 Tech Stack

- **React 18.2** - UI framework
- **TypeScript 5.3** - Type safety
- **Vite 5.0** - Build tool
- **React Router 6.20** - Routing
- **TanStack Query 5.12** - Data fetching
- **Zustand 4.4** - State management
- **Tailwind CSS 3.3** - Styling
- **Framer Motion 10.16** - Animations
- **Lucide React** - Icons

## 🛠️ Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Build for production:**
   ```bash
   npm run build
   ```

## 📁 Project Structure

```
src/
├── components/       # React components
├── contexts/         # React contexts (Auth, Preferences, Audio, Offline)
├── hooks/            # Custom hooks
├── pages/            # Page components
├── services/         # API services
├── types/            # TypeScript types
├── utils/            # Utility functions
├── App.tsx           # Main app component
├── main.tsx          # Entry point
└── index.css         # Global styles
```

## 🎯 Key Components

### Contexts
- **AuthContext** - User authentication
- **PreferenceContext** - User preferences and learning
- **AudioContext** - Audio player state and controls
- **OfflineContext** - Offline state and sync

### Pages
- **LandingPage** - Public homepage
- **LoginPage** - User login
- **RegisterPage** - User registration
- **OnboardingPage** - Interactive onboarding flow
- **DashboardPage** - Main user dashboard
- **PodcastPlayerPage** - Advanced audio player
- **PreferencesPage** - Preference management
- **LibraryPage** - Podcast library
- **DiscoverPage** - Location discovery

## 🔧 Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler check
- `npm run format` - Format code with Prettier

### Code Quality

- **ESLint** for code linting
- **TypeScript** for type checking
- **Prettier** for code formatting

## 🌐 PWA Features

- **Offline Support** - Works without internet
- **Install Prompt** - Add to home screen
- **Service Worker** - Background sync and caching
- **Push Notifications** - (Future feature)

## ♿ Accessibility

- **WCAG 2.1 AA** compliant
- **Keyboard Navigation** - Full keyboard support
- **Screen Reader** - ARIA labels and semantic HTML
- **Focus Management** - Visible focus indicators
- **Color Contrast** - Meets contrast requirements

## 📱 Responsive Design

- **Mobile First** - Optimized for mobile devices
- **Tablet Support** - Responsive layouts
- **Desktop** - Full-featured experience

## 🚀 Performance

- **Code Splitting** - Lazy loading routes
- **Tree Shaking** - Remove unused code
- **Image Optimization** - WebP with fallbacks
- **Caching** - Service worker caching strategies

## 📄 License

Private - All rights reserved
