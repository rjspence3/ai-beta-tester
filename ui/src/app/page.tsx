import Link from 'next/link';

// ─── Data ────────────────────────────────────────────────────────────────────

const FEATURED_PERSONALITIES = [
  {
    name: 'Speedrunner',
    mindset: '"I don\'t have time for this."',
    description:
      'Skips tutorials, clicks the biggest button first, and times every interaction. If it takes more than 3 seconds, it\'s broken.',
  },
  {
    name: 'Chaos Gremlin',
    mindset: '"What happens if I do this?"',
    description:
      'Special characters, rapid clicks, empty form submissions, back button at the worst moment. Finds the edge cases you forgot existed.',
  },
  {
    name: 'Skeptical Exec',
    mindset: '"Why would I trust this?"',
    description:
      'Low tolerance for cognitive load. No exploration, no second chances. Abandons at the first sign of confusion.',
  },
  {
    name: 'Methodical Newcomer',
    mindset: '"Let me read every word."',
    description:
      'Reads tooltips, follows every instruction, clicks in exact order. Notes anything confusing or unexplained.',
  },
  {
    name: 'Privacy Paranoid',
    mindset: '"What are you collecting?"',
    description:
      'Looks for tracking pixels, suspicious of permissions, reads the privacy policy. Will not proceed without understanding data use.',
  },
  {
    name: 'ADHD Founder',
    mindset: '"Ooh, what\'s that?"',
    description:
      'Distracted, opens everything, leaves forms half-filled. Tests your app\'s ability to handle interrupted, non-linear flows.',
  },
];

const MORE_PERSONALITIES = [
  'Accessibility Advocate',
  'International User',
  'Mobile-First Tapper',
  'Budget Shopper',
  'Power User',
  'First Impression Judge',
  'Compliance Officer',
];

const EXAMPLE_FINDINGS = [
  {
    severity: 'HIGH',
    severityColor: 'border-red-500',
    severityBg: 'bg-red-50',
    severityText: 'text-red-600',
    persona: 'Speedrunner',
    title: 'Navigation: "New Test" button requires scrolling to find on mobile',
    description:
      'The primary CTA is below the fold on 375px viewport. First action I took was to look for something obvious — nothing visible without scrolling.',
    steps: ['Load page at 375px width', 'Observe initial viewport', 'Scroll to locate "New Test" button'],
  },
  {
    severity: 'MEDIUM',
    severityColor: 'border-yellow-500',
    severityBg: 'bg-yellow-50',
    severityText: 'text-yellow-700',
    persona: 'Chaos Gremlin',
    title: 'Form: Empty submission shows generic 500 error, no field-level feedback',
    description:
      'Submitted the signup form with all fields empty. Got a raw 500 server error page instead of inline validation messages. No way to know which field failed.',
    steps: ['Navigate to signup', 'Leave all fields blank', 'Click submit', 'Observe: server error page'],
  },
  {
    severity: 'LOW',
    severityColor: 'border-emerald-500',
    severityBg: 'bg-emerald-50',
    severityText: 'text-emerald-700',
    persona: 'Privacy Paranoid',
    title: 'Footer: Privacy policy link is present but opens a 404',
    description:
      'Clicked the privacy policy link in the footer immediately. Page returns a 404. This would be a hard stop for any compliance-sensitive user.',
    steps: ['Scroll to footer', 'Click "Privacy Policy"', 'Observe: 404 not found'],
  },
];

// ─── Components ───────────────────────────────────────────────────────────────

function SeverityBadge({ label, textClass }: { label: string; textClass: string }) {
  return (
    <span className={`text-xs font-semibold uppercase tracking-wider ${textClass}`}>
      {label} SEVERITY
    </span>
  );
}

