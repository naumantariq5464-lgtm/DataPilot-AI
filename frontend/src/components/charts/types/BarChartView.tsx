import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import type { ChartData } from '../../../types/analysis'

export default function BarChartView({ chart }: { chart: ChartData }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chart.data} margin={{ top: 5, right: 20, left: 0, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
        <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#666' }} angle={-30} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11, fill: '#666' }} label={{ value: chart.y_label, angle: -90, position: 'insideLeft', style: { fontSize: 11, fill: '#666' } }} />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E5E5' }} />
        <Bar dataKey="value" fill="#111111" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
