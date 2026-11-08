import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import type { ChartData } from '../../../types/analysis'

const COLORS = ['#111111', '#555555', '#888888', '#BBBBBB']

export default function GroupedBarView({ chart }: { chart: ChartData }) {
  if (!chart.data.length) return null
  const keys = Object.keys(chart.data[0]).filter((k) => k !== 'name')

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chart.data} margin={{ top: 5, right: 20, left: 0, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E5" />
        <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#666' }} angle={-30} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11, fill: '#666' }} />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E5E5' }} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {keys.map((key, i) => (
          <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} radius={[3, 3, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
