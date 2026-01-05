'use client';

import { useSSE, SSEEvent } from '@/hooks/useSSE';

interface LiveProgressProps {
  sessionId: string;
}

export function LiveProgress({ sessionId }: LiveProgressProps) {
  const { events, isConnected, error } = useSSE(sessionId);

  // Get the latest event of each type
  const latestByType = events.reduce((acc, event) => {
    acc[event.type] = event;
    return acc;
  }, {} as Record<string, SSEEvent>);

  // Get all actions and findings
  const actions = events.filter((e) => e.type === 'action_taken');
  const findings = events.filter((e) => e.type === 'finding_reported');
  const agentStarted = latestByType['agent_started'];
  const sessionCompleted = latestByType['session_completed'];

  return (
    <div className="space-y-6">
      {/* Connection status */}
      <div className="flex items-center gap-2 text-sm">
        <div
          className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : error ? 'bg-red-500' : 'bg-gray-500'
          }`}
        />
        <span className="text-gray-400">
          {isConnected
            ? 'Connected - Live updates'
            : error
            ? 'Connection error'
            : 'Connecting...'}
        </span>
      </div>

      {/* Current agent */}
      {agentStarted && !sessionCompleted && (
        <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-400">Current Agent</div>
              <div className="text-lg font-medium">
                {String(agentStarted.personality).replace(/_/g, ' ')}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-400">Progress</div>
              <div className="font-mono">
                {Number(agentStarted.agent_index) + 1} / {Number(agentStarted.total_agents)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Session completed */}
      {sessionCompleted && (
        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
          <div className="text-lg font-medium text-green-400">
            Session Completed
          </div>
          <div className="text-sm text-gray-400 mt-1">
            {Number(sessionCompleted.agent_count)} agents •{' '}
            {Number(sessionCompleted.total_findings)} findings
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-3 bg-gray-800/50 rounded-lg">
          <div className="text-2xl font-bold">{actions.length}</div>
          <div className="text-sm text-gray-400">Actions</div>
        </div>
        <div className="p-3 bg-gray-800/50 rounded-lg">
          <div className="text-2xl font-bold">{findings.length}</div>
          <div className="text-sm text-gray-400">Findings</div>
        </div>
        <div className="p-3 bg-gray-800/50 rounded-lg">
          <div className="text-2xl font-bold">{events.length}</div>
          <div className="text-sm text-gray-400">Events</div>
        </div>
      </div>

      {/* Findings */}
      {findings.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-2">Findings</h3>
          <div className="space-y-2">
            {findings.map((finding, i) => (
              <div
                key={i}
                className={`p-3 border rounded-lg ${
                  finding.severity === 'critical'
                    ? 'severity-critical'
                    : finding.severity === 'high'
                    ? 'severity-high'
                    : finding.severity === 'medium'
                    ? 'severity-medium'
                    : 'severity-low'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="px-1.5 py-0.5 text-xs rounded uppercase font-medium">
                    {String(finding.severity)}
                  </span>
                  <span className="font-medium">{String(finding.title)}</span>
                </div>
                <p className="text-sm mt-1 opacity-80">
                  {String(finding.description)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action log */}
      <div>
        <h3 className="text-sm font-medium text-gray-400 mb-2">Action Log</h3>
        <div className="border border-gray-800 rounded-lg max-h-60 overflow-y-auto">
          {actions.length === 0 ? (
            <div className="p-3 text-gray-500 text-sm">Waiting for actions...</div>
          ) : (
            <div className="divide-y divide-gray-800">
              {actions.slice(-20).reverse().map((action, i) => (
                <div key={i} className="p-2 text-sm">
                  <span className="text-gray-500 font-mono">
                    #{Number(action.action_sequence)}
                  </span>{' '}
                  <span className="text-blue-400">{String(action.action_type)}</span>
                  {action.parameters && (
                    <span className="text-gray-400 ml-2">
                      {JSON.stringify(action.parameters).slice(0, 50)}...
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
