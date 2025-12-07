import { useState, useEffect } from 'react'
import { usersApi } from '@/lib/api'
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { formatRelativeTime, getStatusColor, exportToCSV } from '@/lib/utils'
import {
  Search,
  UserPlus,
  MoreVertical,
  Download,
  Ban,
  Trash2,
  Key,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export default function Users() {
  const [users, setUsers] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [selectedUser, setSelectedUser] = useState<any | null>(null)
  const [showUserDialog, setShowUserDialog] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    fetchUsers()
  }, [page, search])

  const fetchUsers = async () => {
    setIsLoading(true)
    try {
      const response = await usersApi.list({
        page,
        page_size: 20,
        search: search || undefined,
      })
      setUsers(response.items)
      setTotalPages(response.total_pages)
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to load users',
        description: 'An error occurred while fetching users',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuspendUser = async (userId: string) => {
    try {
      await usersApi.suspend(userId)
      toast({ title: 'User suspended successfully' })
      fetchUsers()
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to suspend user',
      })
    }
  }

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure? This action cannot be undone.')) return

    try {
      await usersApi.delete(userId)
      toast({ title: 'User deleted successfully' })
      fetchUsers()
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to delete user',
      })
    }
  }

  const handleResetPassword = async (userId: string) => {
    try {
      const response = await usersApi.resetPassword(userId)
      toast({
        title: 'Password reset',
        description: `New password: ${response.new_password}`,
      })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to reset password',
      })
    }
  }

  const handleExport = () => {
    const exportData = users.map((user) => ({
      id: user.id,
      username: user.username,
      email: user.email,
      status: user.status,
      plan: user.plan_tier,
      memories: user.memory_count,
      last_active: user.last_active,
      created_at: user.created_at,
    }))
    exportToCSV(exportData, `continuum-users-${Date.now()}.csv`)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Users</h1>
          <p className="text-gray-400 mt-1">Manage user accounts and permissions</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button>
            <UserPlus className="mr-2 h-4 w-4" />
            Add User
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search users..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 bg-twilight-medium border-twilight-purple/20"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <CardTitle>All Users ({users.length})</CardTitle>
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
                    <TableHead>Username</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Memories</TableHead>
                    <TableHead>Last Active</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow
                      key={user.id}
                      className="cursor-pointer hover:bg-twilight-medium/50"
                      onClick={() => {
                        setSelectedUser(user)
                        setShowUserDialog(true)
                      }}
                    >
                      <TableCell className="font-medium">{user.username}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <span className={`text-sm ${getStatusColor(user.status)}`}>
                          {user.status}
                        </span>
                      </TableCell>
                      <TableCell>{user.plan_tier}</TableCell>
                      <TableCell>{user.memory_count || 0}</TableCell>
                      <TableCell className="text-gray-400">
                        {formatRelativeTime(user.last_active)}
                      </TableCell>
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleResetPassword(user.id)}>
                              <Key className="mr-2 h-4 w-4" />
                              Reset Password
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleSuspendUser(user.id)}>
                              <Ban className="mr-2 h-4 w-4" />
                              Suspend
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDeleteUser(user.id)}
                              className="text-red-400"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
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

      {/* User Details Dialog */}
      <Dialog open={showUserDialog} onOpenChange={setShowUserDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>User Details</DialogTitle>
            <DialogDescription>
              View and manage user information
            </DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-400">Username</p>
                  <p className="font-medium">{selectedUser.username}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Email</p>
                  <p className="font-medium">{selectedUser.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Status</p>
                  <p className={getStatusColor(selectedUser.status)}>
                    {selectedUser.status}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Plan Tier</p>
                  <p className="font-medium">{selectedUser.plan_tier}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Memory Count</p>
                  <p className="font-medium">{selectedUser.memory_count || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Last Active</p>
                  <p className="font-medium">
                    {formatRelativeTime(selectedUser.last_active)}
                  </p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUserDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
