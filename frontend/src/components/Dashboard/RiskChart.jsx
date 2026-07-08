import { Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import { SEVERITY_COLORS } from '../../utils/constants'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

export default function RiskChart({ data = [] }) {
  const labels = data.map((d) => d.data_type || d.dataType)
  const counts = data.map((d) => d.total_count || d.count || 0)

  const chartData = {
    labels,
    datasets: [{
      label: 'Findings',
      data: counts,
      backgroundColor: data.map((d) => {
        const s = d.severity || d.max_severity || 'LOW'
        return SEVERITY_COLORS[s]?.bg?.replace('bg-', '#') || '#3f51b5'
      }),
      borderRadius: 6,
    }],
  }

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, grid: { color: '#f3f4f6' } },
      x: { grid: { display: false } },
    },
  }

  if (!data.length) return <div className="text-center py-8 text-gray-400">No data available</div>
  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">Risk Distribution</h3>
      <Bar data={chartData} options={options} />
    </div>
  )
}
