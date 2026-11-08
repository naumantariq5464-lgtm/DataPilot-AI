import type { ChartData } from '../../../types/analysis'

// Recharts doesn't have a native boxplot — we render a clean table-style summary
export default function BoxPlotView({ chart }: { chart: ChartData }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead className="bg-muted">
          <tr>
            {['Column', 'Min', 'Q1', 'Median', 'Q3', 'Max', 'Outliers'].map((h) => (
              <th key={h} className="text-left px-4 py-2.5 text-secondary font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {chart.data.map((row, i) => (
            <tr key={i} className="hover:bg-muted/50">
              <td className="px-4 py-2.5 font-medium text-primary">{String(row.name ?? row.column ?? i)}</td>
              <td className="px-4 py-2.5 text-secondary font-mono">{String(row.min ?? '—')}</td>
              <td className="px-4 py-2.5 text-secondary font-mono">{String(row.q1 ?? '—')}</td>
              <td className="px-4 py-2.5 text-primary font-mono font-medium">{String(row.median ?? row.value ?? '—')}</td>
              <td className="px-4 py-2.5 text-secondary font-mono">{String(row.q3 ?? '—')}</td>
              <td className="px-4 py-2.5 text-secondary font-mono">{String(row.max ?? '—')}</td>
              <td className="px-4 py-2.5 text-secondary">{String(row.outliers ?? '—')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
