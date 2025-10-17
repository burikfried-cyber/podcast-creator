/**
 * Onboarding Page
 * Interactive user onboarding with progressive preference discovery
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePreferences } from '@/contexts/PreferenceContext';
import { TOPIC_CATEGORIES, DEPTH_LABELS, TopicWeight } from '@/types';
import { ChevronLeft, ChevronRight, Check } from 'lucide-react';

interface OnboardingState {
  topics: Record<string, TopicWeight>;
  depthPreference: number;
  surpriseTolerance: number;
}

const OnboardingPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [state, setState] = useState<OnboardingState>({
    topics: {},
    depthPreference: 3,
    surpriseTolerance: 3
  });
  const [isGenerating, setIsGenerating] = useState(false);

  const { updatePreferences } = usePreferences();
  const navigate = useNavigate();

  const steps = [
    { title: 'Welcome', component: WelcomeStep },
    { title: 'Topics', component: TopicStep },
    { title: 'Depth', component: DepthStep },
    { title: 'Surprise', component: SurpriseStep },
    { title: 'Complete', component: CompleteStep }
  ];

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return Object.keys(state.topics).length >= 3;
      case 2:
        return state.depthPreference > 0;
      case 3:
        return state.surpriseTolerance > 0;
      default:
        return true;
    }
  };

  const handleNext = async () => {
    if (currentStep === steps.length - 1) {
      // Complete onboarding
      setIsGenerating(true);
      try {
        await updatePreferences({
          topics: state.topics,
          depthPreference: state.depthPreference,
          surpriseTolerance: state.surpriseTolerance,
          learningEnabled: true
        });
        navigate('/dashboard');
      } catch (error) {
        console.error('Failed to save preferences:', error);
      } finally {
        setIsGenerating(false);
      }
    } else {
      setCurrentStep(prev => Math.min(steps.length - 1, prev + 1));
    }
  };

  const handleBack = () => {
    setCurrentStep(prev => Math.max(0, prev - 1));
  };

  const CurrentStepComponent = steps[currentStep].component;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container max-w-3xl py-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            {steps.map((step, index) => (
              <div
                key={index}
                className={`flex items-center ${index < steps.length - 1 ? 'flex-1' : ''}`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    index < currentStep
                      ? 'bg-primary-600 text-white'
                      : index === currentStep
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-300 text-gray-600'
                  }`}
                >
                  {index < currentStep ? <Check className="h-4 w-4" /> : index + 1}
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`h-1 flex-1 mx-2 ${
                      index < currentStep ? 'bg-primary-600' : 'bg-gray-300'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="text-center text-sm text-gray-600">
            Step {currentStep + 1} of {steps.length}: {steps[currentStep].title}
          </div>
        </div>

        {/* Step Content */}
        <div className="card p-8 mb-6">
          <CurrentStepComponent state={state} setState={setState} />
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={handleBack}
            disabled={currentStep === 0}
            className="btn-ghost px-4 py-2 flex items-center space-x-2"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Back</span>
          </button>

          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Skip onboarding
          </button>

          <button
            onClick={handleNext}
            disabled={!canProceed() || isGenerating}
            className="btn-primary px-6 py-2 flex items-center space-x-2"
          >
            <span>{currentStep === steps.length - 1 ? 'Complete' : 'Next'}</span>
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

// Step Components
const WelcomeStep: React.FC<any> = () => (
  <div className="text-center py-8">
    <h2 className="text-3xl font-bold mb-4">Welcome to LocationPodcast!</h2>
    <p className="text-lg text-gray-600 mb-6">
      Let's personalize your experience in just a few steps.
    </p>
    <p className="text-gray-600">
      We'll learn about your interests and preferences to create the perfect podcasts for you.
    </p>
  </div>
);

const TopicStep: React.FC<any> = ({ state, setState }) => {
  const toggleTopic = (topic: string) => {
    setState((prev: OnboardingState) => {
      const topics = { ...prev.topics };
      if (topics[topic]) {
        delete topics[topic];
      } else {
        topics[topic] = { weight: 0.8, subcategories: {} };
      }
      return { ...prev, topics };
    });
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">What interests you?</h2>
      <p className="text-gray-600 mb-6">Select at least 3 topics you'd like to explore</p>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {TOPIC_CATEGORIES.map(topic => (
          <button
            key={topic}
            onClick={() => toggleTopic(topic)}
            className={`p-4 rounded-lg border-2 transition-all ${
              state.topics[topic]
                ? 'border-primary-600 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <span className="font-medium">{topic}</span>
          </button>
        ))}
      </div>

      <p className="text-sm text-gray-500 mt-4">
        Selected: {Object.keys(state.topics).length} / 3 minimum
      </p>
    </div>
  );
};

const DepthStep: React.FC<any> = ({ state, setState }) => {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">How deep should we go?</h2>
      <p className="text-gray-600 mb-6">Choose your preferred level of detail</p>

      <div className="space-y-4">
        {DEPTH_LABELS.map((label, index) => (
          <button
            key={label}
            onClick={() => setState((prev: OnboardingState) => ({ ...prev, depthPreference: index + 1 }))}
            className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
              state.depthPreference === index + 1
                ? 'border-primary-600 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="font-medium mb-1">{label}</div>
            <div className="text-sm text-gray-600">
              {index === 0 && 'Quick overview, main highlights'}
              {index === 1 && 'Basic information with some context'}
              {index === 2 && 'Balanced depth with interesting details'}
              {index === 3 && 'Detailed exploration with analysis'}
              {index === 4 && 'Expert-level insights and connections'}
              {index === 5 && 'Academic depth with comprehensive coverage'}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

const SurpriseStep: React.FC<any> = ({ state, setState }) => {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">How surprising should it be?</h2>
      <p className="text-gray-600 mb-6">Choose how much unexpected content you'd like</p>

      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map(level => (
          <button
            key={level}
            onClick={() => setState((prev: OnboardingState) => ({ ...prev, surpriseTolerance: level }))}
            className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
              state.surpriseTolerance === level
                ? 'border-primary-600 bg-primary-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="font-medium mb-1">Level {level}</div>
            <div className="text-sm text-gray-600">
              {level === 1 && 'Stick to what I know - predictable content'}
              {level === 2 && 'Mostly familiar with occasional surprises'}
              {level === 3 && 'Balanced mix of expected and unexpected'}
              {level === 4 && 'Frequently surprise me with new angles'}
              {level === 5 && 'Maximum surprise - show me the unexpected!'}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

const CompleteStep: React.FC<any> = ({ state }) => (
  <div className="text-center py-8">
    <div className="mb-6">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <Check className="h-8 w-8 text-green-600" />
      </div>
      <h2 className="text-3xl font-bold mb-4">You're all set!</h2>
      <p className="text-lg text-gray-600">
        We've learned about your preferences and we're ready to create amazing podcasts for you.
      </p>
    </div>

    <div className="bg-gray-50 rounded-lg p-6 text-left">
      <h3 className="font-semibold mb-3">Your Preferences:</h3>
      <ul className="space-y-2 text-sm text-gray-600">
        <li>• <strong>Topics:</strong> {Object.keys(state.topics).join(', ')}</li>
        <li>• <strong>Depth:</strong> {DEPTH_LABELS[state.depthPreference - 1]}</li>
        <li>• <strong>Surprise Level:</strong> {state.surpriseTolerance}/5</li>
      </ul>
    </div>
  </div>
);

export default OnboardingPage;
