'use client';

import { useState, useEffect } from 'react';
import { api, Personality } from '@/lib/api';

interface PersonalityPickerProps {
  selected: string[];
  recommended?: string[];
  onChange: (selected: string[]) => void;
}

export function PersonalityPicker({
  selected,
  recommended = [],
  onChange,
}: PersonalityPickerProps) {
  const [personalities, setPersonalities] = useState<Personality[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getPersonalities();
        setPersonalities(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load personalities');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function toggle(name: string) {
    if (selected.includes(name)) {
      onChange(selected.filter((p) => p !== name));
    } else {
      onChange([...selected, name]);
    }
  }

  function selectRecommended() {
    onChange(recommended);
  }

  function selectAll() {
    onChange(personalities.map((p) => p.name));
  }

  function clearAll() {
    onChange([]);
  }

  if (loading) {
    return <div className="text-gray-400">Loading personalities...</div>;
  }

  if (error) {
    return (
      <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-sm">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Quick actions */}
      <div className="flex gap-2 text-sm">
        {recommended.length > 0 && (
          <button
            onClick={selectRecommended}
            className="px-3 py-1 bg-blue-600/20 border border-blue-500/30 hover:bg-blue-600/30 rounded"
          >
            Select Recommended ({recommended.length})
          </button>
        )}
        <button
          onClick={selectAll}
          className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded"
        >
          Select All
        </button>
        <button
          onClick={clearAll}
          className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded"
        >
          Clear
        </button>
      </div>

      {/* Personality grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {personalities.map((personality) => {
          const isSelected = selected.includes(personality.name);
          const isRecommended = recommended.includes(personality.name);

          return (
            <div
              key={personality.name}
              onClick={() => toggle(personality.name)}
              className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                isSelected
                  ? 'bg-blue-600/20 border-blue-500/50'
                  : 'bg-gray-800/30 border-gray-700 hover:border-gray-600'
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Checkbox */}
                <div
                  className={`w-5 h-5 rounded flex items-center justify-center ${
                    isSelected ? 'bg-blue-600' : 'bg-gray-700'
                  }`}
                >
                  {isSelected && (
                    <svg
                      className="w-3 h-3 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">
                      {personality.name.replace(/_/g, ' ')}
                    </span>
                    {isRecommended && (
                      <span className="px-1.5 py-0.5 bg-green-600/20 text-green-400 text-xs rounded">
                        Recommended
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                    {personality.description}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selection count */}
      <div className="text-sm text-gray-400">
        {selected.length} personality{selected.length !== 1 ? 'ies' : 'y'} selected
      </div>
    </div>
  );
}
