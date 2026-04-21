'use client';

import { useMemo, useState } from 'react';
import { apiClient, type AnalysisResult } from '@/lib/api';

type FrameworkId = 'gri' | 'sasb' | 'tcfd' | 'esrs';

const frameworks: Record<FrameworkId, { label: string; summary: string; focus: string }>[] = [
  {
    gri: {
      label: 'GRI Standards',
      summary: 'General-purpose disclosures for sustainability reporting.',
      focus: 'Breadth across E, S, and G with materiality emphasis.',
    },
    sasb: {
      label: 'SASB',
      summary: 'Industry-specific ESG metrics tied to financial impact.',
      focus: 'Material indicators tailored to the chosen sector.',
    },
    tcfd: {
      label: 'TCFD',
      summary: 'Climate-related risks, governance, and scenario analysis.',
      focus: 'Climate governance, transition risk, and resilience.',
    },
    esrs: {
      label: 'ESRS',
      summary: 'EU-focused disclosure with double materiality.',
      focus: 'Regulatory alignment and stakeholder impacts.',
    },
  },
];

// Top zone labels for display
const ZONE_LABELS: Record<string, string> = {
  E_Emissions: 'Emissions',
  E_Energy: 'Energy',
  E_Water: 'Water',
  E_Waste: 'Waste',
  E_Biodiversity: 'Biodiversity',
  S_Labor: 'Labor',
  S_Safety: 'Safety',
  S_Diversity: 'Diversity',
  S_Community: 'Community',
  S_SupplyChain: 'Supply Chain',
  G_Board: 'Board',
  G_ExecutivePay: 'Executive Pay',
  G_AntiCorruption: 'Anti-Corruption',
  G_Transparency: 'Transparency',
  G_RiskManagement: 'Risk Management',
};

