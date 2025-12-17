import { useState, useEffect } from 'react'
import { memoriesApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { formatRelativeTime, exportToCSV } from '@/lib/utils'
import { Search, Download, Brain, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react'

export default function Memories() {
  const [memories, setMemories] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [selectedMemory, setSelectedMemory] = useState<any | null>(null)
  const [showMemoryDialog, setShowMemoryDialog] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    fetchMemories()
  }, [page, search])

  const fetchMemories = async () => {
    setIsLoading(true)
    try {
      const response = await memoriesApi.list({
        page,
        page_size: 20,
        search: search || undefined,
      })
      setMemories(response.items)
      setTotalPages(response.total_pages)
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to load memories',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteMemory = async (memoryId: string) => {
    if (!confirm('Are you sure you want to delete this memory?')) return

    try {
      await memoriesApi.delete(memoryId)
      toast({ title: 'Memory deleted successfully' })
      fetchMemories()
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to delete memory',
      })
    }
  }

  const handleExport = async () => {
    try {
      const blob = await memoriesApi.export({ search })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `continuum-memories-${Date.now()}.json`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to export memories',
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Memories</h1>
          <p className="text-gray-400 mt-1">Browse and manage memory records</p>
        </div>
        <Button variant="outline" onClick={handleExport}>
          <Download className="mr-2 h-4 w-4" />
          Export
        </Button>
      </div>

      {/* Search */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search memories..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-twilight-medium border-twilight-purple/20"
            />
          </div>
        </CardContent>
      </Card>

      {/* Memories Table */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <CardTitle>All Memories ({memories.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 skeleton rounded" />
              ))}
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Content</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Importance</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {memories.map((memory) => (
                    <TableRow
                      key={memory.id}
                      className="cursor-pointer hover:bg-twilight-medium/50"
                      onClick={() => {
                        setSelectedMemory(memory)
                        setShowMemoryDialog(true)
                      }}
                    >
                      <TableCell className="max-w-md">
                        <div className="flex items-start space-x-2">
                          <Brain className="h-4 w-4 mt-1 text-twilight-purple flex-shrink-0" />
                          <p className="truncate">{memory.content}</p>
                        </div>
                      </TableCell>
                      <TableCell>{memory.user_id?.slice(0, 8)}</TableCell>
                      <TableCell>{memory.memory_type || 'general'}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          {[...Array(5)].map((_, i) => (
                            <div
                              key={i}
                              className={`h-2 w-2 rounded-full ${
                                i < (memory.importance || 0)
                                  ? 'bg-twilight-purple'
                                  : 'bg-gray-600'
                              }`}
                            />
                          ))}
                        </div>
                      </TableCell>
                      <TableCell className="text-gray-400">
                        {formatRelativeTime(memory.created_at)}
                      </TableCell>
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteMemory(memory.id)}
                        >
                          <Trash2 className="h-4 w-4 text-red-400" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-gray-400">
                  Page {page} of {totalPages}
                </p>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page + 1)}
                    disabled={page === totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Memory Details Dialog */}
      <Dialog open={showMemoryDialog} onOpenChange={setShowMemoryDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Memory Details</DialogTitle>
            <DialogDescription>Full memory record information</DialogDescription>
          </DialogHeader>
          {selectedMemory && (
            <div className="space-y-4 max-h-96 overflow-y-auto scrollbar-twilight">
              <div>
                <p className="text-sm text-gray-400 mb-2">Content</p>
                <p className="p-3 bg-twilight-medium rounded">{selectedMemory.content}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-400">User ID</p>
                  <p className="font-mono text-sm">{selectedMemory.user_id}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Memory Type</p>
                  <p>{selectedMemory.memory_type || 'general'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Importance</p>
                  <p>{selectedMemory.importance || 0} / 5</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Created</p>
                  <p>{new Date(selectedMemory.created_at).toLocaleString()}</p>
                </div>
              </div>
              {selectedMemory.metadata && (
                <div>
                  <p className="text-sm text-gray-400 mb-2">Metadata</p>
                  <pre className="p-3 bg-twilight-medium rounded text-xs overflow-x-auto">
                    {JSON.stringify(selectedMemory.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
