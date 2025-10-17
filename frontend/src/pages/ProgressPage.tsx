/**
 * Progress Page
 * Real-time podcast generation progress tracking
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { podcastService } from '@/services/podcasts';

interface GenerationStep {
  id: string;
  label: string;
  icon: string;
  progress: number; // Threshold percentage
}

const GENERATION_STEPS: GenerationStep[] = [
  { id: 'init', label: 'Initializing', icon: '🚀', progress: 10 },
  { id: 'content', label: 'Gathering content', icon: '📚', progress: 30 },
  { id: 'script', label: 'Generating script', icon: '✍️', progress: 60 },
  { id: 'details', label: 'Adding details', icon: '🎨', progress: 70 },
  { id: 'audio', label: 'Creating audio', icon: '🎵', progress: 90 },
  { id: 'complete', label: 'Finalizing', icon: '✨', progress: 100 }
];

export default function ProgressPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<string>('processing');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('Starting generation...');
  const [error, setError] = useState<string | null>(null);
  const [podcastId, setPodcastId] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      navigate('/generate');
      return;
    }

    // Poll for status updates
    const pollInterval = setInterval(async () => {
      try {
        console.log('🔄 Polling status for job:', jobId);
        const response = await podcastService.getPodcastStatus(jobId);
        
        console.log('📊 Status Response:', {
          status: response.status,
          progress: response.progress,
          message: response.message,
          podcast_id: response.podcast_id
        });
        
        setStatus(response.status);
        setProgress(response.progress || 0);
        setMessage(response.message);
        setPodcastId(response.podcast_id || null);

        // If completed, redirect to podcast page
        const statusLower = response.status.toLowerCase();
        if (statusLower === 'completed' && response.podcast_id) {
          console.log('✅ Generation complete! Redirecting...');
          clearInterval(pollInterval);
          setTimeout(() => {
            navigate(`/podcast/${response.podcast_id}`);
          }, 2000); // Show success for 2 seconds
        }

        // If failed, show error
        if (statusLower === 'failed') {
          console.error('❌ Generation failed:', response.message);
          clearInterval(pollInterval);
          setError(response.message || 'Generation failed');
        }
      } catch (err: any) {
        console.error('❌ Failed to fetch status:', err);
        setError(err.message || 'Failed to check status');
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [jobId, navigate]);

  const getCurrentStep = () => {
    return GENERATION_STEPS.findIndex(step => progress < step.progress);
  };

  const currentStepIndex = getCurrentStep();

  // Get status display info
  const getStatusInfo = () => {
    const statusLower = status.toLowerCase();
    if (statusLower === 'failed') {
      return { color: 'red', icon: '❌', text: 'Generation Failed' };
    }
    if (statusLower === 'completed') {
      return { color: 'green', icon: '✅', text: 'Complete!' };
    }
    return { color: 'blue', icon: '⏳', text: 'Generating...' };
  };

  const statusInfo = getStatusInfo();

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {status === 'completed' ? '🎉 Podcast Ready!' : '⏳ Generating Your Podcast'}
          </h1>
          <p className="text-lg text-gray-600">
            {status === 'completed' 
              ? 'Your podcast has been successfully generated!'
              : 'This usually takes 1-3 minutes...'}
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 space-y-8">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-sm font-medium text-gray-700 mb-2">
              <span>{message}</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ease-out ${
                  status === 'completed'
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                    : status === 'failed'
                    ? 'bg-gradient-to-r from-red-500 to-rose-500'
                    : 'bg-gradient-to-r from-indigo-500 to-purple-500'
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Generation Steps */}
          <div className="space-y-4">
            {GENERATION_STEPS.map((step, index) => {
              const isCompleted = progress >= step.progress;
              const isCurrent = index === currentStepIndex;
              const isPending = progress < step.progress;

              return (
                <div
                  key={step.id}
                  className={`
                    flex items-center p-4 rounded-lg transition-all duration-300
                    ${isCompleted ? 'bg-green-50 border-2 border-green-200' : ''}
                    ${isCurrent ? 'bg-indigo-50 border-2 border-indigo-300 animate-pulse' : ''}
                    ${isPending ? 'bg-gray-50 border-2 border-gray-200 opacity-50' : ''}
                  `}
                >
                  <div className="text-3xl mr-4">{step.icon}</div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">{step.label}</div>
                    <div className="text-sm text-gray-600">
                      {isCompleted && '✓ Complete'}
                      {isCurrent && '🔄 In progress...'}
                      {isPending && '⏸️ Pending'}
                    </div>
                  </div>
                  {isCompleted && (
                    <div className="text-green-500 text-2xl">✅</div>
                  )}
                  {isCurrent && (
                    <div className="animate-spin text-indigo-500 text-2xl">⚙️</div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <span className="text-red-600 text-2xl mr-3">⚠️</span>
                <div>
                  <div className="font-semibold text-red-900 mb-1">Generation Failed</div>
                  <div className="text-red-800">{error}</div>
                  <button
                    onClick={() => navigate('/generate')}
                    className="mt-3 text-sm text-red-600 hover:text-red-700 font-medium underline"
                  >
                    Try again
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Success Message */}
          {status === 'completed' && (
            <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6 text-center">
              <div className="text-6xl mb-4 animate-bounce">🎉</div>
              <div className="text-2xl font-bold text-green-900 mb-2">
                Podcast Generated Successfully!
              </div>
              <div className="text-green-700 mb-4">
                Redirecting to your podcast...
              </div>
              {podcastId && (
                <button
                  onClick={() => navigate(`/podcast/${podcastId}`)}
                  className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors"
                >
                  View Podcast Now
                </button>
              )}
            </div>
          )}

          {/* Cancel Button */}
          {status === 'processing' && (
            <button
              onClick={() => navigate('/library')}
              className="w-full py-3 px-4 border-2 border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
            >
              Continue in Background
            </button>
          )}
        </div>

        {/* Fun Facts */}
        {status === 'processing' && (
          <div className="mt-8 bg-purple-50 rounded-xl p-6">
            <h3 className="font-semibold text-purple-900 mb-3">💡 Did you know?</h3>
            <p className="text-sm text-purple-800">
              We're analyzing multiple sources to create the most comprehensive and engaging
              podcast about your location. This includes historical records, cultural insights,
              and interesting facts you won't find anywhere else!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
