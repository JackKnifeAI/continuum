import { useState, useEffect } from 'react'
import { systemApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { Save, Settings as SettingsIcon } from 'lucide-react'

export default function Settings() {
  const [config, setConfig] = useState<any>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    setIsLoading(true)
    try {
      const data = await systemApi.config()
      setConfig(data)
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to load configuration',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await systemApi.updateConfig(config)
      toast({ title: 'Configuration saved successfully' })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to save configuration',
      })
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-64 skeleton rounded" />
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-64 skeleton rounded-lg" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Settings</h1>
          <p className="text-gray-400 mt-1">Configure system parameters</p>
        </div>
        <Button onClick={handleSave} disabled={isSaving}>
          <Save className="mr-2 h-4 w-4" />
          {isSaving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>

      {/* General Settings */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <CardTitle>General Settings</CardTitle>
          <CardDescription>Core system configuration</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="api-url">API URL</Label>
              <Input
                id="api-url"
                value={config.api_url || ''}
                onChange={(e) => setConfig({ ...config, api_url: e.target.value })}
                className="bg-twilight-medium border-twilight-purple/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ws-url">WebSocket URL</Label>
              <Input
                id="ws-url"
                value={config.ws_url || ''}
                onChange={(e) => setConfig({ ...config, ws_url: e.target.value })}
                className="bg-twilight-medium border-twilight-purple/20"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rate Limiting */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <CardTitle>Rate Limiting</CardTitle>
          <CardDescription>API request rate limits</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="rate-limit">Requests per Minute</Label>
              <Input
                id="rate-limit"
                type="number"
                value={config.rate_limit || 60}
                onChange={(e) =>
                  setConfig({ ...config, rate_limit: parseInt(e.target.value) })
                }
                className="bg-twilight-medium border-twilight-purple/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="burst-limit">Burst Limit</Label>
              <Input
                id="burst-limit"
                type="number"
                value={config.burst_limit || 100}
                onChange={(e) =>
                  setConfig({ ...config, burst_limit: parseInt(e.target.value) })
                }
                className="bg-twilight-medium border-twilight-purple/20"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cache Settings */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <CardTitle>Cache Configuration</CardTitle>
          <CardDescription>Redis cache settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="cache-ttl">Default TTL (seconds)</Label>
              <Input
                id="cache-ttl"
                type="number"
                value={config.cache_ttl || 3600}
                onChange={(e) =>
                  setConfig({ ...config, cache_ttl: parseInt(e.target.value) })
                }
                className="bg-twilight-medium border-twilight-purple/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max-cache-size">Max Cache Size (MB)</Label>
              <Input
                id="max-cache-size"
                type="number"
                value={config.max_cache_size || 1024}
                onChange={(e) =>
                  setConfig({ ...config, max_cache_size: parseInt(e.target.value) })
                }
                className="bg-twilight-medium border-twilight-purple/20"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Feature Flags */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <CardTitle>Feature Flags</CardTitle>
          <CardDescription>Enable or disable system features</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            {[
              { key: 'federation_enabled', label: 'Federation' },
              { key: 'websocket_enabled', label: 'WebSocket Sync' },
              { key: 'embeddings_enabled', label: 'Embeddings' },
              { key: 'analytics_enabled', label: 'Analytics' },
            ].map((flag) => (
              <label key={flag.key} className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={config[flag.key] || false}
                  onChange={(e) =>
                    setConfig({ ...config, [flag.key]: e.target.checked })
                  }
                  className="h-4 w-4 rounded border-twilight-purple/20 bg-twilight-medium text-twilight-purple focus:ring-twilight-purple"
                />
                <span>{flag.label}</span>
              </label>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>Manage system API keys</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="openai-key">OpenAI API Key</Label>
              <Input
                id="openai-key"
                type="password"
                value={config.openai_api_key || ''}
                onChange={(e) =>
                  setConfig({ ...config, openai_api_key: e.target.value })
                }
                className="bg-twilight-medium border-twilight-purple/20"
                placeholder="sk-..."
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
