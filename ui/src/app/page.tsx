'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, SessionSummary, ReportSummary } from '@/lib/api';

export default function DashboardPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [sessionsData, reportsData] = await Promise.all([
          api.listSessions(),
          api.listReports(),
        ]);
        setSessions(sessionsData);
        setReports(reportsData);
      } catch (e) {
        console.error('Failed to load dashboard data:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Calculate stats
  const totalSessions = sessions.length;
  const completedSessions = sessions.filter((s) => s.status === 'completed').length;
  const totalFindings = sessions.reduce((sum, s) => sum + s.finding_count, 0);
  const runningSessions = sessions.filter(
    (s) => s.status === 'running' || s.status === 'starting'
  );

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">AI Beta Tester</h1>
          <p className="text-gray-400">AI-powered exploratory testing dashboard</p>
        </div>
        <Link
          href="/sessions/new"
          className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium text-lg"
        >
          New Test
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="p-4 bg-gray-800/50 rounded-lg">
          <div className="text-3xl font-bold">{totalSessions}</div>
          <div className="text-gray-400">Total Sessions</div>
        </div>
        <div className="p-4 bg-gray-800/50 rounded-lg">
          <div className="text-3xl font-bold text-green-400">{completedSessions}</div>
          <div className="text-gray-400">Completed</div>
        </div>
        <div className="p-4 bg-gray-800/50 rounded-lg">
          <div className="text-3xl font-bold text-yellow-400">{totalFindings}</div>
          <div className="text-gray-400">Findings</div>
        </div>
        <div className="p-4 bg-gray-800/50 rounded-lg">
          <div className="text-3xl font-bold">{reports.length}</div>
          <div className="text-gray-400">Reports</div>
        </div>
      </div>

      {/* Running sessions */}
      {runningSessions.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-medium mb-4">Running Sessions</h2>
          <div className="space-y-3">
            {runningSessions.map((session) => (
              <Link
                key={session.id}
                href={`/sessions/${session.id}`}
                className="block p-4 bg-blue-600/10 border border-blue-500/30 rounded-lg hover:bg-blue-600/20 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{session.target_url}</div>
                    <div className="text-sm text-gray-400">{session.goal}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                    </span>
                    <span className="text-blue-400">Running</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-8">
        {/* Recent sessions */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium">Recent Sessions</h2>
            <Link href="/sessions" className="text-blue-400 hover:underline text-sm">
              View all
            </Link>
          </div>
          {loading ? (
            <div className="text-gray-400">Loading...</div>
          ) : sessions.length === 0 ? (
            <div className="p-4 bg-gray-800/30 rounded-lg text-center text-gray-400">
              No sessions yet.{' '}
              <Link href="/sessions/new" className="text-blue-400 hover:underline">
                Create one
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.slice(0, 5).map((session) => (
                <Link
                  key={session.id}
                  href={`/sessions/${session.id}`}
                  className="block p-3 bg-gray-800/30 hover:bg-gray-800/50 rounded-lg transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="truncate flex-1 mr-3">
                      <div className="font-medium truncate">{session.target_url}</div>
                      <div className="text-xs text-gray-500">
                        {session.agent_count} agents • {session.finding_count} findings
                      </div>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        session.status === 'completed'
                          ? 'bg-green-600/20 text-green-400'
                          : session.status === 'running' || session.status === 'starting'
                          ? 'bg-blue-600/20 text-blue-400'
                          : session.status === 'failed'
                          ? 'bg-red-600/20 text-red-400'
                          : 'bg-gray-600/20 text-gray-400'
                      }`}
                    >
                      {session.status}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent reports */}
        <div>
          <h2 className="text-lg font-medium mb-4">Recent Reports</h2>
          {loading ? (
            <div className="text-gray-400">Loading...</div>
          ) : reports.length === 0 ? (
            <div className="p-4 bg-gray-800/30 rounded-lg text-center text-gray-400">
              No reports yet. Complete a test session to generate reports.
            </div>
          ) : (
            <div className="space-y-2">
              {reports.slice(0, 5).map((report) => (
                <Link
                  key={report.path}
                  href={`/reports/${encodeURIComponent(report.filename)}`}
                  className="block p-3 bg-gray-800/30 hover:bg-gray-800/50 rounded-lg transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="truncate flex-1 mr-3">
                      <div className="font-medium truncate">{report.filename}</div>
                      <div className="text-xs text-gray-500">
                        {new Date(report.modified_at).toLocaleString()}
                      </div>
                    </div>
                    <span className="text-gray-500 text-xs">
                      {Math.round(report.size_bytes / 1024)}KB
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
