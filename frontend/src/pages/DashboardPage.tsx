/**
 * Dashboard Page
 * Main user dashboard
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Plus, Settings, Library, Compass } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="container py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">Welcome, {user?.name}</span>
            <Link to="/preferences" className="btn-ghost p-2">
              <Settings className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </header>

      <main className="container py-8">
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Link to="/discover" className="card p-6 hover:shadow-md transition-shadow">
            <Compass className="h-8 w-8 text-primary-600 mb-3" />
            <h3 className="font-semibold mb-2">Discover</h3>
            <p className="text-sm text-gray-600">Explore new locations</p>
          </Link>

          <Link to="/library" className="card p-6 hover:shadow-md transition-shadow">
            <Library className="h-8 w-8 text-primary-600 mb-3" />
            <h3 className="font-semibold mb-2">Library</h3>
            <p className="text-sm text-gray-600">Your saved podcasts</p>
          </Link>

          <Link to="/generate" className="card p-6 hover:shadow-md transition-shadow text-left">
            <Plus className="h-8 w-8 text-primary-600 mb-3" />
            <h3 className="font-semibold mb-2">Generate</h3>
            <p className="text-sm text-gray-600">Create new podcast</p>
          </Link>
        </div>

        <div className="card p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Podcasts</h2>
          <p className="text-gray-600">No podcasts yet. Start by generating your first one!</p>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;
