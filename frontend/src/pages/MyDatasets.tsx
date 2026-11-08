import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { useDataset }  from '../hooks/useDataset'

export default function MyDatasets() {
  const { datasets, loading, fetchDatasets, deleteDataset } = useDataset()
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => { fetchDatasets() }, []) // eslint-disable-line

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this dataset? This cannot be undone.')) return
    setDeletingId(id)
    try { await deleteDataset(id) } finally { setDeletingId(null) }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-5 border-b border-[#EBEBEB] bg-white shrink-0">
        <div>
          <h1 className="text-xl font-bold text-[#111]">My Datasets</h1>
          <p className="text-sm text-[#888] mt-0.5">{datasets.length} uploaded file{datasets.length !== 1 ? 's' : ''}</p>
        </div>
        <Link to="/analysis/new" className="btn-primary btn-sm">+ Upload New</Link>
      </div>

      <div className="flex-1 overflow-y-auto bg-[#FAFAFA] px-8 py-6">
        {loading ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner size="md" text="Loading…" />
          </div>
        ) : datasets.length === 0 ? (
          <div className="max-w-md mx-auto text-center py-16">
            <div className="w-14 h-14 bg-white border border-[#EBEBEB] rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl">🗂️</div>
            <p className="text-sm font-semibold text-[#333]">No datasets yet</p>
            <p className="text-xs text-[#888] mt-1 mb-4">Upload a CSV file to get started</p>
            <Link to="/analysis/new" className="btn-primary btn-sm">Upload Dataset</Link>
          </div>
        ) : (
          <div className="max-w-2xl space-y-2">
            {datasets.map((ds) => (
              <div key={ds.dataset_id}
                className="bg-white border border-[#EBEBEB] rounded-xl flex items-center justify-between px-4 py-3.5 hover:border-[#AAAAAA] transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 h-9 bg-[#F5F5F5] rounded-xl flex items-center justify-center shrink-0">
                    <svg className="w-4 h-4 text-[#555]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75}
                        d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-[#111] truncate">{ds.filename}</p>
                    <p className="text-xs text-[#888]">{ds.row_count.toLocaleString()} rows · {ds.column_count} columns</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-3">
                  <button
                    onClick={() => navigate('/analysis/new')}
                    className="btn-primary btn-sm"
                  >
                    Analyze
                  </button>
                  <button
                    onClick={() => handleDelete(ds.dataset_id)}
                    disabled={deletingId === ds.dataset_id}
                    className="btn-ghost btn-sm text-red-400 hover:text-red-600 hover:bg-red-50"
                  >
                    {deletingId === ds.dataset_id ? '…' : 'Delete'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
