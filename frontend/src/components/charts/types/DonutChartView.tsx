import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { ChartData } from '../../../types/analysis'

const COLORS = ['#111111','#444444','#777777','#999999','#BBBBBB','#333333','#555555','#888888']

export default function DonutChartView({ chart }: { chart: ChartData }) {
  const total = chart.data.reduce((s, d) => s + (Number(d.value) || 0), 0)
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={chart.data} dataKey="value" nameKey="name"
          cx="50%" cy="50%" innerRadius={55} outerRadius={90}
        >
          {chart.data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E5E5E5' }}
          formatter={(val: number) => [`${val} (${total ? ((val / total) * 100).toFixed(1) : 0}%)`, '']}
        />
        <Legend iconType="circle" iconSize={10} wrapperStyle={{ fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  )
}
