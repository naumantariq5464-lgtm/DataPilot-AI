import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import type { ChartData } from '../../../types/analysis'

export default function ScatterChartView({ chart }: { chart: ChartData }) {
  // scatter data uses {x, y} keys
  const scatterData = chart.data.map((d) => ({
    x: d.x ?? d.name,
    y: d.y ?? d.value,
  }))
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ScatterChart margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
        <XAxis dataKey="x" name={chart.x_label} tick={{ fontSize: 11, fill: '#666' }} />
        <YAxis dataKey="y" name={chart.y_label} tick={{ fontSize: 11, fill: '#666' }} />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E5E5' }}
          cursor={{ strokeDasharray: '3 3' }}
        />
        <Scatter data={scatterData} fill="#111111" />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
