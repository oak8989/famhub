import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Package, Plus, Trash2, Edit2, Scan, X, AlertTriangle, Camera } from 'lucide-react';
import { pantryAPI } from '../lib/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { BrowserMultiFormatReader } from '@zxing/library';

const categories = ['Produce', 'Dairy', 'Meat', 'Frozen', 'Canned', 'Dry Goods', 'Beverages', 'Snacks', 'Condiments', 'Spices', 'Other'];
const units = ['pcs', 'lbs', 'oz', 'kg', 'g', 'L', 'ml', 'cups', 'bags', 'boxes', 'cans'];

const PantryPage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [scannerOpen, setScannerOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [filterCategory, setFilterCategory] = useState('all');
  const [form, setForm] = useState({
    name: '',
    barcode: '',
    quantity: 1,
    unit: 'pcs',
    category: 'Other',
    expiry_date: ''
  });

  const videoRef = useRef(null);
  const codeReaderRef = useRef(null);

  useEffect(() => {
    loadItems();
    return () => {
      if (codeReaderRef.current) {
        codeReaderRef.current.reset();
      }
    };
  }, []);

  const loadItems = async () => {
    try {
      const response = await pantryAPI.getItems();
      setItems(response.data);
    } catch (error) {
      toast.error('Failed to load pantry items');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) {
      toast.error('Please enter an item name');
      return;
    }

    try {
      if (editingItem) {
        await pantryAPI.updateItem(editingItem.id, { ...form, id: editingItem.id });
        toast.success('Item updated!');
      } else {
        await pantryAPI.createItem(form);
        toast.success('Item added!');
      }
      
      setDialogOpen(false);
      resetForm();
      loadItems();
    } catch (error) {
      toast.error('Failed to save item');
    }
  };

  const handleDelete = async (id) => {
    try {
      await pantryAPI.deleteItem(id);
      loadItems();
      toast.success('Item deleted');
    } catch (error) {
      toast.error('Failed to delete item');
    }
  };

  const resetForm = () => {
    setEditingItem(null);
    setForm({
      name: '',
      barcode: '',
      quantity: 1,
      unit: 'pcs',
      category: 'Other',
      expiry_date: ''
    });
  };

  const openEditDialog = (item) => {
    setEditingItem(item);
    setForm({
      name: item.name,
      barcode: item.barcode || '',
      quantity: item.quantity,
      unit: item.unit || 'pcs',
      category: item.category || 'Other',
      expiry_date: item.expiry_date || ''
    });
    setDialogOpen(true);
  };

  const startScanner = useCallback(async () => {
    setScannerOpen(true);
    
    try {
      const codeReader = new BrowserMultiFormatReader();
      codeReaderRef.current = codeReader;
      
      const videoInputDevices = await codeReader.listVideoInputDevices();
      
      if (videoInputDevices.length === 0) {
        toast.error('No camera found');
        setScannerOpen(false);
        return;
      }

      // Prefer back camera
      const selectedDevice = videoInputDevices.find(device => 
        device.label.toLowerCase().includes('back') || 
        device.label.toLowerCase().includes('rear')
      ) || videoInputDevices[0];

      await codeReader.decodeFromVideoDevice(
        selectedDevice.deviceId,
        videoRef.current,
        async (result, error) => {
          if (result) {
            const barcode = result.getText();
            toast.success(`Scanned: ${barcode}`);
            
            // Look up the barcode
            try {
              const response = await pantryAPI.lookupBarcode(barcode);
              setForm(prev => ({
                ...prev,
                name: response.data.name || `Product ${barcode}`,
                barcode: barcode,
                category: response.data.category || 'Other'
              }));
            } catch {
              setForm(prev => ({
                ...prev,
                barcode: barcode
              }));
            }
            
            stopScanner();
            setDialogOpen(true);
          }
        }
      );
    } catch (error) {
      console.error('Scanner error:', error);
      toast.error('Failed to start scanner. Please check camera permissions.');
      setScannerOpen(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stopScanner = useCallback(() => {
    if (codeReaderRef.current) {
      codeReaderRef.current.reset();
    }
    setScannerOpen(false);
  }, []);

  const filteredItems = filterCategory === 'all'
    ? items
    : items.filter(i => i.category === filterCategory);

  // Group items by category
  const groupedItems = filteredItems.reduce((acc, item) => {
    const cat = item.category || 'Other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {});

  // Check for expiring items (within 3 days)
  const isExpiringSoon = (date) => {
    if (!date) return false;
    const expiry = new Date(date);
    const today = new Date();
    const diffTime = expiry - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays <= 3 && diffDays >= 0;
  };

  const isExpired = (date) => {
    if (!date) return false;
    return new Date(date) < new Date();
  };

  return (
    <div className="space-y-6" data-testid="pantry-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-navy flex items-center gap-3">
            <Package className="w-8 h-8 text-amber-500" />
            Pantry Tracker
          </h1>
          <p className="text-navy-light mt-1">{items.length} items in your pantry</p>
        </div>
        
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={startScanner}
            className="border-amber-400 text-amber-600 hover:bg-amber-50"
            data-testid="scan-barcode-btn"
          >
            <Scan className="w-4 h-4 mr-2" />
            Scan Barcode
          </Button>
          
          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="btn-primary" data-testid="add-pantry-btn">
                <Plus className="w-4 h-4 mr-2" />
                Add Item
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-warm-white border-sunny/50">
              <DialogHeader>
                <DialogTitle className="font-heading text-navy">
                  {editingItem ? 'Edit Item' : 'Add Pantry Item'}
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-navy mb-2">Item Name</label>
                  <Input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="e.g., Milk, Bread, Eggs"
                    className="input-cozy"
                    data-testid="pantry-name-input"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-navy mb-2">Quantity</label>
                    <Input
                      type="number"
                      min="1"
                      value={form.quantity}
                      onChange={(e) => setForm({ ...form, quantity: parseInt(e.target.value) || 1 })}
                      className="input-cozy"
                      data-testid="pantry-quantity-input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-navy mb-2">Unit</label>
                    <Select value={form.unit} onValueChange={(v) => setForm({ ...form, unit: v })}>
                      <SelectTrigger className="input-cozy" data-testid="pantry-unit-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {units.map(unit => (
                          <SelectItem key={unit} value={unit}>{unit}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-navy mb-2">Category</label>
                  <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                    <SelectTrigger className="input-cozy" data-testid="pantry-category-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map(cat => (
                        <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-navy mb-2">Expiry Date (optional)</label>
                  <Input
                    type="date"
                    value={form.expiry_date}
                    onChange={(e) => setForm({ ...form, expiry_date: e.target.value })}
                    className="input-cozy"
                    data-testid="pantry-expiry-input"
                  />
                </div>
                
                {form.barcode && (
                  <div className="text-sm text-navy-light">
                    Barcode: {form.barcode}
                  </div>
                )}
                
                <div className="flex gap-3">
                  <Button type="submit" className="btn-primary flex-1" data-testid="save-pantry-btn">
                    {editingItem ? 'Update' : 'Add'} Item
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

      {/* Filter */}
      <div className="flex gap-3 overflow-x-auto pb-2">
        <Button
          variant={filterCategory === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilterCategory('all')}
          className={filterCategory === 'all' ? 'bg-amber-500 hover:bg-amber-600' : 'border-amber-300'}
          data-testid="filter-all"
        >
          All
        </Button>
        {categories.map(cat => (
          <Button
            key={cat}
            variant={filterCategory === cat ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterCategory(cat)}
            className={filterCategory === cat ? 'bg-amber-500 hover:bg-amber-600' : 'border-amber-300'}
            data-testid={`filter-${cat.toLowerCase().replace(' ', '-')}`}
          >
            {cat}
          </Button>
        ))}
      </div>

      {/* Items list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="spinner" />
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="card-cozy text-center py-12">
          <Package className="w-16 h-16 text-sunny mx-auto mb-4" />
          <h3 className="text-xl font-heading font-bold text-navy mb-2">Pantry is empty</h3>
          <p className="text-navy-light font-handwritten text-lg">Add items or scan barcodes!</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedItems).map(([category, categoryItems]) => (
            <div key={category} className="card-cozy">
              <h2 className="font-heading font-bold text-navy mb-4 flex items-center gap-2">
                <span className="w-3 h-3 bg-amber-400 rounded-full" />
                {category}
                <span className="text-sm font-normal text-navy-light">({categoryItems.length})</span>
              </h2>
              <div className="space-y-2">
                {categoryItems.map((item) => (
                  <div
                    key={item.id}
                    className={`flex items-center gap-4 p-3 rounded-xl bg-cream group ${
                      isExpired(item.expiry_date) ? 'ring-2 ring-red-400' :
                      isExpiringSoon(item.expiry_date) ? 'ring-2 ring-amber-400' : ''
                    }`}
                    data-testid={`pantry-item-${item.id}`}
                  >
                    <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center">
                      <Package className="w-5 h-5 text-amber-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-navy">{item.name}</h3>
                      <div className="flex flex-wrap gap-2 mt-1">
                        <span className="text-sm text-navy-light">
                          {item.quantity} {item.unit}
                        </span>
                        {item.expiry_date && (
                          <span className={`text-xs px-2 py-0.5 rounded-full flex items-center gap-1 ${
                            isExpired(item.expiry_date) ? 'bg-red-100 text-red-600' :
                            isExpiringSoon(item.expiry_date) ? 'bg-amber-100 text-amber-700' :
                            'bg-sage/20 text-sage'
                          }`}>
                            {isExpired(item.expiry_date) && <AlertTriangle className="w-3 h-3" />}
                            {isExpired(item.expiry_date) ? 'Expired' :
                             isExpiringSoon(item.expiry_date) ? 'Expiring soon' :
                             `Exp: ${item.expiry_date}`}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => openEditDialog(item)}
                        className="h-8 w-8 text-sage hover:bg-sage/10"
                        data-testid={`edit-pantry-${item.id}`}
                      >
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(item.id)}
                        className="h-8 w-8 text-red-500 hover:bg-red-50"
                        data-testid={`delete-pantry-${item.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Barcode Scanner Modal */}
      {scannerOpen && (
        <div className="scanner-overlay" data-testid="scanner-modal">
          <div className="w-full max-w-md p-4">
            <div className="bg-warm-white rounded-3xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-heading font-bold text-navy flex items-center gap-2">
                  <Camera className="w-5 h-5 text-amber-500" />
                  Scan Barcode
                </h2>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={stopScanner}
                  className="text-navy"
                  data-testid="close-scanner-btn"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>
              <div className="scanner-viewport bg-navy/10 rounded-2xl">
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover rounded-2xl"
                />
                <div className="scanner-line" />
              </div>
              <p className="text-center text-navy-light mt-4 text-sm">
                Point your camera at a barcode
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PantryPage;
