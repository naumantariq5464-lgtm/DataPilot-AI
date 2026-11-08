import type { ChartData } from '../../../types/analysis'

// Color scale from white to black
function getColor(value: number, min: number, max: number): string {
  const normalized = max === min ? 0.5 : (value - min) / (max - min)
  const lightness = Math.round(100 - normalized * 75) // 100% (white) → 25% (dark)
  return `hsl(0, 0%, ${lightness}%)`
}

function getTextColor(value: number, min: number, max: number): string {
  const normalized = max === min ? 0.5 : (value - min) / (max - min)
  return normalized > 0.55 ? '#ffffff' : '#111111'
}

export default function HeatmapView({ chart }: { chart: ChartData }) {
  const data = chart.data
  if (!data.length) return <p className="text-sm text-secondary p-4">No data</p>

  // Collect all numeric values for scale
  const allValues: number[] = []
  data.forEach((row) => {
    Object.entries(row).forEach(([k, v]) => {
      if (k !== 'name' && k !== 'index' && typeof v === 'number') {
        allValues.push(v)
      }
    })
  })
  const min = Math.min(...allValues)
  const max = Math.max(...allValues)

  const cols = Object.keys(data[0]).filter((k) => k !== 'name' && k !== 'index')

  return (
    <div className="overflow-x-auto">
      <table className="text-xs border-collapse">
        <thead>
          <tr>
            <th className="px-3 py-2 text-left text-secondary font-medium">—</th>
            {cols.map((c) => (
              <th key={c} className="px-3 py-2 text-center text-secondary font-medium whitespace-nowrap">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              <td className="px-3 py-2 font-medium text-primary whitespace-nowrap">{String(row.name ?? i)}</td>
              {cols.map((col) => {
                const val = Number(row[col] ?? 0)
                return (
                  <td
                    key={col}
                    className="px-3 py-2 text-center font-mono w-14 h-10"
                    style={{ backgroundColor: getColor(val, min, max), color: getTextColor(val, min, max) }}
                    title={`${row.name} × ${col}: ${val}`}
                  >
                    {val.toFixed(2)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
