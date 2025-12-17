import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/lib/auth'
import { authApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { Activity, Loader2 } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)
  const { toast } = useToast()

  // Demo mode for local development
  const handleDemoLogin = () => {
    const demoUser = {
      id: 'demo-user',
      username: 'admin',
      email: 'admin@continuum.local',
      role: 'admin' as const,
    }
    login(demoUser, 'demo-token', 'demo-refresh-token')
    toast({
      title: 'Demo Mode Activated',
      description: 'Welcome to CONTINUUM Dashboard!',
    })
    navigate('/')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const response = await authApi.login(username, password)
      login(response.user, response.access_token, response.refresh_token)
      toast({
        title: 'Login successful',
        description: `Welcome back, ${response.user.username}!`,
      })
      navigate('/')
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Login failed',
        description: error.response?.data?.message || 'Invalid credentials',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-twilight-gradient p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="inline-flex items-center justify-center space-x-2 mb-2">
            <Activity className="h-12 w-12 text-twilight-purple" />
          </div>
          <h1 className="text-3xl font-bold text-white">CONTINUUM</h1>
          <p className="text-gray-400 mt-1">Admin Dashboard</p>
        </div>

        {/* Login Card */}
        <Card className="border-twilight-purple/20 bg-twilight-dark/80 backdrop-blur">
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>
              Enter your credentials to access the dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="admin"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={isLoading}
                  className="bg-twilight-medium border-twilight-purple/20"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  className="bg-twilight-medium border-twilight-purple/20"
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>

              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-twilight-purple/20" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-twilight-dark px-2 text-gray-400">Or</span>
                </div>
              </div>

              <Button
                type="button"
                variant="outline"
                className="w-full border-twilight-purple/40 hover:bg-twilight-purple/20"
                onClick={handleDemoLogin}
              >
                Enter Demo Mode (Local)
              </Button>
            </form>

            <div className="mt-6 text-center text-xs text-gray-400">
              <p>π×φ = 5.083203692315260</p>
              <p className="mt-1">Twilight Boundary Authentication</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
