'use client';

import { useState, useEffect } from 'react';
import { api, DirectoryEntry, DirectoryListing, ProjectDetection } from '@/lib/api';

interface FileBrowserProps {
  onProjectSelect: (project: ProjectDetection) => void;
}

export function FileBrowser({ onProjectSelect }: FileBrowserProps) {
  const [listing, setListing] = useState<DirectoryListing | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [projectInfo, setProjectInfo] = useState<ProjectDetection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load initial directory
  useEffect(() => {
    loadDirectory();
  }, []);

  async function loadDirectory(path?: string) {
    setLoading(true);
    setError(null);
    try {
      const data = await api.browse(path);
      setListing(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load directory');
    } finally {
      setLoading(false);
    }
  }

  async function handleEntryClick(entry: DirectoryEntry) {
    if (entry.is_directory) {
      await loadDirectory(entry.path);
      setSelectedPath(null);
      setProjectInfo(null);
    }
  }

  async function handleSelectProject(entry: DirectoryEntry) {
    setSelectedPath(entry.path);
    try {
      const info = await api.detect(entry.path);
      setProjectInfo(info);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to detect project');
    }
  }

  function handleConfirmProject() {
    if (projectInfo) {
      onProjectSelect(projectInfo);
    }
  }

  function navigateUp() {
    if (listing?.parent) {
      loadDirectory(listing.parent);
      setSelectedPath(null);
      setProjectInfo(null);
    }
  }

  return (
    <div className="space-y-4">
      {/* Current path */}
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <span className="font-mono">{listing?.path || 'Loading...'}</span>
      </div>

      {/* Navigation */}
      <div className="flex gap-2">
        <button
          onClick={navigateUp}
          disabled={!listing?.parent}
          className="px-3 py-1 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm"
        >
          ← Up
        </button>
        <button
          onClick={() => loadDirectory()}
          className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded text-sm"
        >
          Reset
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Directory listing */}
      <div className="border border-gray-800 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-4 text-gray-400">Loading...</div>
        ) : (
          <div className="divide-y divide-gray-800 max-h-80 overflow-y-auto">
            {listing?.entries.map((entry) => (
              <div
                key={entry.path}
                className={`flex items-center gap-3 p-3 hover:bg-gray-800/50 cursor-pointer ${
                  selectedPath === entry.path ? 'bg-blue-500/10' : ''
                }`}
                onClick={() =>
                  entry.is_project
                    ? handleSelectProject(entry)
                    : handleEntryClick(entry)
                }
                onDoubleClick={() => handleEntryClick(entry)}
              >
                {/* Icon */}
                <span className="text-lg">
                  {entry.is_directory
                    ? entry.is_project
                      ? '📦'
                      : '📁'
                    : '📄'}
                </span>

                {/* Name */}
                <span className="flex-1 truncate">{entry.name}</span>

                {/* Project type badge */}
                {entry.is_project && entry.project_type && (
                  <span className="px-2 py-0.5 bg-gray-700 rounded text-xs text-gray-300">
                    {entry.project_type}
                  </span>
                )}

                {/* Select button for projects */}
                {entry.is_project && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectProject(entry);
                    }}
                    className="px-2 py-1 bg-blue-600 hover:bg-blue-500 rounded text-xs"
                  >
                    Select
                  </button>
                )}
              </div>
            ))}

            {listing?.entries.length === 0 && (
              <div className="p-4 text-gray-500 text-center">
                Empty directory
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selected project info */}
      {projectInfo && (
        <div className="p-4 bg-gray-800/50 border border-gray-700 rounded-lg space-y-3">
          <h3 className="font-semibold">{projectInfo.name}</h3>

          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-gray-400">Type:</div>
            <div>{projectInfo.project_type || 'Unknown'}</div>

            <div className="text-gray-400">URL:</div>
            <div className={projectInfo.url ? 'text-green-400' : 'text-yellow-400'}>
              {projectInfo.url || 'Not registered'}
            </div>

            {projectInfo.registered && (
              <>
                <div className="text-gray-400">Port:</div>
                <div>{projectInfo.port}</div>
              </>
            )}
          </div>

          {projectInfo.recommended_personalities && (
            <div>
              <div className="text-gray-400 text-sm mb-1">Recommended:</div>
              <div className="flex flex-wrap gap-1">
                {projectInfo.recommended_personalities.map((p) => (
                  <span
                    key={p}
                    className="px-2 py-0.5 bg-gray-700 rounded text-xs"
                  >
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={handleConfirmProject}
            disabled={!projectInfo.url}
            className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded font-medium"
          >
            {projectInfo.url ? 'Use This Project' : 'Project not registered in ports.json'}
          </button>
        </div>
      )}
    </div>
  );
}
