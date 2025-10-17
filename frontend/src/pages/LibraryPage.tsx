/**
 * Library Page
 * User's podcast library with grid view and filters
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { podcastService } from '@/services/podcasts';
import { PodcastLibraryItem } from '@/types';

export default function LibraryPage() {
  const navigate = useNavigate();
  const [podcasts, setPodcasts] = useState<PodcastLibraryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadPodcasts();
  }, [filter]);

  const loadPodcasts = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('📚 Loading library...', { filter });
      
      const startTime = Date.now();
      const response = await podcastService.getLibrary({
        limit: 50,
        status_filter: filter === 'all' ? undefined : filter
      });
      const duration = Date.now() - startTime;
      
      console.log('✅ Library loaded:', {
        count: response.podcasts.length,
        duration: `${duration}ms`
      });
      
      setPodcasts(response.podcasts);
    } catch (err: any) {
      console.error('❌ Failed to load library:', err);
      setError(err.message || 'Failed to load podcasts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filteredPodcasts = podcasts.filter(podcast =>
    podcast.location?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    podcast.title?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const badges = {
      completed: { bg: 'bg-green-100', text: 'text-green-800', label: '✓ Complete' },
      processing: { bg: 'bg-blue-100', text: 'text-blue-800', label: '⏳ Processing' },
      failed: { bg: 'bg-red-100', text: 'text-red-800', label: '✗ Failed' },
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: '⏸️ Pending' }
    };
    const badge = badges[status as keyof typeof badges] || badges.pending;
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    return `${mins} min`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">📚 Your Library</h1>
            <p className="text-gray-600">
              {podcasts.length} podcast{podcasts.length !== 1 ? 's' : ''} in your collection
            </p>
          </div>
          <button
            onClick={() => navigate('/generate')}
            className="mt-4 md:mt-0 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all"
          >
            ✨ Generate New Podcast
          </button>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search by location or title..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <div className="absolute left-3 top-2.5 text-gray-400">🔍</div>
              </div>
            </div>

            {/* Status Filter */}
            <div className="flex gap-2">
              {['all', 'completed', 'processing', 'failed'].map((status) => (
                <button
                  key={status}
                  onClick={() => setFilter(status)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    filter === status
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin text-6xl">⚙️</div>
            <p className="mt-4 text-gray-600">Loading your podcasts...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6 text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <div className="text-red-900 font-semibold mb-2">Failed to Load Library</div>
            <div className="text-red-700 mb-4">{error}</div>
            <button
              onClick={loadPodcasts}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && filteredPodcasts.length === 0 && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <div className="text-6xl mb-4">🎙️</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">No Podcasts Yet</h3>
            <p className="text-gray-600 mb-6">
              {searchQuery
                ? 'No podcasts match your search'
                : 'Start by generating your first podcast!'}
            </p>
            {!searchQuery && (
              <button
                onClick={() => navigate('/generate')}
                className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 shadow-lg transition-all"
              >
                Generate Your First Podcast
              </button>
            )}
          </div>
        )}

        {/* Podcast Grid */}
        {!loading && !error && filteredPodcasts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPodcasts.map((podcast) => (
              <div
                key={podcast.id}
                onClick={() => podcast.status === 'completed' && navigate(`/podcast/${podcast.id}`)}
                className={`bg-white rounded-xl shadow-md overflow-hidden transition-all duration-200 ${
                  podcast.status === 'completed'
                    ? 'hover:shadow-xl hover:scale-105 cursor-pointer'
                    : 'opacity-75'
                }`}
              >
                {/* Cover Image */}
                <div className="h-48 bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center">
                  <div className="text-6xl">
                    {podcast.status === 'completed' ? '🗺️' : '⏳'}
                  </div>
                </div>

                {/* Content */}
                <div className="p-6">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-bold text-gray-900 line-clamp-2">
                      {podcast.title || podcast.location}
                    </h3>
                    {getStatusBadge(podcast.status)}
                  </div>

                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {podcast.description || `Podcast about ${podcast.location}`}
                  </p>

                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>⏱️ {formatDuration(podcast.duration_seconds)}</span>
                    <span>📅 {formatDate(podcast.created_at)}</span>
                  </div>

                  {podcast.status === 'completed' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/podcast/${podcast.id}`);
                      }}
                      className="mt-4 w-full py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                    >
                      ▶️ Play Podcast
                    </button>
                  )}

                  {podcast.status === 'processing' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/progress/${podcast.id}`);
                      }}
                      className="mt-4 w-full py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                    >
                      View Progress
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
