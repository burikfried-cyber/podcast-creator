/**
 * Podcast Player Page
 * Advanced audio player with behavioral tracking
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAudio } from '@/contexts/AudioContext';
import { useQuery } from '@tanstack/react-query';
import { podcastService } from '@/services/podcasts';
import { 
  Play, Pause, SkipForward, SkipBack, Volume2, VolumeX, 
  Share2, Download, ThumbsUp, ThumbsDown, ChevronLeft,
  Loader2
} from 'lucide-react';
import { PLAYBACK_SPEEDS } from '@/types';

const PodcastPlayerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    playbackState,
    currentTime,
    duration,
    playbackSpeed,
    volume,
    isMuted,
    isBuffering,
    play,
    pause,
    seek,
    setSpeed,
    setVolume,
    toggleMute,
    skipForward,
    skipBackward,
    loadPodcast,
    trackBehavior
  } = useAudio();

  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);

  // Fetch podcast data
  const { data: podcast, isLoading, error } = useQuery({
    queryKey: ['podcast', id],
    queryFn: () => podcastService.getPodcast(id!),
    enabled: !!id
  });

  // Debug logging
  useEffect(() => {
    if (podcast) {
      console.log('📻 Podcast Data Received:', {
        id: podcast.id,
        title: podcast.title,
        hasScript: !!podcast.script_content,
        scriptLength: podcast.script_content?.length || 0,
        scriptPreview: podcast.script_content?.substring(0, 100),
        hasAudio: !!podcast.audio_url,
        status: podcast.status
      });
    }
  }, [podcast]);

  // Load podcast when data is available
  useEffect(() => {
    if (podcast?.audio_url) {
      loadPodcast(podcast.id, podcast.audio_url);
    }
  }, [podcast, loadPodcast]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value);
    seek(newTime);
  };

  const handleFeedback = (rating: number) => {
    if (!id) return;
    trackBehavior('explicit_feedback', { rating, podcast_id: id });
    setShowFeedback(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary-600" />
      </div>
    );
  }

  if (error || !podcast) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to load podcast</p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary px-4 py-2">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <header className="container py-4">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
        >
          <ChevronLeft className="h-5 w-5" />
          <span>Back</span>
        </button>
      </header>

      {/* Main Player */}
      <main className="container max-w-4xl py-8">
        <div className="bg-gray-800 rounded-2xl shadow-2xl overflow-hidden">
          {/* Podcast Info */}
          <div className="p-8 text-center">
            <h1 className="text-3xl font-bold mb-2">{podcast.title || 'Untitled Podcast'}</h1>
            <p className="text-gray-400 mb-4">{podcast.description || 'No description available'}</p>
            <div className="flex items-center justify-center space-x-4 text-sm text-gray-400">
              <span>{podcast.location}</span>
              <span>•</span>
              <span>{formatTime(podcast.duration_seconds || 0)}</span>
              <span>•</span>
              <span className="capitalize">{podcast.podcast_type}</span>
            </div>
            
            {/* No Audio Warning */}
            {!podcast.audio_url && podcast.script_content && (
              <div className="mt-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <p className="text-yellow-400 text-sm">
                  🎙️ Audio generation coming soon! Read the script below.
                </p>
              </div>
            )}
          </div>

          {/* Progress Bar */}
          <div className="px-8 pb-4">
            <div className="relative">
              <input
                type="range"
                min="0"
                max={duration || 100}
                value={currentTime}
                onChange={handleSeek}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #2563eb 0%, #2563eb ${(currentTime / duration) * 100}%, #374151 ${(currentTime / duration) * 100}%, #374151 100%)`
                }}
              />
              {/* Chapter markers - Not available yet */}
            </div>
            <div className="flex items-center justify-between text-sm text-gray-400 mt-2">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Main Controls */}
          <div className="px-8 pb-8">
            <div className="flex items-center justify-center space-x-6">
              {/* Skip Backward */}
              <button
                onClick={() => skipBackward(15)}
                className="p-3 hover:bg-gray-700 rounded-full transition-colors"
                aria-label="Skip backward 15 seconds"
              >
                <SkipBack className="h-6 w-6" />
              </button>

              {/* Play/Pause */}
              <button
                onClick={playbackState === 'playing' ? pause : play}
                disabled={isBuffering}
                className="p-6 bg-primary-600 hover:bg-primary-700 rounded-full transition-colors disabled:opacity-50"
                aria-label={playbackState === 'playing' ? 'Pause' : 'Play'}
              >
                {isBuffering ? (
                  <Loader2 className="h-8 w-8 animate-spin" />
                ) : playbackState === 'playing' ? (
                  <Pause className="h-8 w-8" />
                ) : (
                  <Play className="h-8 w-8 ml-1" />
                )}
              </button>

              {/* Skip Forward */}
              <button
                onClick={() => skipForward(15)}
                className="p-3 hover:bg-gray-700 rounded-full transition-colors"
                aria-label="Skip forward 15 seconds"
              >
                <SkipForward className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* Advanced Controls */}
          <div className="px-8 pb-8 flex items-center justify-between">
            {/* Speed Control */}
            <div className="relative">
              <button
                onClick={() => setShowSpeedMenu(!showSpeedMenu)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-sm font-medium"
              >
                {playbackSpeed}x
              </button>
              {showSpeedMenu && (
                <div className="absolute bottom-full left-0 mb-2 bg-gray-700 rounded-lg shadow-lg overflow-hidden">
                  {PLAYBACK_SPEEDS.map(speed => (
                    <button
                      key={speed}
                      onClick={() => {
                        setSpeed(speed);
                        setShowSpeedMenu(false);
                      }}
                      className={`block w-full px-4 py-2 text-left hover:bg-gray-600 transition-colors ${
                        playbackSpeed === speed ? 'bg-gray-600' : ''
                      }`}
                    >
                      {speed}x
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Volume Control */}
            <div className="flex items-center space-x-3">
              <button
                onClick={toggleMute}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                aria-label={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={volume}
                onChange={(e) => setVolume(parseFloat(e.target.value))}
                className="w-24 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                aria-label="Volume"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowFeedback(!showFeedback)}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                aria-label="Feedback"
              >
                <ThumbsUp className="h-5 w-5" />
              </button>
              <button
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                aria-label="Share"
              >
                <Share2 className="h-5 w-5" />
              </button>
              <button
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                aria-label="Download"
              >
                <Download className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Feedback Panel */}
          {showFeedback && (
            <div className="px-8 pb-8">
              <div className="bg-gray-700 rounded-lg p-4">
                <p className="text-sm mb-3">How would you rate this podcast?</p>
                <div className="flex items-center space-x-2">
                  {[1, 2, 3, 4, 5].map(rating => (
                    <button
                      key={rating}
                      onClick={() => handleFeedback(rating)}
                      className="px-4 py-2 bg-gray-600 hover:bg-primary-600 rounded-lg transition-colors text-sm"
                    >
                      {rating}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Script Content */}
          {podcast.script_content && (
            <div className="px-8 pb-8">
              <h3 className="text-lg font-semibold mb-4">Podcast Script</h3>
              <div className="bg-gray-700 rounded-lg p-4 max-h-96 overflow-y-auto">
                <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
                  {podcast.script_content}
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default PodcastPlayerPage;
