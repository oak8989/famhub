import React, { useState, useEffect } from 'react';
import { ShieldAlert, Plus, Trash2, Edit2, Upload, FileText, Phone, Car, Heart, X, Loader2, Download } from 'lucide-react';
import { nokBoxAPI } from '../lib/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';

const sections = [
  { key: 'emergency_contacts', label: 'Emergency Contacts', icon: Phone, color: 'text-red-500 bg-red-50' },
  { key: 'medical', label: 'Medical Info', icon: Heart, color: 'text-pink-500 bg-pink-50' },
  { key: 'vehicles', label: 'Vehicles', icon: Car, color: 'text-blue-500 bg-blue-50' },
  { key: 'documents', label: 'Important Documents', icon: FileText, color: 'text-amber-500 bg-amber-50' },
  { key: 'custom', label: 'Other Notes', icon: ShieldAlert, color: 'text-purple-500 bg-purple-50' },
];

const NOKBoxPage = () => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [activeSection, setActiveSection] = useState('all');
  const [uploading, setUploading] = useState(false);
  const [form, setForm] = useState({ section: 'emergency_contacts', title: '', content: '', file_url: '', file_name: '' });

  useEffect(() => { loadEntries(); }, []);

  const loadEntries = async () => {
    try {
      const res = await nokBoxAPI.getEntries();
      setEntries(res.data);
    } catch { toast.error('Failed to load entries'); }
    setLoading(false);
  };

  const resetForm = () => {
    setForm({ section: 'emergency_contacts', title: '', content: '', file_url: '', file_name: '' });
    setEditingEntry(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) { toast.error('Title is required'); return; }
    try {
      if (editingEntry) {
        await nokBoxAPI.updateEntry(editingEntry.id, form);
        toast.success('Entry updated');
      } else {
        await nokBoxAPI.createEntry(form);
        toast.success('Entry added');
      }
      setDialogOpen(false);
      resetForm();
      loadEntries();
    } catch { toast.error('Failed to save entry'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this entry?')) return;
    try {
      await nokBoxAPI.deleteEntry(id);
      toast.success('Entry deleted');
      loadEntries();
    } catch { toast.error('Failed to delete'); }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { toast.error('File too large (max 10MB)'); return; }
    setUploading(true);
    try {
      const res = await nokBoxAPI.uploadFile(file);
      setForm({ ...form, file_url: res.data.file_url, file_name: res.data.file_name });
      toast.success('File uploaded');
    } catch { toast.error('Upload failed'); }
    setUploading(false);
  };

  const openEdit = (entry) => {
    setEditingEntry(entry);
    setForm({ section: entry.section, title: entry.title, content: entry.content || '', file_url: entry.file_url || '', file_name: entry.file_name || '' });
    setDialogOpen(true);
  };

  const filtered = activeSection === 'all' ? entries : entries.filter(e => e.section === activeSection);
  const getSectionMeta = (key) => sections.find(s => s.key === key) || sections[4];

  return (
    <div className="space-y-6" data-testid="nok-box-page">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold text-navy flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-red-500" />
            </div>
            In Case of Emergency
          </h1>
          <p className="text-navy-light text-sm mt-1">Critical family information in one secure place</p>
        </div>
        <Button onClick={() => { resetForm(); setDialogOpen(true); }} className="btn-primary" data-testid="add-nok-entry-btn">
          <Plus className="w-4 h-4 mr-2" /> Add Entry
        </Button>
      </div>

      {/* Section Tabs */}
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant={activeSection === 'all' ? 'default' : 'outline'} onClick={() => setActiveSection('all')} className={activeSection === 'all' ? 'bg-navy text-white' : ''}>
          All ({entries.length})
        </Button>
        {sections.map(s => {
          const count = entries.filter(e => e.section === s.key).length;
          return (
            <Button key={s.key} size="sm" variant={activeSection === s.key ? 'default' : 'outline'}
              onClick={() => setActiveSection(s.key)}
              className={activeSection === s.key ? 'bg-navy text-white' : ''}>
              <s.icon className="w-3.5 h-3.5 mr-1.5" /> {s.label} ({count})
            </Button>
          );
        })}
      </div>

      {/* Entries Grid */}
      {loading ? (
        <div className="text-center py-12"><Loader2 className="w-8 h-8 animate-spin mx-auto text-navy-light" /></div>
      ) : filtered.length === 0 ? (
        <div className="card-cozy text-center py-12">
          <ShieldAlert className="w-12 h-12 mx-auto text-navy-light/30 mb-3" />
          <p className="text-navy-light">No entries yet. Add important info for your family.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(entry => {
            const meta = getSectionMeta(entry.section);
            return (
              <div key={entry.id} className="card-cozy" data-testid={`nok-entry-${entry.id}`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${meta.color}`}>
                      <meta.icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-navy text-sm">{entry.title}</h3>
                      <span className="text-xs text-navy-light">{meta.label}</span>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(entry)} data-testid={`nok-edit-${entry.id}`}>
                      <Edit2 className="w-3.5 h-3.5 text-navy-light" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleDelete(entry.id)} data-testid={`nok-delete-${entry.id}`}>
                      <Trash2 className="w-3.5 h-3.5 text-red-400" />
                    </Button>
                  </div>
                </div>
                {entry.content && (
                  <p className="text-sm text-navy-light whitespace-pre-wrap break-words">{entry.content}</p>
                )}
                {entry.file_url && (
                  <a href={entry.file_url} target="_blank" rel="noreferrer"
                    className="mt-2 inline-flex items-center gap-1.5 text-xs text-blue-600 hover:underline bg-blue-50 px-2.5 py-1 rounded-lg">
                    <Download className="w-3.5 h-3.5" /> {entry.file_name || 'Download file'}
                  </a>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!open) resetForm(); setDialogOpen(open); }}>
        <DialogContent className="max-w-lg" data-testid="nok-dialog">
          <DialogHeader>
            <DialogTitle>{editingEntry ? 'Edit Entry' : 'Add Entry'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-navy mb-1">Section</label>
              <Select value={form.section} onValueChange={(v) => setForm({ ...form, section: v })}>
                <SelectTrigger data-testid="nok-section-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {sections.map(s => <SelectItem key={s.key} value={s.key}>{s.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium text-navy mb-1">Title</label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Dr. Smith - Pediatrician" className="input-cozy" data-testid="nok-title-input" />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy mb-1">Details</label>
              <textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })}
                placeholder="Phone number, address, VIN, policy number, notes..."
                className="w-full min-h-[100px] rounded-xl border border-amber-200 p-3 text-sm focus:ring-2 focus:ring-terracotta/30 resize-y"
                data-testid="nok-content-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy mb-1">Attach File (optional, max 10MB)</label>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 px-4 py-2 bg-cream rounded-xl border border-amber-200 cursor-pointer hover:bg-amber-50 text-sm">
                  <Upload className="w-4 h-4 text-navy-light" />
                  {uploading ? 'Uploading...' : 'Choose File'}
                  <input type="file" className="hidden" onChange={handleFileUpload} disabled={uploading} data-testid="nok-file-input" />
                </label>
                {form.file_name && (
                  <div className="flex items-center gap-2 text-sm text-navy-light">
                    <FileText className="w-4 h-4" /> {form.file_name}
                    <button type="button" onClick={() => setForm({ ...form, file_url: '', file_name: '' })} className="text-red-400 hover:text-red-600">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <Button type="button" variant="outline" onClick={() => { resetForm(); setDialogOpen(false); }}>Cancel</Button>
              <Button type="submit" className="btn-primary" data-testid="nok-save-btn">{editingEntry ? 'Update' : 'Save'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default NOKBoxPage;
