import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Archive, Plus, Trash2, Edit2, Scan, X, Camera, Loader2, Search } from 'lucide-react';
import { inventoryAPI } from '../lib/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { BrowserMultiFormatReader } from '@zxing/library';

const categories = ['School Supplies', 'Seasonal Decorations', 'Electronics', 'Tools', 'Furniture', 'Cleaning Supplies', 'Outdoor', 'Sports', 'Clothing', 'Books', 'Toys', 'Kitchen', 'Other'];
const locations = ['Garage', 'Attic', 'Basement', 'Kitchen', 'Bedroom', 'Bathroom', 'Living Room', 'Office', 'Storage', 'Closet', 'Shed', 'Other'];
const conditions = ['New', 'Good', 'Fair', 'Worn', 'Needs Repair'];

const InventoryPage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [scannerOpen, setScannerOpen] = useState(false);
  const [lookingUp, setLookingUp] = useState(false);
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterLocation, setFilterLocation] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [form, setForm] = useState({
    name: '', barcode: '', category: 'Other', location: 'Storage',
    quantity: '', condition: 'Good', purchase_date: '', notes: '',
  });

  const videoRef = useRef(null);
  const codeReaderRef = useRef(null);

  useEffect(() => {
    loadItems();
    return () => { if (codeReaderRef.current) codeReaderRef.current.reset(); };
  }, []);

  const loadItems = async () => {
    try {
      const res = await inventoryAPI.getItems();
      setItems(res.data);
    } catch { toast.error('Failed to load inventory'); }
    setLoading(false);
  };

  const resetForm = () => {
    setForm({ name: '', barcode: '', category: 'Other', location: 'Storage', quantity: '', condition: 'Good', purchase_date: '', notes: '' });
    setEditingItem(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { toast.error('Item name is required'); return; }
    const submitData = { ...form, quantity: form.quantity === '' ? 1 : parseInt(form.quantity) || 1 };
    try {
      if (editingItem) {
        await inventoryAPI.updateItem(editingItem.id, submitData);
        toast.success('Item updated');
      } else {
        await inventoryAPI.createItem(submitData);
        toast.success('Item added');
      }
      setDialogOpen(false);
      resetForm();
      loadItems();
    } catch { toast.error('Failed to save item'); }
  };

  const handleDelete = async (id) => {
    try {
      await inventoryAPI.deleteItem(id);
      toast.success('Item deleted');
      loadItems();
    } catch { toast.error('Failed to delete'); }
  };

  const openEdit = (item) => {
    setEditingItem(item);
    setForm({
      name: item.name, barcode: item.barcode || '', category: item.category,
      location: item.location, quantity: item.quantity,
      condition: item.condition || 'Good', purchase_date: item.purchase_date || '', notes: item.notes || '',
    });
    setDialogOpen(true);
  };

  const startScanner = useCallback(async () => {
    setScannerOpen(true);
    try {
      const codeReader = new BrowserMultiFormatReader();
      codeReaderRef.current = codeReader;
      const devices = await codeReader.listVideoInputDevices();
      if (devices.length === 0) { toast.error('No camera found'); setScannerOpen(false); return; }
      const device = devices.find(d => d.label.toLowerCase().includes('back') || d.label.toLowerCase().includes('rear')) || devices[0];
      await codeReader.decodeFromVideoDevice(device.deviceId, videoRef.current, async (result) => {
        if (result) {
          const barcode = result.getText();
          codeReader.reset();
          setScannerOpen(false);
          setLookingUp(true);
          try {
            const res = await inventoryAPI.lookupBarcode(barcode);
            if (res.data.found) {
              setForm(f => ({ ...f, name: res.data.name || f.name, barcode, category: mapCategory(res.data.category) || f.category }));
              toast.success(`Found: ${res.data.name}`);
            } else {
              setForm(f => ({ ...f, barcode }));
              toast.info(`Barcode scanned: ${barcode}`);
            }
          } catch { setForm(f => ({ ...f, barcode })); }
          setLookingUp(false);
          setDialogOpen(true);
        }
      });
    } catch (err) {
      toast.error('Scanner failed. Check camera permissions.');
      setScannerOpen(false);
    }
  }, []);

  const stopScanner = useCallback(() => {
    if (codeReaderRef.current) codeReaderRef.current.reset();
    setScannerOpen(false);
  }, []);

  const mapCategory = (cat) => {
    if (!cat) return 'Other';
    const lower = cat.toLowerCase();
    if (lower.includes('electron')) return 'Electronics';
    if (lower.includes('tool')) return 'Tools';
    if (lower.includes('book')) return 'Books';
    if (lower.includes('toy')) return 'Toys';
    if (lower.includes('kitchen')) return 'Kitchen';
    if (lower.includes('clean')) return 'Cleaning Supplies';
    if (lower.includes('sport')) return 'Sports';
    if (lower.includes('cloth')) return 'Clothing';
    return 'Other';
  };

  const filtered = items.filter(item => {
    if (filterCategory !== 'all' && item.category !== filterCategory) return false;
    if (filterLocation !== 'all' && item.location !== filterLocation) return false;
    if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase()) && !(item.barcode || '').includes(searchQuery)) return false;
    return true;
  });

  const conditionColor = (c) => {
    switch (c) {
      case 'New': return 'bg-green-100 text-green-700';
      case 'Good': return 'bg-blue-100 text-blue-700';
      case 'Fair': return 'bg-amber-100 text-amber-700';
      case 'Worn': return 'bg-orange-100 text-orange-700';
      case 'Needs Repair': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-6" data-testid="inventory-page">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold text-navy flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
              <Archive className="w-5 h-5 text-indigo-500" />
            </div>
            Household Inventory
          </h1>
          <p className="text-navy-light text-sm mt-1">Track everything in your home</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="outline" onClick={startScanner} className="border-amber-400 text-amber-600 hover:bg-amber-50" data-testid="inv-scan-btn">
            <Scan className="w-4 h-4 mr-2" /> Scan Barcode
          </Button>
          <Button onClick={() => { resetForm(); setDialogOpen(true); }} className="btn-primary" data-testid="add-inv-item-btn">
            <Plus className="w-4 h-4 mr-2" /> Add Item
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="card-cozy flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-light" />
          <Input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search items..." className="input-cozy pl-10" data-testid="inv-search" />
        </div>
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-full sm:w-44" data-testid="inv-filter-category"><SelectValue placeholder="Category" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={filterLocation} onValueChange={setFilterLocation}>
          <SelectTrigger className="w-full sm:w-44" data-testid="inv-filter-location"><SelectValue placeholder="Location" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Locations</SelectItem>
            {locations.map(l => <SelectItem key={l} value={l}>{l}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {/* Items List */}
      {loading ? (
        <div className="text-center py-12"><Loader2 className="w-8 h-8 animate-spin mx-auto text-navy-light" /></div>
      ) : filtered.length === 0 ? (
        <div className="card-cozy text-center py-12">
          <Archive className="w-12 h-12 mx-auto text-navy-light/30 mb-3" />
          <p className="text-navy-light">{items.length === 0 ? 'No items yet. Start adding your household inventory.' : 'No items match your filters.'}</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(item => (
            <div key={item.id} className="card-cozy" data-testid={`inv-item-${item.id}`}>
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-navy text-sm truncate">{item.name}</h3>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">{item.category}</span>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{item.location}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${conditionColor(item.condition)}`}>{item.condition}</span>
                  </div>
                </div>
                <div className="flex gap-1 shrink-0 ml-2">
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(item)} data-testid={`inv-edit-${item.id}`}>
                    <Edit2 className="w-3.5 h-3.5 text-navy-light" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleDelete(item.id)} data-testid={`inv-delete-${item.id}`}>
                    <Trash2 className="w-3.5 h-3.5 text-red-400" />
                  </Button>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-navy-light mt-2 pt-2 border-t border-amber-100">
                <span>Qty: <strong className="text-navy">{item.quantity}</strong></span>
                {item.barcode && <span className="bg-gray-100 px-1.5 py-0.5 rounded font-mono">{item.barcode}</span>}
                {item.purchase_date && <span>{item.purchase_date}</span>}
              </div>
              {item.notes && <p className="text-xs text-navy-light mt-1.5 truncate">{item.notes}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Scanner Modal */}
      {scannerOpen && (
        <div className="scanner-overlay" data-testid="inv-scanner-modal">
          <div className="w-full max-w-md p-4">
            <div className="bg-warm-white rounded-3xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-heading font-bold text-navy flex items-center gap-2">
                  <Camera className="w-5 h-5 text-amber-500" /> Scan Barcode
                </h2>
                <Button variant="ghost" size="icon" onClick={stopScanner} className="text-navy" data-testid="inv-close-scanner"><X className="w-5 h-5" /></Button>
              </div>
              <div className="scanner-viewport bg-navy/10 rounded-2xl">
                <video ref={videoRef} className="w-full h-full object-cover rounded-2xl" />
                <div className="scanner-line" />
              </div>
              <p className="text-center text-navy-light mt-4 text-sm">Point camera at a barcode</p>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!open) resetForm(); setDialogOpen(open); }}>
        <DialogContent className="max-w-lg" data-testid="inv-dialog">
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit Item' : 'Add Item'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-navy mb-1">Name</label>
                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Item name" className="input-cozy" data-testid="inv-name-input" />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-1">Category</label>
                <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                  <SelectTrigger data-testid="inv-category-select"><SelectValue /></SelectTrigger>
                  <SelectContent>{categories.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-1">Location</label>
                <Select value={form.location} onValueChange={(v) => setForm({ ...form, location: v })}>
                  <SelectTrigger data-testid="inv-location-select"><SelectValue /></SelectTrigger>
                  <SelectContent>{locations.map(l => <SelectItem key={l} value={l}>{l}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-1">Quantity</label>
                <Input type="number" min="0" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value === '' ? '' : parseInt(e.target.value) || 0 })} placeholder="0" className="input-cozy" data-testid="inv-quantity-input" />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-1">Condition</label>
                <Select value={form.condition} onValueChange={(v) => setForm({ ...form, condition: v })}>
                  <SelectTrigger data-testid="inv-condition-select"><SelectValue /></SelectTrigger>
                  <SelectContent>{conditions.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-1">Barcode</label>
                <Input value={form.barcode} onChange={(e) => setForm({ ...form, barcode: e.target.value })} placeholder="Optional" className="input-cozy" data-testid="inv-barcode-input" />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-1">Purchase Date</label>
                <Input type="date" value={form.purchase_date} onChange={(e) => setForm({ ...form, purchase_date: e.target.value })} className="input-cozy" data-testid="inv-date-input" />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-navy mb-1">Notes</label>
                <Input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Optional notes" className="input-cozy" data-testid="inv-notes-input" />
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <Button type="button" variant="outline" onClick={() => { resetForm(); setDialogOpen(false); }}>Cancel</Button>
              <Button type="submit" className="btn-primary" data-testid="inv-save-btn">{editingItem ? 'Update' : 'Save'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default InventoryPage;
