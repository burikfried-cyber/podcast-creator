/**
 * Landing Page
 * Public homepage with app introduction
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Play, Sparkles, Globe, Headphones } from 'lucide-react';

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="container py-6">
        <nav className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Globe className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">LocationPodcast</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link to="/login" className="btn-ghost px-4 py-2">
              Login
            </Link>
            <Link to="/register" className="btn-primary px-4 py-2">
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main id="main-content" className="container py-20">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Discover the World Through
            <span className="text-primary-600"> Personalized Podcasts</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Generate custom podcasts about any location worldwide, tailored to your interests and preferences.
          </p>
          <div className="flex items-center justify-center space-x-4">
            <Link to="/register" className="btn-primary px-8 py-3 text-lg">
              Start Exploring
            </Link>
            <button className="btn-ghost px-8 py-3 text-lg flex items-center space-x-2">
              <Play className="h-5 w-5" />
              <span>Watch Demo</span>
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-20 max-w-5xl mx-auto">
          <div className="card p-6 text-center">
            <div className="flex justify-center mb-4">
              <Sparkles className="h-12 w-12 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">AI-Powered Content</h3>
            <p className="text-gray-600">
              Advanced AI generates engaging narratives about any location
            </p>
          </div>

          <div className="card p-6 text-center">
            <div className="flex justify-center mb-4">
              <Headphones className="h-12 w-12 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Personalized Experience</h3>
            <p className="text-gray-600">
              Adapts to your interests, depth preferences, and listening habits
            </p>
          </div>

          <div className="card p-6 text-center">
            <div className="flex justify-center mb-4">
              <Globe className="h-12 w-12 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Global Coverage</h3>
            <p className="text-gray-600">
              Explore any location worldwide with rich, detailed content
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LandingPage;
