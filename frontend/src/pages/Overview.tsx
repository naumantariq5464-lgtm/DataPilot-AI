import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useDataset } from '../hooks/useDataset'
import { useAnalysis } from '../hooks/useAnalysis'

export default function Overview() {
  const { user } = useAuth()
  const { datasets, fetchDatasets } = useDataset()
  const { history, fetchHistory } = useAnalysis()

  useEffect(() => {
    fetchDatasets()
    fetchHistory()
  }, []) // eslint-disable-line

  const totalCharts = history.reduce((s, h) => s + h.chart_count, 0)
  const firstName = user?.name?.split(' ')[0] || user?.email?.split('@')[0] || 'there'

  return (
    <div className="flex flex-col min-h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 md:px-8 py-4 md:py-5 border-b border-[#EBEBEB] bg-white">
        <div>
          <h1 className="text-lg md:text-xl font-bold text-[#111]">Good day, {firstName} 👋</h1>
          <p className="text-xs md:text-sm text-[#888] mt-0.5">Here's what's happening with your data</p>
        </div>
        <Link to="/analysis/new" className="btn-primary text-xs md:text-sm px-3 py-2">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4"/>
          </svg>
          <span className="hidden sm:inline">New Analysis</span>
          <span className="sm:hidden">New</span>
        </Link>
      </div>

      <div className="flex-1 px-4 md:px-8 py-5 md:py-6 space-y-6 bg-[#FAFAFA]">

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Datasets',  value: datasets.length, emoji: '🗂️' },
            { label: 'Analyses',  value: history.length,  emoji: '⚡' },
            { label: 'Charts',    value: totalCharts,     emoji: '📊' },
          ].map((s) => (
            <div key={s.label} className="bg-white rounded-2xl border border-[#EBEBEB] p-3 md:p-5">
              <div className="text-xl md:text-2xl mb-1 md:mb-2">{s.emoji}</div>
              <p className="text-2xl md:text-3xl font-bold text-[#111]">{s.value}</p>
              <p className="text-[11px] md:text-sm text-[#888] mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Quick actions */}
        <div>
          <p className="text-[10px] md:text-xs font-semibold text-[#999] uppercase tracking-widest mb-3">Quick Actions</p>
          <div className="grid grid-cols-2 gap-3">
            <Link to="/analysis/new" className="bg-[#111] text-white rounded-2xl p-4 md:p-5 hover:bg-[#333] transition-colors">
              <div className="w-8 h-8 bg-white/10 rounded-xl flex items-center justify-center mb-2 md:mb-3">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4"/>
                </svg>
              </div>
              <p className="text-xs md:text-sm font-semibold">New Analysis</p>
              <p className="text-[10px] md:text-xs text-white/60 mt-0.5">Upload CSV → Ask AI</p>
            </Link>
            <Link to="/datasets" className="bg-white rounded-2xl border border-[#EBEBEB] p-4 md:p-5 hover:border-[#AAAAAA] transition-colors">
              <div className="w-8 h-8 bg-[#F5F5F5] rounded-xl flex items-center justify-center mb-2 md:mb-3">
                <svg className="w-4 h-4 text-[#555]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
                    d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                </svg>
              </div>
              <p className="text-xs md:text-sm font-semibold text-[#111]">My Datasets</p>
              <p className="text-[10px] md:text-xs text-[#888] mt-0.5">{datasets.length} file{datasets.length !== 1 ? 's' : ''}</p>
            </Link>
          </div>
        </div>

        {/* Recent */}
        {history.length > 0 ? (
          <div>
            <div className="flex items-center justify-between mb-3">
              <p className="text-[10px] md:text-xs font-semibold text-[#999] uppercase tracking-widest">Recent Analyses</p>
              <Link to="/history" className="text-xs text-[#666] hover:text-[#111]">View all →</Link>
            </div>
            <div className="space-y-2">
              {history.slice(0, 5).map((item) => (
                <Link key={item.analysis_id} to="/history"
                  className="flex items-center justify-between bg-white border border-[#EBEBEB]
                             rounded-xl px-4 py-3 hover:border-[#AAAAAA] transition-colors"
                >
                  <p className="text-xs md:text-sm text-[#333] truncate">{item.prompt}</p>
                  <span className="text-[10px] md:text-xs font-medium px-2 py-0.5 rounded-full bg-[#F5F5F5] text-[#666] ml-2 shrink-0">
                    {item.chart_count} charts
                  </span>
                </Link>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-white border border-dashed border-[#DDD] rounded-2xl p-8 text-center">
            <div className="text-3xl mb-3">📈</div>
            <p className="text-sm font-semibold text-[#333]">No analyses yet</p>
            <p className="text-xs text-[#888] mt-1 mb-4">Upload a CSV and ask your first question</p>
            <Link to="/analysis/new" className="btn-primary text-xs px-3 py-2">Start Analyzing</Link>
          </div>
        )}
      </div>
    </div>
  )
}
