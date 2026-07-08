import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

export default function TrendChart({ data = [] }) {
  if (!data.length) return <div className="text-center py-8 text-gray-400">No trend data</div>

  const chartData = {
    labels: data.map((d) => d.date?.slice(5) || ''),
    datasets: [{
      label: 'Risk Score',
      data: data.map((d) => d.score || 0),
      fill: true,
      borderColor: '#3f51b5',
      backgroundColor: 'rgba(63, 81, 181, 0.1)',
      tension: 0.4,
      pointRadius: 3,
    }],
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">Risk Score Trend</h3>
      <Line data={chartData} options={{
        responsive: true,
        scales: { y: { beginAtZero: true, max: 100, grid: { color: '#f3f4f6' } }, x: { grid: { display: false } } },
        plugins: { legend: { display: false } },
      }} />
    </div>
  )
}
