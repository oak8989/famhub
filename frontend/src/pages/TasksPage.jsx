import React, { useState, useEffect } from 'react';
import { CheckSquare, Plus, Trash2, Edit2, Calendar, User } from 'lucide-react';
import { tasksAPI, familyAPI } from '../lib/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Checkbox } from '../components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';

const TasksPage = () => {
  const [tasks, setTasks] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [filter, setFilter] = useState('all'); // all, pending, completed
  const [form, setForm] = useState({
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    priority: 'medium'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [tasksRes, membersRes] = await Promise.all([
        tasksAPI.getTasks(),
        familyAPI.getMembers().catch(() => ({ data: [] }))
      ]);
      setTasks(tasksRes.data);
      setMembers(membersRes.data);
    } catch (error) {
      toast.error('Failed to load tasks');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) {
      toast.error('Please enter a task title');
      return;
    }

    try {
      if (editingTask) {
        await tasksAPI.updateTask(editingTask.id, { ...form, id: editingTask.id, completed: editingTask.completed });
        toast.success('Task updated!');
      } else {
        await tasksAPI.createTask(form);
        toast.success('Task created!');
      }
      
      setDialogOpen(false);
      setEditingTask(null);
      setForm({ title: '', description: '', assigned_to: '', due_date: '', priority: 'medium' });
      loadData();
    } catch (error) {
      toast.error('Failed to save task');
    }
  };

  const handleToggle = async (task) => {
    try {
      await tasksAPI.updateTask(task.id, { ...task, completed: !task.completed });
      loadData();
    } catch (error) {
      toast.error('Failed to update task');
    }
  };

  const handleDelete = async (id) => {
    try {
      await tasksAPI.deleteTask(id);
      loadData();
      toast.success('Task deleted');
    } catch (error) {
      toast.error('Failed to delete task');
    }
  };

  const openEditDialog = (task) => {
    setEditingTask(task);
    setForm({
      title: task.title,
      description: task.description || '',
      assigned_to: task.assigned_to || '',
      due_date: task.due_date || '',
      priority: task.priority || 'medium'
    });
    setDialogOpen(true);
  };

  const filteredTasks = tasks.filter(t => {
    if (filter === 'pending') return !t.completed;
    if (filter === 'completed') return t.completed;
    return true;
  });

  const getMemberName = (id) => members.find(m => m.id === id)?.name || 'Unassigned';

  const priorityColors = {
    high: 'border-l-red-400 bg-red-50',
    medium: 'border-l-sunny bg-sunny/10',
    low: 'border-l-sage bg-sage/10'
  };

  return (
    <div className="space-y-6" data-testid="tasks-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-navy flex items-center gap-3">
            <CheckSquare className="w-8 h-8 text-sage" />
            Family Tasks
          </h1>
          <p className="text-navy-light mt-1">
            {tasks.filter(t => !t.completed).length} pending • {tasks.filter(t => t.completed).length} completed
          </p>
        </div>
        
        <div className="flex gap-3">
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-32 input-cozy" data-testid="task-filter">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
            </SelectContent>
          </Select>
          
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button 
                className="btn-primary"
                onClick={() => {
                  setEditingTask(null);
                  setForm({ title: '', description: '', assigned_to: '', due_date: '', priority: 'medium' });
                }}
                data-testid="add-task-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Task
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-warm-white border-sunny/50">
              <DialogHeader>
                <DialogTitle className="font-heading text-navy">
                  {editingTask ? 'Edit Task' : 'New Task'}
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-navy mb-2">Title</label>
                  <Input
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    placeholder="Task title"
                    className="input-cozy"
                    data-testid="task-title-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-navy mb-2">Description</label>
                  <Textarea
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    placeholder="Optional description"
                    className="input-cozy min-h-[80px]"
                    data-testid="task-description-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-navy mb-2">Assign To</label>
                    <Select value={form.assigned_to || "unassigned"} onValueChange={(v) => setForm({ ...form, assigned_to: v === "unassigned" ? "" : v })}>
                      <SelectTrigger className="input-cozy" data-testid="task-assignee-select">
                        <SelectValue placeholder="Select member" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="unassigned">Unassigned</SelectItem>
                        {members.map(m => (
                          <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-navy mb-2">Priority</label>
                    <Select value={form.priority} onValueChange={(v) => setForm({ ...form, priority: v })}>
                      <SelectTrigger className="input-cozy" data-testid="task-priority-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-navy mb-2">Due Date</label>
                  <Input
                    type="date"
                    value={form.due_date}
                    onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                    className="input-cozy"
                    data-testid="task-duedate-input"
                  />
                </div>
                <div className="flex gap-3">
                  <Button type="submit" className="btn-primary flex-1" data-testid="save-task-btn">
                    {editingTask ? 'Update' : 'Create'} Task
                  </Button>
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="border-sunny">
                    Cancel
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Tasks list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="spinner" />
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="card-cozy text-center py-12">
          <CheckSquare className="w-16 h-16 text-sunny mx-auto mb-4" />
          <h3 className="text-xl font-heading font-bold text-navy mb-2">No tasks</h3>
          <p className="text-navy-light font-handwritten text-lg">Create a task to get started!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredTasks.map((task) => (
            <div
              key={task.id}
              className={`card-cozy border-l-4 ${priorityColors[task.priority] || priorityColors.medium} group`}
              data-testid={`task-${task.id}`}
            >
              <div className="flex items-start gap-4">
                <Checkbox
                  checked={task.completed}
                  onCheckedChange={() => handleToggle(task)}
                  className="mt-1 border-sage data-[state=checked]:bg-sage"
                  data-testid={`task-checkbox-${task.id}`}
                />
                <div className="flex-1 min-w-0">
                  <h3 className={`font-medium ${task.completed ? 'line-through text-navy-light' : 'text-navy'}`}>
                    {task.title}
                  </h3>
                  {task.description && (
                    <p className="text-sm text-navy-light mt-1">{task.description}</p>
                  )}
                  <div className="flex flex-wrap gap-3 mt-2">
                    {task.assigned_to && (
                      <span className="text-xs text-navy-light flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {getMemberName(task.assigned_to)}
                      </span>
                    )}
                    {task.due_date && (
                      <span className="text-xs text-navy-light flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {task.due_date}
                      </span>
                    )}
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      task.priority === 'high' ? 'bg-red-100 text-red-600' :
                      task.priority === 'low' ? 'bg-sage/20 text-sage' :
                      'bg-sunny/30 text-amber-700'
                    }`}>
                      {task.priority}
                    </span>
                  </div>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => openEditDialog(task)}
                    className="p-2 hover:bg-sage/20 rounded-lg"
                    data-testid={`edit-task-${task.id}`}
                  >
                    <Edit2 className="w-4 h-4 text-sage" />
                  </button>
                  <button
                    onClick={() => handleDelete(task.id)}
                    className="p-2 hover:bg-red-100 rounded-lg"
                    data-testid={`delete-task-${task.id}`}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TasksPage;
