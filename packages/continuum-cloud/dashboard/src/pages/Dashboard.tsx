import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useMetrics } from '@/lib/hooks/useMetrics'
import { formatBytes, formatNumber, getStatusColor } from '@/lib/utils'
import { Users, Brain, Zap, HardDrive, Server, Database, CloudCog, Network } from 'lucide-react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function Dashboard() {
  const { metrics, isLoading } = useMetrics()

  if (isLoading || !metrics) {
    return <DashboardSkeleton />
  }

  // Mock data for charts - in production, this would come from the API
  const performanceData = Array.from({ length: 24 }, (_, i) => ({
    time: `${i}:00`,
    qps: Math.floor(Math.random() * 100) + 50,
    latency: Math.floor(Math.random() * 50) + 10,
  }))

  const storageData = Array.from({ length: 7 }, (_, i) => ({
    day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i],
    used: Math.floor(Math.random() * 20) + 60,
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">System overview and metrics</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Users"
          value={formatNumber(metrics.users.total)}
          icon={Users}
          description={`${metrics.users.active} active`}
          trend="+12% from last month"
        />
        <MetricCard
          title="Total Memories"
          value={formatNumber(metrics.memories.total)}
          icon={Brain}
          description={formatBytes(metrics.memories.size)}
          trend={`+${metrics.memories.growth_rate}% growth`}
        />
        <MetricCard
          title="Queries/sec"
          value={metrics.performance.queries_per_sec.toFixed(1)}
          icon={Zap}
          description={`${metrics.performance.avg_response_time}ms avg`}
          trend={`${metrics.performance.cache_hit_rate}% cache hit`}
        />
        <MetricCard
          title="Storage Used"
          value={`${metrics.storage.percent}%`}
          icon={HardDrive}
          description={`${formatBytes(metrics.storage.used)} / ${formatBytes(metrics.storage.total)}`}
          trend="Within capacity"
        />
      </div>

      {/* Health Status */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <CardTitle>System Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <HealthIndicator
              name="API Server"
              status={metrics.health.api}
              icon={Server}
            />
            <HealthIndicator
              name="Database"
              status={metrics.health.database}
              icon={Database}
            />
            <HealthIndicator
              name="Cache Layer"
              status={metrics.health.cache}
              icon={CloudCog}
            />
            <HealthIndicator
              name="Federation"
              status={metrics.health.federation}
              icon={Network}
            />
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Performance Chart */}
        <Card className="border-twilight-purple/20 bg-twilight-dark/50">
          <CardHeader>
            <CardTitle>Query Performance (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                <XAxis dataKey="time" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #7c3aed' }}
                />
                <Line type="monotone" dataKey="qps" stroke="#7c3aed" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Storage Chart */}
        <Card className="border-twilight-purple/20 bg-twilight-dark/50">
          <CardHeader>
            <CardTitle>Storage Growth (7d)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={storageData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                <XAxis dataKey="day" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #3b82f6' }}
                />
                <Area type="monotone" dataKey="used" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Grafana Embed (if enabled) */}
      {import.meta.env.VITE_ENABLE_GRAFANA && (
        <Card className="border-twilight-purple/20 bg-twilight-dark/50">
          <CardHeader>
            <CardTitle>Detailed Metrics (Grafana)</CardTitle>
          </CardHeader>
          <CardContent>
            <iframe
              src={`${import.meta.env.VITE_GRAFANA_URL}/d/${import.meta.env.VITE_GRAFANA_DASHBOARD_ID}`}
              width="100%"
              height="600"
              frameBorder="0"
              className="rounded-md"
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
}: {
  title: string
  value: string
  icon: any
  description: string
  trend: string
}) {
  return (
    <Card className="metric-card">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-gray-400">{title}</p>
            <p className="text-3xl font-bold text-white mt-2">{value}</p>
            <p className="text-xs text-gray-500 mt-1">{description}</p>
            <p className="text-xs text-twilight-purple mt-2">{trend}</p>
          </div>
          <Icon className="h-8 w-8 text-twilight-purple" />
        </div>
      </CardContent>
    </Card>
  )
}

function HealthIndicator({
  name,
  status,
  icon: Icon,
}: {
  name: string
  status: string
  icon: any
}) {
  return (
    <div className="flex items-center space-x-3 p-3 rounded-lg bg-twilight-medium/50">
      <Icon className={`h-6 w-6 ${getStatusColor(status)}`} />
      <div>
        <p className="text-sm font-medium text-white">{name}</p>
        <p className={`text-xs ${getStatusColor(status)}`}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </p>
      </div>
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-10 w-64 skeleton rounded" />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 skeleton rounded-lg" />
        ))}
      </div>
      <div className="h-48 skeleton rounded-lg" />
      <div className="grid gap-4 md:grid-cols-2">
        <div className="h-80 skeleton rounded-lg" />
        <div className="h-80 skeleton rounded-lg" />
      </div>
    </div>
  )
}
