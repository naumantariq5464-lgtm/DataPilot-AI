import { useState } from 'react'
import CSVUpload          from '../components/upload/CSVUpload'
import DatasetPreview     from '../components/upload/DatasetPreview'
import AnalysisInput      from '../components/analysis/AnalysisInput'
import AnalysisResultView from '../components/analysis/AnalysisResult'
import LoadingSpinner     from '../components/common/LoadingSpinner'
import { useDataset }     from '../hooks/useDataset'
import { useAnalysis }    from '../hooks/useAnalysis'
import type { DatasetUploadResponse } from '../types/dataset'

export default function NewAnalysis() {
  const { activeDataset, uploading, uploadError, uploadCSV } = useDataset()
  const { currentResult, isRunning, error: analysisError, runAnalysis } = useAnalysis()
  const [step, setStep]       = useState<'upload' | 'analyze'>('upload')
  const [previewOpen, setPreviewOpen] = useState(false)

  const handleUpload = async (file: File): Promise<DatasetUploadResponse | null> => {
    const result = await uploadCSV(file)
    if (result) setStep('analyze')
    return result
  }

  return (
    <div className="flex flex-col min-h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 md:px-8 py-4 md:py-5 border-b border-[#EBEBEB] bg-white">
        <div>
          <h1 className="text-lg md:text-xl font-bold text-[#111]">New Analysis</h1>
          <p className="text-xs md:text-sm text-[#888] mt-0.5">
            {step === 'upload' ? 'Upload a CSV to get started' : activeDataset?.filename}
          </p>
        </div>
        {step === 'analyze' && (
          <button onClick={() => setStep('upload')} className="btn-secondary text-xs px-3 py-2">
            ← Change
          </button>
        )}
      </div>

      <div className="flex-1 bg-[#FAFAFA]">

        {/* ── Upload step ── */}
        {step === 'upload' && (
          <div className="max-w-lg mx-auto px-4 md:px-6 py-6 md:py-10">
            <div className="bg-white border border-[#EBEBEB] rounded-2xl p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-[#111] rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0">1</div>
                <div>
                  <p className="text-sm font-semibold text-[#111]">Upload your dataset</p>
                  <p className="text-xs text-[#888]">CSV · Max 10MB</p>
                </div>
              </div>
              <CSVUpload onUpload={handleUpload} uploading={uploading} error={uploadError} />
            </div>

            <div className="flex items-center gap-3 my-4">
              <div className="flex-1 h-px bg-[#EBEBEB]"/>
              <span className="text-xs text-[#CCC]">then</span>
              <div className="flex-1 h-px bg-[#EBEBEB]"/>
            </div>

            <div className="bg-white border border-dashed border-[#DDD] rounded-2xl p-4 opacity-50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-[#F5F5F5] rounded-lg flex items-center justify-center text-xs font-bold text-[#999] shrink-0">2</div>
                <p className="text-sm text-[#999]">Ask your question in plain English</p>
              </div>
            </div>
          </div>
        )}

        {/* ── Analyze step ── */}
        {step === 'analyze' && activeDataset && (
          <div className="max-w-3xl mx-auto px-4 md:px-6 py-4 md:py-6 space-y-4">

            {/* Dataset collapsible */}
            <div className="bg-white border border-[#EBEBEB] rounded-2xl overflow-hidden">
              <button
                onClick={() => setPreviewOpen(!previewOpen)}
                className="w-full flex items-center justify-between px-4 md:px-5 py-3.5 hover:bg-[#FAFAFA] transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 bg-[#F5F5F5] rounded-lg flex items-center justify-center shrink-0">
                    <svg className="w-4 h-4 text-[#555]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
                        d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                  </div>
                  <div className="min-w-0 text-left">
                    <p className="text-sm font-semibold text-[#111] truncate">{activeDataset.filename}</p>
                    <p className="text-xs text-[#888]">
                      {activeDataset.row_count.toLocaleString()} rows · {activeDataset.column_count} cols
                    </p>
                  </div>
                </div>
                <svg className={`w-4 h-4 text-[#999] shrink-0 ml-2 transition-transform ${previewOpen ? 'rotate-180' : ''}`}
                  fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M19 9l-7 7-7-7"/>
                </svg>
              </button>
              {previewOpen && (
                <div className="px-4 md:px-5 pb-5 border-t border-[#F5F5F5]">
                  <div className="pt-4 overflow-x-auto">
                    <DatasetPreview dataset={activeDataset} />
                  </div>
                </div>
              )}
            </div>

            {/* Ask question */}
            <div className="bg-white border border-[#EBEBEB] rounded-2xl p-4 md:p-5">
              <p className="text-sm font-semibold text-[#111] mb-3">Ask a question</p>
              <AnalysisInput
                onSubmit={(p) => runAnalysis(activeDataset.dataset_id, p)}
                isRunning={isRunning}
              />
              {analysisError && (
                <div className="mt-3 text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl px-3 py-2.5">
                  {analysisError}
                </div>
              )}
            </div>

            {/* Loading */}
            {isRunning && (
              <div className="bg-white border border-[#EBEBEB] rounded-2xl p-8">
                <div className="flex flex-col items-center gap-3">
                  <LoadingSpinner size="md" />
                  <div className="text-center">
                    <p className="text-sm font-semibold text-[#111]">Analyzing…</p>
                    <p className="text-xs text-[#888] mt-1">AI → Sandbox → Charts</p>
                  </div>
                </div>
              </div>
            )}

            {/* Result */}
            {!isRunning && currentResult && (
              <AnalysisResultView result={currentResult} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
