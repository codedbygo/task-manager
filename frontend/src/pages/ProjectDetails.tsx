import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { AxiosError } from 'axios';
import api from '../api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '../contexts/AuthContext';

interface User { id: number; name: string; email: string; }
interface ProjectMember { user: User; role: string; }
interface Project { id: number; name: string; description: string; creator_id: number; members: ProjectMember[]; }
interface Task { id: number; title: string; description: string; status: string; priority: string; due_date?: string; assignees: User[]; }

export default function ProjectDetails() {
  const { id } = useParams();
  const { user } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  
  const [isTaskOpen, setIsTaskOpen] = useState(false);
  const [newTask, setNewTask] = useState({ title: '', description: '', due_date: '', priority: 'MEDIUM', assignees: [] as number[] });

  const [isMemberOpen, setIsMemberOpen] = useState(false);
  const [newMemberId, setNewMemberId] = useState<string>('');

  const fetchProject = useCallback(async () => {
    const res = await api.get(`/projects/${id}`);
    setProject(res.data);
  }, [id]);

  const fetchTasks = useCallback(async () => {
    const res = await api.get(`/projects/${id}/tasks`);
    setTasks(res.data);
  }, [id]);

  const fetchUsers = useCallback(async () => {
    const res = await api.get('/users');
    setUsers(res.data);
  }, []);

  useEffect(() => {
    void fetchProject();
    void fetchTasks();
    void fetchUsers();
  }, [fetchProject, fetchTasks, fetchUsers]);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      ...newTask,
      due_date: newTask.due_date ? new Date(newTask.due_date).toISOString() : null,
    };
    await api.post(`/projects/${id}/tasks`, payload);
    setIsTaskOpen(false);
    setNewTask({ title: '', description: '', due_date: '', priority: 'MEDIUM', assignees: [] });
    void fetchTasks();
  };

  const handleUpdateTaskStatus = async (taskId: number, status: string) => {
    try {
      await api.put(`/tasks/${taskId}`, { status });
      void fetchTasks();
    } catch (err: unknown) {
      const apiError = err as AxiosError<{ detail?: string }>;
      alert(apiError.response?.data?.detail || "Failed to update status");
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post(`/projects/${id}/members`, { user_id: parseInt(newMemberId), role: 'MEMBER' });
      setIsMemberOpen(false);
      setNewMemberId('');
      void fetchProject();
    } catch (err: unknown) {
      const apiError = err as AxiosError<{ detail?: string }>;
      alert(apiError.response?.data?.detail || "Failed to add member");
    }
  };

  const handleRemoveMember = async (memberUserId: number) => {
    try {
      await api.delete(`/projects/${id}/members/${memberUserId}`);
      void fetchProject();
      void fetchTasks();
    } catch (err: unknown) {
      const apiError = err as AxiosError<{ detail?: string }>;
      alert(apiError.response?.data?.detail || "Failed to remove member");
    }
  };

  if (!project) return <div>Loading...</div>;

  const isAdmin = project.members.some(m => m.user.id === user?.id && m.role === 'ADMIN');

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{project.name}</h2>
          <p className="text-muted-foreground">{project.description}</p>
        </div>
        <div className="flex space-x-2">
          {isAdmin && (
            <Dialog open={isMemberOpen} onOpenChange={setIsMemberOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">Add Member</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Add Team Member</DialogTitle></DialogHeader>
                <form onSubmit={handleAddMember} className="space-y-4">
                  <div className="space-y-2">
                    <Label>User</Label>
                    <Select onValueChange={setNewMemberId}>
                      <SelectTrigger><SelectValue placeholder="Select a user" /></SelectTrigger>
                      <SelectContent>
                        {users.filter(u => !project.members.some(m => m.user.id === u.id)).map(u => (
                          <SelectItem key={u.id} value={u.id.toString()}>{u.name} ({u.email})</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button type="submit" className="w-full">Add</Button>
                </form>
              </DialogContent>
            </Dialog>
          )}
          
          {isAdmin && (
            <Dialog open={isTaskOpen} onOpenChange={setIsTaskOpen}>
              <DialogTrigger asChild>
                <Button>Create Task</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>Create New Task</DialogTitle></DialogHeader>
                <form onSubmit={handleCreateTask} className="space-y-4">
                  <div className="space-y-2">
                    <Label>Title</Label>
                    <Input value={newTask.title} onChange={e => setNewTask({...newTask, title: e.target.value})} required />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Input value={newTask.description} onChange={e => setNewTask({...newTask, description: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Due Date</Label>
                    <Input
                      type="datetime-local"
                      value={newTask.due_date}
                      onChange={e => setNewTask({ ...newTask, due_date: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Assignee</Label>
                    <Select onValueChange={(val) => setNewTask({...newTask, assignees: [parseInt(val)]})}>
                      <SelectTrigger><SelectValue placeholder="Select Assignee" /></SelectTrigger>
                      <SelectContent>
                        {project.members.map(m => (
                          <SelectItem key={m.user.id} value={m.user.id.toString()}>{m.user.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button type="submit" className="w-full">Create</Button>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-4">
          <h3 className="text-xl font-semibold">Tasks</h3>
          <div className="grid gap-4">
            {tasks.map(task => (
              <Card key={task.id} className="glass-panel">
                <CardContent className="p-4 flex justify-between items-center">
                  <div>
                    <h4 className="font-semibold">{task.title}</h4>
                    <p className="text-sm text-muted-foreground">{task.description}</p>
                    <div className="flex gap-2 mt-2">
                      <Badge variant={task.priority === 'HIGH' ? 'destructive' : 'secondary'}>{task.priority}</Badge>
                      {task.due_date && <Badge variant="outline">{new Date(task.due_date).toLocaleString()}</Badge>}
                      {task.assignees.map(a => (
                        <Badge key={a.id} variant="outline">{a.name}</Badge>
                      ))}
                    </div>
                  </div>
                  <Select value={task.status} onValueChange={(val) => handleUpdateTaskStatus(task.id, val)}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="TODO">To Do</SelectItem>
                      <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                      <SelectItem value="DONE">Done</SelectItem>
                    </SelectContent>
                  </Select>
                </CardContent>
              </Card>
            ))}
            {tasks.length === 0 && <p className="text-muted-foreground text-sm">No tasks yet.</p>}
          </div>
        </div>
        
        <div>
          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Team Members</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-4">
                {project.members.map(member => (
                  <li key={member.user.id} className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{member.user.name}</p>
                      <p className="text-xs text-muted-foreground">{member.user.email}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={member.role === 'ADMIN' ? 'default' : 'secondary'}>{member.role}</Badge>
                      {isAdmin && member.user.id !== user?.id && (
                        <Button variant="outline" size="sm" onClick={() => handleRemoveMember(member.user.id)}>
                          Remove
                        </Button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