function PersonaBadge({ name }: { name: string }) {
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
      {name}
    </span>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F8F9FC]">

      {/* ── Section 1: Hero ─────────────────────────────────────────────── */}
      <section className="px-6 pt-24 pb-20 text-center">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-xs font-medium text-indigo-600 mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 inline-block"></span>
            Claude-powered · Playwright automation · 13 personalities
          </div>

          <h1 className="text-5xl font-bold tracking-tight text-[#111827] leading-tight mb-6">
            Your app has blind spots.
            <br />
            <span className="text-indigo-600">Meet the testers who find them.</span>
          </h1>

          <p className="text-xl text-[#6B7280] leading-relaxed mb-10 max-w-2xl mx-auto">
            AI agents with distinct personalities — the impatient user, the chaos gremlin,
            the skeptical exec — each browsing your app differently to surface the bugs
            you can&apos;t see.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="https://github.com/imaglide/betaTesters"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-lg transition-colors"
            >
              View on GitHub
              <span aria-hidden="true">→</span>
            </a>
            <a
              href="#example-report"
              className="inline-flex items-center gap-2 px-6 py-3 border-2 border-indigo-500 text-indigo-600 font-semibold rounded-lg hover:bg-indigo-50 transition-colors"
            >
              See an example report
              <span aria-hidden="true">↓</span>
            </a>
          </div>
        </div>
      </section>

      {/* ── Section 2: The Problem ──────────────────────────────────────── */}
      <section className="px-6 py-20 bg-white border-y border-[#E5E7EB]">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold tracking-tight text-[#111827] mb-4">
              You built it. That&apos;s the problem.
            </h2>
            <p className="text-[#6B7280] text-lg">
              Your instincts about your app are your biggest blind spot.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: '🧠',
                title: 'Familiarity bias',
                body: 'You know how it works, so you use it correctly. Real users won\'t. They\'ll click the wrong thing, skip the tooltip, and blame your app.',
              },
              {
                icon: '⏱️',
                title: 'Beta testing takes days',
                body: 'Recruiting humans, scheduling, waiting for feedback. By the time you get results, you\'ve already shipped three more features.',
              },
              {
                icon: '🤖',
                title: 'Automated tests miss UX',
                body: 'Unit and E2E tests verify expected behavior. They don\'t explore. They don\'t get confused. They don\'t abandon your flow in frustration.',
              },
            ].map((card) => (
              <div
                key={card.title}
                className="p-6 rounded-xl"
                style={{
                  background: 'rgba(255,255,255,0.9)',
                  border: '1px solid rgba(99,102,241,0.12)',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.04)',
                  backdropFilter: 'blur(8px)',
                }}
              >
                <div className="text-3xl mb-4">{card.icon}</div>
                <h3 className="text-lg font-semibold text-[#111827] mb-2">{card.title}</h3>
                <p className="text-[#6B7280] text-sm leading-relaxed">{card.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Section 3: Personalities ────────────────────────────────────── */}
      <section className="px-6 py-20">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold tracking-tight text-[#111827] mb-4">
              13 testers. 13 perspectives.
            </h2>
            <p className="text-[#6B7280] text-lg">
              Each agent has a distinct mental model, tolerance level, and set of instincts.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
            {FEATURED_PERSONALITIES.map((persona) => (
              <div
                key={persona.name}
                className="p-5 rounded-xl flex flex-col gap-2"
                style={{
                  background: 'rgba(255,255,255,0.9)',
                  border: '1px solid rgba(99,102,241,0.12)',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.04)',
                  backdropFilter: 'blur(8px)',
                }}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[#111827] font-semibold">{persona.name}</span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-600 border border-indigo-100 whitespace-nowrap shrink-0">
                    Agent
                  </span>
                </div>
                <p className="text-sm italic text-indigo-500">{persona.mindset}</p>
                <p className="text-sm text-[#6B7280] leading-relaxed">{persona.description}</p>
              </div>
            ))}
          </div>

          <div className="text-center">
            <p className="text-sm text-[#9CA3AF] mb-3">…and 7 more</p>
            <div className="flex flex-wrap justify-center gap-2">
              {MORE_PERSONALITIES.map((name) => (
                <span
                  key={name}
                  className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-[#6B7280] border border-gray-200"
                >
                  {name}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 4: How It Works ─────────────────────────────────────── */}
      <section className="px-6 py-20 bg-white border-y border-[#E5E7EB]">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tight text-[#111827] mb-4">
              Three commands to a full report
            </h2>
            <p className="text-[#6B7280] text-lg">
              No configuration. No account setup. Just a URL and a goal.
            </p>
          </div>

          <div className="rounded-xl overflow-hidden mb-8" style={{ boxShadow: '0 4px 24px rgba(0,0,0,0.12)' }}>
            <div className="flex items-center gap-2 px-4 py-3 bg-gray-800">
              <span className="w-3 h-3 rounded-full bg-red-400/80"></span>
              <span className="w-3 h-3 rounded-full bg-yellow-400/80"></span>
              <span className="w-3 h-3 rounded-full bg-green-400/80"></span>
              <span className="ml-2 text-xs text-gray-400 font-mono">terminal</span>
            </div>
            <pre className="bg-gray-900 text-gray-100 p-6 text-sm leading-relaxed font-mono overflow-x-auto">
              <code>{`# Install
pip install -e .

# Run
ai-beta-test run https://your-app.com \\
  --goal "Complete the signup flow" \\
  --personalities speedrunner chaos_gremlin skeptical_exec

# Output: structured markdown report with findings,
#         screenshots, and reproduction steps`}</code>
            </pre>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 text-sm">
            {[
              { step: '1', label: 'Spawns agents' },
              { step: '2', label: 'Each browses independently' },
              { step: '3', label: 'Findings consolidated' },
            ].map((item, index) => (
              <div key={item.step} className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 font-medium">
                  <span className="w-5 h-5 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold shrink-0">
                    {item.step}
                  </span>
                  {item.label}
                </div>
                {index < 2 && (
                  <span className="text-[#9CA3AF] hidden sm:inline" aria-hidden="true">→</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Section 5: Example Report ───────────────────────────────────── */}
      <section id="example-report" className="px-6 py-20">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tight text-[#111827] mb-4">
              What a report looks like
            </h2>
            <p className="text-[#6B7280] text-lg">
              Each finding includes severity, reproduction steps, and the persona&apos;s perspective.
            </p>
          </div>

          <div className="space-y-4">
            {EXAMPLE_FINDINGS.map((finding) => (
              <div
                key={finding.title}
                className={`rounded-xl overflow-hidden border-l-4 ${finding.severityColor}`}
                style={{
                  background: 'rgba(255,255,255,0.9)',
                  border: `1px solid rgba(0,0,0,0.06)`,
                  borderLeftWidth: '4px',
                  borderLeftColor: finding.severityColor.replace('border-', '').replace('-500', ''),
                  boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
                }}
              >
                <div className={`px-5 py-3 ${finding.severityBg} flex items-center justify-between flex-wrap gap-2`}>
                  <SeverityBadge label={finding.severity} textClass={finding.severityText} />
                  <PersonaBadge name={finding.persona} />
                </div>
                <div className="px-5 py-4">
                  <h3 className="font-semibold text-[#111827] mb-2">{finding.title}</h3>
                  <p className="text-sm text-[#6B7280] leading-relaxed mb-4">{finding.description}</p>
                  <div>
                    <p className="text-xs font-medium text-[#9CA3AF] uppercase tracking-wider mb-1.5">
                      Reproduction steps
                    </p>
                    <ol className="space-y-1">
                      {finding.steps.map((step, i) => (
                        <li key={i} className="text-sm text-[#374151] flex items-start gap-2">
                          <span className="text-[#9CA3AF] shrink-0 font-mono text-xs mt-0.5">{i + 1}.</span>
                          {step}
                        </li>
                      ))}
                    </ol>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Section 6: Footer ───────────────────────────────────────────── */}
      <footer className="px-6 py-12 bg-white border-t border-[#E5E7EB]">
        <div className="max-w-5xl mx-auto flex flex-col items-center gap-4 text-center">
          <p className="font-semibold text-[#111827]">
            Built by NoMouthLabs · Part of the NML portfolio
          </p>
          <div className="flex items-center gap-6 text-sm">
            <a
              href="https://github.com/imaglide/betaTesters"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#6B7280] hover:text-[#111827] transition-colors"
            >
              GitHub
            </a>
            <a
              href="https://nomouthlabs.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#6B7280] hover:text-[#111827] transition-colors"
            >
              nomouthlabs.com
            </a>
          </div>
          <p className="text-xs text-[#9CA3AF]">Powered by Claude + Playwright</p>
        </div>
      </footer>

    </div>
  );
}