function pillarColor(zone: string) {
  if (zone.startsWith('E_')) return 'bg-green-300';
  if (zone.startsWith('S_')) return 'bg-sky-300';
  return 'bg-amber-300';
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [frameworkId, setFrameworkId] = useState<FrameworkId>('gri');
  const [status, setStatus] = useState<'idle' | 'ready' | 'scoring' | 'scored' | 'error'>('idle');
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [message, setMessage] = useState<string>('');

  const selectedFramework = useMemo(() => frameworks[0][frameworkId], [frameworkId]);

  const handleFile = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setFile(files[0]);
    setStatus('ready');
    setMessage('Ready to score.');
    setAnalysis(null);
  };

  const runScoring = async () => {
    if (!file) {
      setMessage('Please upload an ESG profile first.');
      return;
    }
    setStatus('scoring');
    setMessage('Uploading document & running NLP analysis...');

    try {
      // organization_id=1 as default — in a full app this would be selectable
      const result = await apiClient.uploadAndAnalyze(file, 1, frameworkId);
      setAnalysis(result);
      setStatus('scored');
      setMessage(
        `Scoring complete — ${result.total_pages ?? '?'} pages, ${result.total_words?.toLocaleString() ?? '?'} words analysed.`
      );
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed';
      setStatus('error');
      setMessage(`Error: ${errorMessage}`);
    }
  };

  // Derive top zone drivers sorted by keyword density
  const topZones = useMemo(() => {
    if (!analysis?.zone_breakdown) return [];
    return Object.entries(analysis.zone_breakdown)
      .map(([zone, density]) => ({ zone, density }))
      .sort((a, b) => b.density - a.density)
      .slice(0, 7);
  }, [analysis]);

  const maxDensity = topZones.length > 0 ? topZones[0].density : 1;

  const statusTone = {
    idle: 'text-slate-500 bg-slate-100',
    ready: 'text-emerald-700 bg-emerald-50',
    scoring: 'text-amber-700 bg-amber-50',
    scored: 'text-blue-700 bg-blue-50',
    error: 'text-red-700 bg-red-50',
  }[status];

  const step =
    status === 'idle' ? 1 : status === 'ready' ? 2 : status === 'scoring' ? 3 : 4;

  return (
    <div className="min-h-screen bg-white text-slate-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-emerald-600">ESG Scoring Studio</p>
            <h1 className="mt-2 text-3xl sm:text-4xl font-semibold">Upload &rarr; Framework &rarr; Score</h1>
            <p className="mt-2 text-slate-600 max-w-2xl">
              Bring your ESG report (PDF), choose the disclosure framework, and let the model
              scan the entire document and compute transparent E / S / G scores with zone breakdown.
            </p>
          </div>
          <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-xl px-4 py-3">
            <span className={`text-xs font-medium px-3 py-1 rounded-full ${statusTone}`}>{message || 'Awaiting upload'}</span>
          </div>
        </header>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_1fr]">
          <div className="space-y-4">
            <div className="bg-white border border-slate-200 rounded-2xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Step {step} of 4</p>
                  <h2 className="text-2xl font-semibold">1. Upload ESG profile</h2>
                </div>
                <span className="text-xs text-slate-500">PDF</span>
              </div>

              <label className="mt-4 block cursor-pointer border-2 border-dashed border-white/20 rounded-xl p-5 text-center hover:border-emerald-400/60 transition">
                <input
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={(e) => handleFile(e.target.files)}
                />
                <div className="flex flex-col items-center gap-2 text-slate-700">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" className="text-emerald-300">
                    <path
                      d="M12 3v14m0-14 4 4m-4-4-4 4"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M6 17h12v1a3 3 0 0 1-3 3H9a3 3 0 0 1-3-3v-1Z"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div className="text-lg font-medium text-slate-900">Drop your ESG report (PDF)</div>
                  <div className="text-sm text-slate-500">The entire document is scanned, text extracted, and analysed by our NLP model.</div>
                  {file && <div className="mt-2 text-sm text-emerald-700">Selected: {file.name}</div>}
                </div>
              </label>

              <div className="mt-6">
                <h3 className="text-xl font-semibold">2. Select framework</h3>
                <p className="text-sm text-slate-600">Choose the disclosure lens for the scoring run.</p>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  {(['gri', 'sasb', 'tcfd', 'esrs'] as FrameworkId[]).map((fw) => {
                    const f = frameworks[0][fw];
                    const active = frameworkId === fw;
                    return (
                      <button
                        key={fw}
                        onClick={() => setFrameworkId(fw)}
                        className={`text-left rounded-xl border transition p-4 h-full ${
                          active
                            ? 'border-emerald-400 bg-emerald-50 shadow-[0_10px_40px_-25px_rgba(16,185,129,0.5)]'
                            : 'border-slate-200 bg-white hover:border-emerald-300'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div>
                            <div className="text-sm uppercase tracking-wide text-emerald-700">{f.label}</div>
                            <div className="text-lg font-semibold text-slate-900">{f.summary}</div>
                          </div>
                          <div className="text-xs px-3 py-1 rounded-full bg-slate-100 text-slate-700">{active ? 'Selected' : 'Pick'}</div>
                        </div>
                        <p className="mt-2 text-sm text-slate-600">{f.focus}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <button
                  onClick={runScoring}
                  disabled={status === 'scoring'}
                  className="inline-flex items-center gap-2 rounded-xl bg-emerald-400 text-slate-900 px-5 py-3 font-semibold hover:-translate-y-0.5 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {status === 'scoring' ? (
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-slate-900 animate-ping" /> Analysing document...
                    </span>
                  ) : (
                    'Run ESG scoring'
                  )}
                </button>
                <div className="text-sm text-slate-300">Framework: {selectedFramework.label}</div>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl p-6">
              <h3 className="text-xl font-semibold">Process at a glance</h3>
              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                {[{
                  title: 'Ingestion',
                  detail: 'Upload PDF, extract full text from every page.',
                }, {
                  title: 'NLP Analysis',
                  detail: 'LSA + keyword features scored by E/S/G models.',
                }, {
                  title: 'Scoring',
                  detail: 'Composite + pillar scores with zone breakdown.',
                }].map((item) => (
                  <div key={item.title} className="rounded-xl border border-slate-200 bg-white p-4">
                    <div className="text-sm uppercase tracking-wide text-emerald-700">{item.title}</div>
                    <div className="mt-1 text-sm text-slate-700">{item.detail}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-white border border-slate-200 rounded-2xl p-6">
              <h2 className="text-2xl font-semibold">3. Model outputs</h2>
              <p className="text-sm text-slate-600">NLP-derived E / S / G and composite scores (0-10 scale).</p>

              <div className="mt-5 grid gap-3">
                {[{ label: 'Composite', value: analysis?.composite_score ?? 0, color: 'bg-emerald-400' },
                  { label: 'Environmental', value: analysis?.e_score ?? 0, color: 'bg-green-300' },
                  { label: 'Social', value: analysis?.s_score ?? 0, color: 'bg-sky-300' },
                  { label: 'Governance', value: analysis?.g_score ?? 0, color: 'bg-amber-300' },
                ].map((s) => (
                  <div key={s.label} className="rounded-xl border border-slate-200 bg-white p-4">
                    <div className="flex items-center justify-between text-slate-800">
                      <span>{s.label}</span>
                      <span className="text-xl font-semibold text-slate-900">{(s.value || 0).toFixed(2)}</span>
                    </div>
                    <div className="mt-3 h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className={`${s.color} h-full`} style={{ width: `${Math.min((s.value || 0) * 10, 100)}%` }} />
                    </div>
                  </div>
                ))}

                {analysis && (
                  <div className="rounded-xl border border-slate-200 bg-white p-4">
                    <div className="flex items-center justify-between text-slate-800">
                      <span>Document</span>
                      <span className="text-sm font-medium text-slate-700">
                        {analysis.total_pages} pages &middot; {analysis.total_words?.toLocaleString()} words
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl p-6">
              <h3 className="text-xl font-semibold">4. Zone breakdown</h3>
              <p className="text-sm text-slate-600">Top ESG topic areas detected in the document (keyword density).</p>
              <div className="mt-4 space-y-3">
                {topZones.length === 0 && (
                  <p className="text-sm text-slate-400">Upload and score a document to see zone breakdown.</p>
                )}
                {topZones.map((d) => (
                  <div key={d.zone} className="rounded-lg border border-slate-200 bg-white px-4 py-3">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-mono text-slate-900">
                        {ZONE_LABELS[d.zone] ?? d.zone}
                      </div>
                      <span
                        className={`text-xs font-semibold px-3 py-1 rounded-full ${
                          d.zone.startsWith('E_')
                            ? 'bg-green-100 text-green-800'
                            : d.zone.startsWith('S_')
                            ? 'bg-sky-100 text-sky-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {d.zone.split('_')[0]}
                      </span>
                    </div>
                    <div className="mt-2 h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`${pillarColor(d.zone)} h-full`}
                        style={{ width: `${Math.round((d.density / maxDensity) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
