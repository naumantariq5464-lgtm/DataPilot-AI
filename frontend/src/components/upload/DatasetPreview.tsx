import type { DatasetUploadResponse } from '../../types/dataset'

interface DatasetPreviewProps {
  dataset: DatasetUploadResponse
}

export default function DatasetPreview({ dataset }: DatasetPreviewProps) {
  const previewColumns = Object.keys(dataset.preview[0] ?? {})

  return (
    <div className="space-y-4">
      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Rows',    value: dataset.row_count.toLocaleString() },
          { label: 'Columns', value: dataset.column_count },
          { label: 'File',    value: dataset.filename },
        ].map((s) => (
          <div key={s.label} className="card p-3">
            <p className="text-xs text-secondary">{s.label}</p>
            <p className="text-sm font-semibold text-primary mt-0.5 truncate">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Column info */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <p className="text-sm font-medium text-primary">Columns</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-muted">
              <tr>
                {['Name', 'Type', 'Nulls', 'Sample values'].map((h) => (
                  <th key={h} className="text-left px-4 py-2 text-secondary font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {dataset.columns.map((col) => (
                <tr key={col.name} className="hover:bg-muted/50">
                  <td className="px-4 py-2 font-medium text-primary">{col.name}</td>
                  <td className="px-4 py-2 text-secondary font-mono">{col.dtype}</td>
                  <td className="px-4 py-2 text-secondary">{col.null_count}</td>
                  <td className="px-4 py-2 text-secondary truncate max-w-[200px]">
                    {col.sample_values.slice(0, 3).join(', ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Data preview */}
      {dataset.preview.length > 0 && (
        <div className="card overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <p className="text-sm font-medium text-primary">
              Preview <span className="text-secondary font-normal">(first {dataset.preview.length} rows)</span>
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs whitespace-nowrap">
              <thead className="bg-muted">
                <tr>
                  {previewColumns.map((col) => (
                    <th key={col} className="text-left px-4 py-2 text-secondary font-medium">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {dataset.preview.map((row, i) => (
                  <tr key={i} className="hover:bg-muted/50">
                    {previewColumns.map((col) => (
                      <td key={col} className="px-4 py-2 text-primary max-w-[150px] truncate">
                        {String(row[col] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
