import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import LoadingSpinner from '../components/common/LoadingSpinner'
import AnalysisResultView from '../components/analysis/AnalysisResult'
import { useAnalysis } from '../hooks/useAnalysis'
import type { AnalysisResult } from '../types/analysis'

export default function AnalysisHistory() {
  const { history, fetchHistory, fetchResult } = useAnalysis()
  const [loading, setLoading]     = useState(false)
  const [selected, setSelected]   = useState<AnalysisResult | null>(null)
  const [fetching, setFetching]   = useState(false)
  const [detailOpen, setDetailOpen] = useState(false) // mobile: open detail view

  useEffect(() => {
    setLoading(true)
    fetchHistory().finally(() => setLoading(false))
  }, []) // eslint-disable-line

  const handleView = async (id: string) => {
    if (selected?.analysis_id === id) { setDetailOpen(true); return }
    setFetching(true)
    const r = await fetchResult(id)
    if (r) { setSelected(r); setDetailOpen(true) }
    setFetching(false)
  }

  return (
    <div className="flex flex-col min-h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 md:px-8 py-4 md:py-5 border-b border-[#EBEBEB] bg-white">
        <div>
          <h1 className="text-lg md:text-xl font-bold text-[#111]">
            {/* Mobile: show back button when detail open */}
            {detailOpen && selected ? (
              <button
                onClick={() => setDetailOpen(false)}
                className="flex items-center gap-2 text-[#111]"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7"/>
                </svg>
                Analysis History
              </button>
            ) : 'Analysis History'}
          </h1>
          <p className="text-xs md:text-sm text-[#888] mt-0.5">{history.length} past analyses</p>
        </div>
        <Link to="/analysis/new" className="btn-primary text-xs px-3 py-2">+ New</Link>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center bg-[#FAFAFA]">
          <LoadingSpinner size="md" text="Loading…" />
        </div>
      ) : history.length === 0 ? (
        <div className="flex-1 flex items-center justify-center bg-[#FAFAFA] px-4">
          <div className="text-center">
            <div className="text-4xl mb-3">⏱️</div>
            <p className="text-sm font-semibold text-[#333]">No analyses yet</p>
            <p className="text-xs text-[#888] mt-1 mb-4">Run your first analysis to see it here</p>
            <Link to="/analysis/new" className="btn-primary text-xs px-3 py-2">Start Analyzing</Link>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex overflow-hidden bg-[#FAFAFA]">

          {/* ── DESKTOP: side-by-side ── */}
          {/* List */}
          <div className={`
            md:w-72 md:shrink-0 md:border-r border-[#EBEBEB] overflow-y-auto bg-white p-3 space-y-1.5
            ${detailOpen ? 'hidden md:block' : 'flex-1 md:flex-none'}
          `}>
            {history.map((item) => (
              <button
                key={item.analysis_id}
                onClick={() => handleView(item.analysis_id)}
                className={`
                  w-full text-left p-3.5 rounded-xl transition-all duration-150
                  ${selected?.analysis_id === item.analysis_id
                    ? 'bg-[#111] text-white'
                    : 'hover:bg-[#F5F5F5] text-[#333]'
                  }
                `}
              >
                <p className={`text-xs font-medium line-clamp-2 leading-relaxed
                  ${selected?.analysis_id === item.analysis_id ? 'text-white' : 'text-[#333]'}`}>
                  {item.prompt}
                </p>
                <span className={`inline-block mt-2 text-[10px] font-medium px-2 py-0.5 rounded-full
                  ${selected?.analysis_id === item.analysis_id
                    ? 'bg-white/20 text-white'
                    : 'bg-[#F0F0F0] text-[#666]'
                  }`}>
                  {item.chart_count} charts
                </span>
              </button>
            ))}
          </div>

          {/* Detail */}
          <div className={`
            flex-1 overflow-y-auto p-4 md:p-6
            ${detailOpen ? 'flex-1' : 'hidden md:block'}
          `}>
            {fetching ? (
              <div className="flex items-center justify-center h-40">
                <LoadingSpinner size="md" text="Loading…" />
              </div>
            ) : selected ? (
              <AnalysisResultView result={selected} />
            ) : (
              <div className="hidden md:flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-4xl mb-3">👈</div>
                  <p className="text-sm text-[#888]">Select an analysis to view results</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
