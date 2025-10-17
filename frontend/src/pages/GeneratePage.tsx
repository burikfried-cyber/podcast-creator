/**
 * Generate Podcast Page
 * Beautiful interface for generating location-based podcasts
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { podcastService } from '@/services/podcasts';
import { PodcastGenerationRequest } from '@/types';

const PODCAST_TYPES = [
  {
    id: 'base',
    name: 'Base',
    icon: '📚',
    description: 'Essential information, balanced depth',
    color: 'from-blue-500 to-blue-600'
  },
  {
    id: 'standout',
    name: 'Standout',
    icon: '⭐',
    description: 'Remarkable discoveries, mystery focus',
    color: 'from-purple-500 to-purple-600'
  },
  {
    id: 'topic',
    name: 'Topic',
    icon: '🎯',
    description: 'Deep dive, expert-level content',
    color: 'from-indigo-500 to-indigo-600'
  },
  {
    id: 'personalized',
    name: 'Personal',
    icon: '💫',
    description: 'Tailored to your preferences',
    color: 'from-pink-500 to-pink-600'
  }
];

const LENGTHS = [
  { value: 'short', label: 'Short', duration: '5-8 min' },
  { value: 'medium', label: 'Medium', duration: '10-15 min' },
  { value: 'long', label: 'Long', duration: '15-20 min' }
];

export default function GeneratePage() {
  const navigate = useNavigate();
  const [location, setLocation] = useState('');
  const [selectedType, setSelectedType] = useState('base');
  const [length, setLength] = useState('medium');
  const [surpriseTolerance, setSurpriseTolerance] = useState(2);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!location.trim()) {
      setError('Please enter a location');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const request: PodcastGenerationRequest = {
        location: location.trim(),
        podcast_type: selectedType,
        preferences: {
          surprise_tolerance: surpriseTolerance,
          preferred_length: length,
          preferred_style: 'balanced',
          preferred_pace: 'moderate',
          interests: []
        }
      };

      const response = await podcastService.generatePodcast(request);
      
      // Navigate to progress page
      navigate(`/progress/${response.job_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to start podcast generation');
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🎙️ Generate Your Podcast
          </h1>
          <p className="text-lg text-gray-600">
            Create a personalized podcast about any location in the world
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 space-y-8">
          {/* Location Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📍 Where are you going?
            </label>
            <div className="relative">
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g., Paris, France"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-lg"
                disabled={isGenerating}
              />
              <div className="absolute right-3 top-3 text-gray-400">
                🔍
              </div>
            </div>
          </div>

          {/* Podcast Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-4">
              🎯 Choose Your Style
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {PODCAST_TYPES.map((type) => (
                <button
                  key={type.id}
                  onClick={() => setSelectedType(type.id)}
                  disabled={isGenerating}
                  className={`
                    relative p-4 rounded-xl border-2 transition-all duration-200
                    ${selectedType === type.id
                      ? 'border-indigo-500 bg-indigo-50 shadow-lg scale-105'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
                    }
                    ${isGenerating ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  <div className="text-4xl mb-2">{type.icon}</div>
                  <div className="font-semibold text-gray-900 mb-1">{type.name}</div>
                  <div className="text-xs text-gray-600">{type.description}</div>
                  {selectedType === type.id && (
                    <div className="absolute top-2 right-2 text-indigo-500">✓</div>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Length Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-4">
              ⏱️ Podcast Length
            </label>
            <div className="grid grid-cols-3 gap-4">
              {LENGTHS.map((len) => (
                <button
                  key={len.value}
                  onClick={() => setLength(len.value)}
                  disabled={isGenerating}
                  className={`
                    p-4 rounded-lg border-2 transition-all duration-200
                    ${length === len.value
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                    }
                    ${isGenerating ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  <div className="font-semibold text-gray-900">{len.label}</div>
                  <div className="text-sm text-gray-600">{len.duration}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Surprise Tolerance */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🎲 Surprise Level: {surpriseTolerance}
            </label>
            <input
              type="range"
              min="0"
              max="5"
              value={surpriseTolerance}
              onChange={(e) => setSurpriseTolerance(parseInt(e.target.value))}
              disabled={isGenerating}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <div className="flex justify-between text-xs text-gray-600 mt-1">
              <span>Familiar</span>
              <span>Balanced</span>
              <span>Adventurous</span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <span className="text-red-600 mr-2">⚠️</span>
                <span className="text-red-800">{error}</span>
              </div>
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating || !location.trim()}
            className={`
              w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all duration-200
              ${isGenerating || !location.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700 shadow-lg hover:shadow-xl transform hover:scale-105'
              }
            `}
          >
            {isGenerating ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Generating...
              </span>
            ) : (
              '✨ Generate Podcast'
            )}
          </button>
        </div>

        {/* Tips Section */}
        <div className="mt-8 bg-blue-50 rounded-xl p-6">
          <h3 className="font-semibold text-blue-900 mb-3">💡 Tips for Best Results</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li>• Be specific with locations (e.g., "Eiffel Tower, Paris" vs just "Paris")</li>
            <li>• Choose "Standout" for unique, lesser-known facts</li>
            <li>• Increase surprise level for more adventurous content</li>
            <li>• Generation typically takes 1-3 minutes</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
