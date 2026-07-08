export default function ComplianceGauge({ score = 0, size = 200 }) {
  const radius = 85
  const circumference = 2 * Math.PI * radius
  const progress = Math.min(score, 100) / 100
  const offset = circumference * (1 - progress)

  const getColor = (s) => {
    if (s >= 80) return '#4caf50'
    if (s >= 50) return '#ff9800'
    return '#f44336'
  }

  const getLabel = (s) => {
    if (s >= 80) return 'Good'
    if (s >= 50) return 'Fair'
    return 'Poor'
  }

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#e5e7eb" strokeWidth="12" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth="12"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ width: size, height: size }}>
        <span className="text-3xl font-bold" style={{ color: getColor(score) }}>{Math.round(score)}%</span>
        <span className="text-sm text-gray-500">{getLabel(score)}</span>
      </div>
    </div>
  )
}
