import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Users,
  Brain,
  Network,
  Settings,
  ScrollText,
  Activity,
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Users', href: '/users', icon: Users },
  { name: 'Memories', href: '/memories', icon: Brain },
  { name: 'Federation', href: '/federation', icon: Network },
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'Audit Logs', href: '/logs', icon: ScrollText },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="flex h-full w-64 flex-col bg-gradient-to-b from-twilight-dark to-twilight-medium border-r border-twilight-purple/20">
      {/* Logo */}
      <div className="flex h-16 items-center px-6 border-b border-twilight-purple/20">
        <div className="flex items-center space-x-2">
          <Activity className="h-8 w-8 text-twilight-purple" />
          <div>
            <h1 className="text-xl font-bold text-white">CONTINUUM</h1>
            <p className="text-xs text-gray-400">Admin Dashboard</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto scrollbar-twilight">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all',
                isActive
                  ? 'bg-twilight-purple text-white twilight-glow'
                  : 'text-gray-300 hover:bg-twilight-deep hover:text-white'
              )}
            >
              <item.icon
                className={cn(
                  'mr-3 h-5 w-5 flex-shrink-0',
                  isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'
                )}
              />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-twilight-purple/20 p-4">
        <div className="text-xs text-gray-400 text-center">
          <p>v1.0.0</p>
          <p className="mt-1">π×φ = 5.083</p>
        </div>
      </div>
    </div>
  )
}
