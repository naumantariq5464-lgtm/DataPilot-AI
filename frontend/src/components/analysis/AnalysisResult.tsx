import type { AnalysisResult } from '../../types/analysis'
import ChartRenderer from '../charts/ChartRenderer'

interface Props { result: AnalysisResult }

// ── Helpers ────────────────────────────────────────────────────────────────────

/**
 * Converts any statistics value to a human-readable string.
 * Backend sanitises these, but this is a second safety layer.
 */
function formatStatValue(val: unknown): string {
  if (val === null || val === undefined) return 'N/A'
  if (typeof val === 'number') {
    if (!isFinite(val)) return 'N/A'
    return Number.isInteger(val) ? val.toLocaleString() : val.toFixed(2)
  }
  if (typeof val === 'string') return val

  // Array — backend normally converts these to strings already,
  // but guard here too so [object Object] can never reach the DOM.
  if (Array.isArray(val)) {
    if (val.length === 0) return '—'
    const first = val[0]
    if (first && typeof first === 'object' && ('name' in first || 'label' in first)) {
      return (val as Record<string, unknown>[])
        .map((item, i) => {
          const name = item.name ?? item.label ?? item.category ?? Object.values(item)[0]
          const value = item.value ?? item.count ?? Object.values(item)[1]
          return `${i + 1}. ${name}${value !== undefined ? ` — ${value}` : ''}`
        })
        .join(' | ')
    }
    return val.map(String).join(' | ')
  }

  // Plain object
  if (typeof val === 'object') {
    const entries = Object.entries(val as Record<string, unknown>)
    return entries.map(([k, v]) => `${k}: ${v}`).join(' | ')
  }

  return String(val)
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function AnalysisResultView({ result }: Props) {
  const stats = Object.entries(result.statistics ?? {})

  return (
    <div className="space-y-5">

      {/* Insights card */}
      <div className="bg-white border border-[#EBEBEB] rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 bg-[#111] rounded-lg flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
          </div>
          <span className="text-sm font-semibold text-[#111]">AI Insights</span>
        </div>
        {/* Render multi-line insights (newlines become paragraphs) */}
        {result.insights.split('\n').filter(Boolean).map((line, i) => (
          <p key={i} className="text-sm text-[#444] leading-relaxed mt-1">{line}</p>
        ))}
        <div className="mt-3 pt-3 border-t border-[#F0F0F0]">
          <p className="text-xs text-[#999] italic">"{result.prompt}"</p>
        </div>
      </div>

      {/* Stats grid */}
      {stats.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-[#999] uppercase tracking-widest mb-3">Key Statistics</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
            {stats.map(([key, val]) => {
              const displayVal = formatStatValue(val)
              const isNumber   = typeof val === 'number' && isFinite(val as number)
              // Long strings (>25 chars) span extra columns for readability
              const isLong = !isNumber && displayVal.length > 25

              return (
                <div
                  key={key}
                  className={`bg-white border border-[#EBEBEB] rounded-xl p-4
                    ${isLong ? 'col-span-2 xl:col-span-4' : ''}`}
                >
                  <p className="text-[11px] text-[#999] capitalize mb-1">
                    {key.replace(/_/g, ' ')}
                  </p>
                  <p className={`text-base font-bold text-[#111] leading-snug
                    ${isLong ? 'break-words whitespace-normal text-sm font-medium' : 'truncate'}`}>
                    {displayVal}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Charts */}
      {result.charts.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-[#999] uppercase tracking-widest mb-3">
            Visualizations ({result.charts.length})
          </p>
          <div className={`grid gap-4 ${result.charts.length > 1 ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-1'}`}>
            {result.charts.map((chart, i) => (
              <ChartRenderer key={i} chart={chart} />
            ))}
          </div>
        </div>
      )}

      {/* Footer meta */}
      <div className="flex items-center gap-3 pt-1">
        <span className="tag">⏱ {result.execution_time_ms}ms</span>
        {result.retry_count > 0 && (
          <span className="tag">🔄 {result.retry_count} {result.retry_count === 1 ? 'retry' : 'retries'}</span>
        )}
        <span className="text-[10px] text-[#CCC] font-mono">{result.analysis_id.slice(0, 8)}</span>
      </div>
    </div>
  )
}
