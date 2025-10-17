/**
 * Preferences Page
 * Comprehensive user preference management interface
 */
import React, { useState } from 'react';
import { usePreferences } from '@/contexts/PreferenceContext';
import { TOPIC_CATEGORIES, DEPTH_LABELS } from '@/types';
import { Save, RotateCcw, TrendingUp, Settings } from 'lucide-react';

const PreferencesPage: React.FC = () => {
  const { preferences, learningStats, recentAdaptations, updatePreferences, toggleLearning, resetPreferences, isLoading } = usePreferences();
  const [hasChanges, setHasChanges] = useState(false);
  const [localPrefs, setLocalPrefs] = useState(preferences);

  const handleTopicChange = (topic: string, weight: number) => {
    setLocalPrefs(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        topics: {
          ...prev.topics,
          [topic]: { weight, subcategories: {} }
        }
      };
    });
    setHasChanges(true);
  };

  const handleDepthChange = (depth: number) => {
    setLocalPrefs(prev => prev ? { ...prev, depthPreference: depth } : prev);
    setHasChanges(true);
  };

  const handleSurpriseChange = (surprise: number) => {
    setLocalPrefs(prev => prev ? { ...prev, surpriseTolerance: surprise } : prev);
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!localPrefs) return;
    try {
      await updatePreferences({
        topics: localPrefs.topics,
        depthPreference: localPrefs.depthPreference,
        surpriseTolerance: localPrefs.surpriseTolerance
      });
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }
  };

  const handleReset = async () => {
    if (confirm('Are you sure you want to reset all preferences to defaults?')) {
      try {
        await resetPreferences();
        setHasChanges(false);
      } catch (error) {
        console.error('Failed to reset preferences:', error);
      }
    }
  };

  const handleToggleLearning = async () => {
    if (!preferences) return;
    try {
      await toggleLearning(!preferences.learningEnabled);
    } catch (error) {
      console.error('Failed to toggle learning:', error);
    }
  };

  if (isLoading || !localPrefs) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="container py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Settings className="h-6 w-6 text-primary-600" />
              <h1 className="text-2xl font-bold">Preferences</h1>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleReset}
                className="btn-ghost px-4 py-2 flex items-center space-x-2"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Reset</span>
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges}
                className="btn-primary px-4 py-2 flex items-center space-x-2"
              >
                <Save className="h-4 w-4" />
                <span>Save Changes</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="container py-8 max-w-5xl">
        <div className="space-y-8">
          {/* Topic Preferences */}
          <section className="card p-6">
            <h2 className="text-xl font-semibold mb-4">Topic Interests</h2>
            <p className="text-gray-600 mb-6">
              Adjust how interested you are in each topic (0 = not interested, 10 = very interested)
            </p>
            
            <div className="space-y-4">
              {TOPIC_CATEGORIES.map(topic => {
                const weight = localPrefs.topics[topic]?.weight || 0;
                return (
                  <div key={topic} className="flex items-center space-x-4">
                    <label className="w-32 font-medium text-sm">{topic}</label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={weight}
                      onChange={(e) => handleTopicChange(topic, parseFloat(e.target.value))}
                      className="flex-1"
                    />
                    <span className="w-12 text-right text-sm font-medium">
                      {Math.round(weight * 10)}/10
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Depth Preference */}
          <section className="card p-6">
            <h2 className="text-xl font-semibold mb-4">Content Depth</h2>
            <p className="text-gray-600 mb-6">
              How detailed should the content be?
            </p>

            <div className="space-y-3">
              {DEPTH_LABELS.map((label, index) => (
                <button
                  key={label}
                  onClick={() => handleDepthChange(index + 1)}
                  className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                    localPrefs.depthPreference === index + 1
                      ? 'border-primary-600 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{label}</div>
                      <div className="text-sm text-gray-600">
                        {index === 0 && 'Quick overview, main highlights'}
                        {index === 1 && 'Basic information with some context'}
                        {index === 2 && 'Balanced depth with interesting details'}
                        {index === 3 && 'Detailed exploration with analysis'}
                        {index === 4 && 'Expert-level insights and connections'}
                        {index === 5 && 'Academic depth with comprehensive coverage'}
                      </div>
                    </div>
                    {localPrefs.depthPreference === index + 1 && (
                      <div className="w-6 h-6 bg-primary-600 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-white rounded-full"></div>
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </section>

          {/* Surprise Tolerance */}
          <section className="card p-6">
            <h2 className="text-xl font-semibold mb-4">Surprise Level</h2>
            <p className="text-gray-600 mb-6">
              How much unexpected content would you like?
            </p>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Predictable</span>
              <input
                type="range"
                min="1"
                max="5"
                value={localPrefs.surpriseTolerance}
                onChange={(e) => handleSurpriseChange(parseInt(e.target.value))}
                className="flex-1"
              />
              <span className="text-sm text-gray-600">Surprising</span>
              <span className="w-12 text-right font-medium">
                {localPrefs.surpriseTolerance}/5
              </span>
            </div>

            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-700">
                {localPrefs.surpriseTolerance === 1 && 'Stick to what you know - predictable content'}
                {localPrefs.surpriseTolerance === 2 && 'Mostly familiar with occasional surprises'}
                {localPrefs.surpriseTolerance === 3 && 'Balanced mix of expected and unexpected'}
                {localPrefs.surpriseTolerance === 4 && 'Frequently surprise you with new angles'}
                {localPrefs.surpriseTolerance === 5 && 'Maximum surprise - show the unexpected!'}
              </p>
            </div>
          </section>

          {/* Adaptive Learning */}
          <section className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <TrendingUp className="h-6 w-6 text-primary-600" />
                <h2 className="text-xl font-semibold">Adaptive Learning</h2>
              </div>
              <button
                onClick={handleToggleLearning}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  preferences?.learningEnabled ? 'bg-primary-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    preferences?.learningEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <p className="text-gray-600 mb-4">
              Allow the system to learn from your listening behavior and automatically adjust preferences
            </p>

            {preferences?.learningEnabled && learningStats && (
              <div className="mt-4 p-4 bg-primary-50 rounded-lg">
                <h3 className="font-semibold mb-2">Learning Statistics</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">Total Interactions</div>
                    <div className="font-semibold">{learningStats.totalInteractions}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Accuracy</div>
                    <div className="font-semibold">{Math.round(learningStats.accuracy * 100)}%</div>
                  </div>
                </div>
              </div>
            )}

            {recentAdaptations.length > 0 && (
              <div className="mt-4">
                <h3 className="font-semibold mb-2">Recent Adaptations</h3>
                <div className="space-y-2">
                  {recentAdaptations.slice(0, 5).map(adaptation => (
                    <div key={adaptation.id} className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded">
                      <span className="text-gray-700">{adaptation.description}</span>
                      <span className="text-gray-500">
                        {Math.round(adaptation.confidence * 100)}% confidence
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* Confidence Score */}
          {preferences && (
            <section className="card p-6">
              <h2 className="text-xl font-semibold mb-4">Preference Confidence</h2>
              <p className="text-gray-600 mb-4">
                How confident we are in understanding your preferences
              </p>
              
              <div className="flex items-center space-x-4">
                <div className="flex-1 bg-gray-200 rounded-full h-4">
                  <div
                    className="bg-primary-600 h-4 rounded-full transition-all"
                    style={{ width: `${preferences.confidenceScore * 100}%` }}
                  />
                </div>
                <span className="font-semibold">
                  {Math.round(preferences.confidenceScore * 100)}%
                </span>
              </div>

              <p className="text-sm text-gray-600 mt-2">
                {preferences.confidenceScore < 0.3 && 'We\'re still learning about your preferences'}
                {preferences.confidenceScore >= 0.3 && preferences.confidenceScore < 0.7 && 'We have a good understanding of your preferences'}
                {preferences.confidenceScore >= 0.7 && 'We have a strong understanding of your preferences'}
              </p>
            </section>
          )}
        </div>
      </main>
    </div>
  );
};

export default PreferencesPage;
