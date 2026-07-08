import { Doughnut } from 'react-chartjs-2'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

const COLORS = ['#3f51b5', '#ff9800', '#4caf50', '#f44336', '#9c27b0', '#00bcd4']

export default function FindingChart({ data = {} }) {
  const entries = Object.entries(data)
  if (!entries.length) return <div className="text-center py-8 text-gray-400">No findings data</div>

  const chartData = {
    labels: entries.map(([k]) => k),
    datasets: [{
      data: entries.map(([, v]) => v),
      backgroundColor: COLORS.slice(0, entries.length),
      borderWidth: 0,
    }],
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">Findings by Type</h3>
      <div className="max-w-xs mx-auto">
        <Doughnut data={chartData} options={{ cutout: '65%', plugins: { legend: { position: 'bottom' } } }} />
      </div>
    </div>
  )
}
