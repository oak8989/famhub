import React, { useState, useEffect } from 'react';
import { FileText, Plus, Trash2, Edit2 } from 'lucide-react';
import { notesAPI } from '../lib/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';

const noteColors = [
  { name: 'Sunny', value: '#F2CC8F' },
  { name: 'Sage', value: '#81B29A' },
  { name: 'Terracotta', value: '#E07A5F' },
  { name: 'Purple', value: '#DDA0DD' },
  { name: 'Blue', value: '#87CEEB' },
];

const NotesPage = () => {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [form, setForm] = useState({ title: '', content: '', color: '#F2CC8F' });

  useEffect(() => {
    loadNotes();
  }, []);

  const loadNotes = async () => {
    try {
      const response = await notesAPI.getNotes();
      setNotes(response.data);
    } catch (error) {
      toast.error('Failed to load notes');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) {
      toast.error('Please enter a note title');
      return;
    }

    try {
      if (editingNote) {
        await notesAPI.updateNote(editingNote.id, { ...form, id: editingNote.id });
        toast.success('Note updated!');
      } else {
        await notesAPI.createNote(form);
        toast.success('Note created!');
      }
      
      setDialogOpen(false);
      setEditingNote(null);
      setForm({ title: '', content: '', color: '#F2CC8F' });
      loadNotes();
    } catch (error) {
      toast.error('Failed to save note');
    }
  };

  const handleDelete = async (id) => {
    try {
      await notesAPI.deleteNote(id);
      loadNotes();
      toast.success('Note deleted');
    } catch (error) {
      toast.error('Failed to delete note');
    }
  };

  const openEditDialog = (note) => {
    setEditingNote(note);
    setForm({
      title: note.title,
      content: note.content,
      color: note.color || '#F2CC8F'
    });
    setDialogOpen(true);
  };

  return (
    <div className="space-y-6" data-testid="notes-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-navy flex items-center gap-3">
            <FileText className="w-8 h-8 text-purple-400" />
            Family Notes
          </h1>
          <p className="text-navy-light mt-1">{notes.length} notes</p>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button 
              className="btn-primary"
              onClick={() => {
                setEditingNote(null);
                setForm({ title: '', content: '', color: '#F2CC8F' });
              }}
              data-testid="add-note-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Note
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-warm-white border-sunny/50 max-w-lg">
            <DialogHeader>
              <DialogTitle className="font-heading text-navy">
                {editingNote ? 'Edit Note' : 'New Note'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-navy mb-2">Title</label>
                <Input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="Note title"
                  className="input-cozy"
                  data-testid="note-title-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-2">Content</label>
                <Textarea
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  placeholder="Write your note here..."
                  className="input-cozy min-h-[150px]"
                  data-testid="note-content-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-2">Color</label>
                <div className="flex gap-2">
                  {noteColors.map((color) => (
                    <button
                      key={color.value}
                      type="button"
                      onClick={() => setForm({ ...form, color: color.value })}
                      className={`w-8 h-8 rounded-full transition-all ${
                        form.color === color.value ? 'ring-2 ring-offset-2 ring-navy' : ''
                      }`}
                      style={{ backgroundColor: color.value }}
                      data-testid={`note-color-${color.name.toLowerCase()}`}
                    />
                  ))}
                </div>
              </div>
              <div className="flex gap-3">
                <Button type="submit" className="btn-primary flex-1" data-testid="save-note-btn">
                  {editingNote ? 'Update' : 'Create'} Note
                </Button>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="border-sunny">
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Notes grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="spinner" />
        </div>
      ) : notes.length === 0 ? (
        <div className="card-cozy text-center py-12">
          <FileText className="w-16 h-16 text-sunny mx-auto mb-4" />
          <h3 className="text-xl font-heading font-bold text-navy mb-2">No notes yet</h3>
          <p className="text-navy-light font-handwritten text-lg">Create a note to share with your family!</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {notes.map((note) => (
            <div
              key={note.id}
              className="rounded-2xl p-5 shadow-card hover:shadow-card-hover transition-all group relative"
              style={{ backgroundColor: note.color || '#F2CC8F' }}
              data-testid={`note-${note.id}`}
            >
              <div className="absolute top-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => openEditDialog(note)}
                  className="p-1.5 bg-white/50 hover:bg-white rounded-lg"
                  data-testid={`edit-note-${note.id}`}
                >
                  <Edit2 className="w-4 h-4 text-navy" />
                </button>
                <button
                  onClick={() => handleDelete(note.id)}
                  className="p-1.5 bg-white/50 hover:bg-white rounded-lg"
                  data-testid={`delete-note-${note.id}`}
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </button>
              </div>
              
              <h3 className="font-heading font-bold text-navy text-lg mb-2 pr-16">{note.title}</h3>
              <p className="text-navy/80 whitespace-pre-wrap line-clamp-6">{note.content}</p>
              
              {note.updated_at && (
                <p className="text-xs text-navy/50 mt-4 font-handwritten">
                  Last updated: {new Date(note.updated_at).toLocaleDateString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NotesPage;
