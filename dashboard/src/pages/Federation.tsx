import { useState, useEffect } from 'react'
import { federationApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useToast } from '@/components/ui/use-toast'
import { formatRelativeTime, getStatusColor } from '@/lib/utils'
import { Network, Plus, RefreshCw, Trash2, AlertCircle } from 'lucide-react'

export default function Federation() {
  const [peers, setPeers] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    fetchPeers()
  }, [])

  const fetchPeers = async () => {
    setIsLoading(true)
    try {
      const data = await federationApi.listPeers()
      setPeers(data)
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to load peers',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleRemovePeer = async (peerId: string) => {
    if (!confirm('Remove this federation peer?')) return

    try {
      await federationApi.removePeer(peerId)
      toast({ title: 'Peer removed successfully' })
      fetchPeers()
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to remove peer',
      })
    }
  }

  const handleResolveConflicts = async (peerId: string) => {
    try {
      await federationApi.resolveConflicts(peerId)
      toast({ title: 'Conflicts resolved successfully' })
      fetchPeers()
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to resolve conflicts',
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Federation</h1>
          <p className="text-gray-400 mt-1">Manage federation peers and sync status</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Peer
        </Button>
      </div>

      {/* Federation Overview */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Total Peers</p>
                <p className="text-3xl font-bold text-white mt-2">{peers.length}</p>
              </div>
              <Network className="h-8 w-8 text-twilight-purple" />
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Active Peers</p>
                <p className="text-3xl font-bold text-white mt-2">
                  {peers.filter((p) => p.status === 'online').length}
                </p>
              </div>
              <div className="h-8 w-8 rounded-full bg-green-400/20 flex items-center justify-center">
                <div className="h-3 w-3 rounded-full bg-green-400 animate-pulse" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="metric-card">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Sync Conflicts</p>
                <p className="text-3xl font-bold text-white mt-2">
                  {peers.reduce((acc, p) => acc + (p.conflicts || 0), 0)}
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-yellow-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Peers Table */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Federation Peers</CardTitle>
            <Button variant="outline" size="sm" onClick={fetchPeers}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 skeleton rounded" />
              ))}
            </div>
          ) : peers.length === 0 ? (
            <div className="text-center py-12">
              <Network className="h-12 w-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No federation peers configured</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Peer ID</TableHead>
                  <TableHead>Address</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Sync</TableHead>
                  <TableHead>Conflicts</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {peers.map((peer) => (
                  <TableRow key={peer.id}>
                    <TableCell className="font-mono text-sm">
                      {peer.id.slice(0, 12)}...
                    </TableCell>
                    <TableCell>{peer.address}</TableCell>
                    <TableCell>
                      <span className={getStatusColor(peer.status)}>{peer.status}</span>
                    </TableCell>
                    <TableCell className="text-gray-400">
                      {formatRelativeTime(peer.last_sync)}
                    </TableCell>
                    <TableCell>
                      {peer.conflicts > 0 ? (
                        <span className="text-yellow-400">{peer.conflicts}</span>
                      ) : (
                        <span className="text-gray-400">0</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex space-x-2">
                        {peer.conflicts > 0 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleResolveConflicts(peer.id)}
                          >
                            Resolve
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRemovePeer(peer.id)}
                        >
                          <Trash2 className="h-4 w-4 text-red-400" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Network Topology Visualization */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <CardTitle>Network Topology</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center border border-twilight-purple/20 rounded bg-twilight-deep/30">
            <p className="text-gray-400">
              Network topology visualization (D3.js integration)
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
