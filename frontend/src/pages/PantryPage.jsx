import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Package, Plus, Trash2, Edit2, Scan, X, AlertTriangle, Camera, Loader2, ExternalLink, ListPlus, Check, Minus } from 'lucide-react';
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
  const [lookingUp, setLookingUp] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [filterCategory, setFilterCategory] = useState('all');
  const [form, setForm] = useState({
    name: '',
    barcode: '',
    quantity: '',
    unit: 'pcs',
    category: 'Other',
    expiry_date: ''
  });

  const videoRef = useRef(null);
  const codeReaderRef = useRef(null);
  const bulkVideoRef = useRef(null);
  const bulkCodeReaderRef = useRef(null);
  const recentScansRef = useRef(new Set());

  // Bulk scanning state
  const [bulkScanMode, setBulkScanMode] = useState(false);
  const [bulkItems, setBulkItems] = useState([]);
  const [bulkScannerActive, setBulkScannerActive] = useState(false);
  const [bulkLookingUp, setBulkLookingUp] = useState(false);
  const [savingBulk, setSavingBulk] = useState(false);

  useEffect(() => {
    loadItems();
    return () => {
      if (codeReaderRef.current) {
        codeReaderRef.current.reset();
      }
      if (bulkCodeReaderRef.current) {
        bulkCodeReaderRef.current.reset();
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
    const submitData = { ...form, quantity: form.quantity === '' ? 1 : form.quantity };
    try {
      if (editingItem) {
        await pantryAPI.updateItem(editingItem.id, { ...submitData, id: editingItem.id });
        toast.success('Item updated!');
      } else {
        await pantryAPI.createItem(submitData);
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
    setScanResult(null);
    setForm({
      name: '',
      barcode: '',
      quantity: '',
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

  const lookupBarcode = async (barcode) => {
    setLookingUp(true);
    setScanResult(null);
    try {
      const response = await pantryAPI.lookupBarcode(barcode);
      const data = response.data;
      if (data.found) {
        setScanResult(data);
        setForm(prev => ({
          ...prev,
          name: data.name || prev.name,
          barcode: barcode,
          category: mapCategory(data.category)
        }));
        toast.success(`Found: ${data.name}`);
      } else {
        setScanResult({ found: false, barcode });
        setForm(prev => ({ ...prev, barcode }));
        toast.info('Product not found in database. Enter details manually.');
      }
    } catch {
      setScanResult({ found: false, barcode });
      setForm(prev => ({ ...prev, barcode }));
      toast.info('Product not found. Enter details manually.');
    }
    setLookingUp(false);
  };

  const mapCategory = (rawCategory) => {
    if (!rawCategory) return 'Other';
    const lower = rawCategory.toLowerCase();
    for (const cat of categories) {
      if (lower.includes(cat.toLowerCase())) return cat;
    }
    if (lower.includes('drink') || lower.includes('juice') || lower.includes('water') || lower.includes('soda') || lower.includes('tea') || lower.includes('coffee') || lower.includes('beer') || lower.includes('wine')) return 'Beverages';
    if (lower.includes('milk') || lower.includes('cheese') || lower.includes('yogurt') || lower.includes('butter') || lower.includes('cream') || lower.includes('egg')) return 'Dairy';
    if (lower.includes('fruit') || lower.includes('vegetable') || lower.includes('salad') || lower.includes('herb') || lower.includes('fresh')) return 'Produce';
    if (lower.includes('chip') || lower.includes('cookie') || lower.includes('candy') || lower.includes('chocolate') || lower.includes('cracker') || lower.includes('bar') || lower.includes('nut')) return 'Snacks';
    if (lower.includes('sauce') || lower.includes('ketchup') || lower.includes('mustard') || lower.includes('dressing') || lower.includes('oil') || lower.includes('vinegar') || lower.includes('mayo')) return 'Condiments';
    if (lower.includes('spice') || lower.includes('seasoning') || lower.includes('pepper') || lower.includes('salt') || lower.includes('cumin') || lower.includes('paprika')) return 'Spices';
    if (lower.includes('chicken') || lower.includes('beef') || lower.includes('pork') || lower.includes('fish') || lower.includes('meat') || lower.includes('turkey') || lower.includes('sausage') || lower.includes('bacon')) return 'Meat';
    if (lower.includes('frozen') || lower.includes('ice')) return 'Frozen';
    if (lower.includes('can') || lower.includes('soup') || lower.includes('bean') || lower.includes('tomato') || lower.includes('tuna')) return 'Canned';
    if (lower.includes('pasta') || lower.includes('rice') || lower.includes('cereal') || lower.includes('flour') || lower.includes('bread') || lower.includes('grain') || lower.includes('oat') || lower.includes('noodle')) return 'Dry Goods';
    return 'Other';
  };

  const startScanner = useCallback(async () => {
    setScannerOpen(true);
    setScanResult(null);

    try {
      const codeReader = new BrowserMultiFormatReader();
      codeReaderRef.current = codeReader;
      const videoInputDevices = await codeReader.listVideoInputDevices();

      if (videoInputDevices.length === 0) {
        toast.error('No camera found');
        setScannerOpen(false);
        return;
      }

      const selectedDevice = videoInputDevices.find(device =>
        device.label.toLowerCase().includes('back') ||
        device.label.toLowerCase().includes('rear')
      ) || videoInputDevices[0];

      await codeReader.decodeFromVideoDevice(
        selectedDevice.deviceId,
        videoRef.current,
        async (result) => {
          if (result) {
            const barcode = result.getText();
            // Immediately stop camera
            stopScanner();
            // Immediately search for the product
            setDialogOpen(true);
            await lookupBarcode(barcode);
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

  // Bulk scanning functions
  const startBulkScan = useCallback(() => {
    setBulkScanMode(true);
    setBulkItems([]);
    recentScansRef.current = new Set();
    // Auto-start the scanner
    setTimeout(() => startBulkScanner(), 100);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startBulkScanner = useCallback(async () => {
    setBulkScannerActive(true);
    try {
      const codeReader = new BrowserMultiFormatReader();
      bulkCodeReaderRef.current = codeReader;
      const videoInputDevices = await codeReader.listVideoInputDevices();
      if (videoInputDevices.length === 0) {
        toast.error('No camera found');
        setBulkScannerActive(false);
        return;
      }
      const selectedDevice = videoInputDevices.find(device =>
        device.label.toLowerCase().includes('back') ||
        device.label.toLowerCase().includes('rear')
      ) || videoInputDevices[0];

      await codeReader.decodeFromVideoDevice(
        selectedDevice.deviceId,
        bulkVideoRef.current,
        async (result) => {
          if (result) {
            const barcode = result.getText();
            // Skip if we recently scanned this barcode
            if (recentScansRef.current.has(barcode)) return;
            recentScansRef.current.add(barcode);
            // Clear from recent after 5 seconds to allow re-scanning
            setTimeout(() => recentScansRef.current.delete(barcode), 5000);

            setBulkLookingUp(true);
            try {
              const response = await pantryAPI.lookupBarcode(barcode);
              const data = response.data;
              const newItem = {
                _tempId: Date.now() + '_' + barcode,
                name: data.found ? (data.name || 'Unknown Product') : '',
                barcode: barcode,
                quantity: 1,
                unit: 'pcs',
                category: data.found ? mapCategory(data.category) : 'Other',
                expiry_date: '',
                found: data.found,
                brand: data.found ? data.brand : '',
                image: data.found ? data.image : '',
              };
              setBulkItems(prev => [newItem, ...prev]);
              toast.success(data.found ? `Found: ${data.name}` : `Scanned: ${barcode}`);
            } catch {
              const newItem = {
                _tempId: Date.now() + '_' + barcode,
                name: '',
                barcode: barcode,
                quantity: 1,
                unit: 'pcs',
                category: 'Other',
                expiry_date: '',
                found: false,
              };
              setBulkItems(prev => [newItem, ...prev]);
              toast.info(`Scanned: ${barcode} — enter name manually`);
            }
            setBulkLookingUp(false);
          }
        }
      );
    } catch (error) {
      console.error('Bulk scanner error:', error);
      toast.error('Failed to start scanner. Check camera permissions.');
      setBulkScannerActive(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stopBulkScanner = useCallback(() => {
    if (bulkCodeReaderRef.current) {
      bulkCodeReaderRef.current.reset();
    }
    setBulkScannerActive(false);
  }, []);

  const closeBulkScan = useCallback(() => {
    stopBulkScanner();
    setBulkScanMode(false);
    setBulkItems([]);
    recentScansRef.current = new Set();
  }, [stopBulkScanner]);

  const updateBulkItem = (tempId, field, value) => {
    setBulkItems(prev => prev.map(item =>
      item._tempId === tempId ? { ...item, [field]: value } : item
    ));
  };

  const removeBulkItem = (tempId) => {
    setBulkItems(prev => prev.filter(item => item._tempId !== tempId));
  };

  const saveBulkItems = async () => {
    const validItems = bulkItems.filter(item => item.name.trim());
    if (validItems.length === 0) {
      toast.error('No items with names to save. Please enter names for scanned items.');
      return;
    }
    setSavingBulk(true);
    try {
      const itemsToSave = validItems.map(({ _tempId, found, brand, image, ...item }) => ({
        ...item,
        quantity: item.quantity || 1,
      }));
      const response = await pantryAPI.bulkAdd(itemsToSave);
      toast.success(`${response.data.count} items added to pantry!`);
      closeBulkScan();
      loadItems();
    } catch (error) {
      toast.error('Failed to save items');
    }
    setSavingBulk(false);
  };

  const filteredItems = filterCategory === 'all'
    ? items
    : items.filter(i => i.category === filterCategory);

  const groupedItems = filteredItems.reduce((acc, item) => {
    const cat = item.category || 'Other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {});

  const isExpiringSoon = (date) => {
    if (!date) return false;
    const expiry = new Date(date);
    const today = new Date();
    const diffDays = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));
    return diffDays <= 3 && diffDays >= 0;
  };

  const isExpired = (date) => {
    if (!date) return false;
    return new Date(date) < new Date();
  };

  return (
    <div className="space-y-6" data-testid="pantry-page">
      <div className="flex flex-col gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-heading font-bold text-navy flex items-center gap-3">
            <Package className="w-7 h-7 sm:w-8 sm:h-8 text-amber-500" />
            Pantry Tracker
          </h1>
          <p className="text-navy-light mt-1 text-sm sm:text-base">{items.length} items in your pantry</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="outline"
            onClick={startScanner}
            className="border-amber-400 text-amber-600 hover:bg-amber-50 w-full sm:w-auto"
            data-testid="scan-barcode-btn"
          >
            <Scan className="w-4 h-4 mr-2" />
            Scan Barcode
          </Button>

          <Button
            variant="outline"
            onClick={startBulkScan}
            className="border-teal-400 text-teal-600 hover:bg-teal-50 w-full sm:w-auto"
            data-testid="bulk-scan-btn"
          >
            <ListPlus className="w-4 h-4 mr-2" />
            Bulk Scan
          </Button>

          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="btn-primary w-full sm:w-auto" data-testid="add-pantry-btn">
                <Plus className="w-4 h-4 mr-2" />
                Add Item
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-warm-white border-sunny/50 max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="font-heading text-navy">
                  {editingItem ? 'Edit Item' : 'Add Pantry Item'}
                </DialogTitle>
              </DialogHeader>

              {/* Scan Result Card */}
              {lookingUp && (
                <div className="flex items-center gap-3 p-4 bg-amber-50 rounded-xl border border-amber-200" data-testid="barcode-searching">
                  <Loader2 className="w-5 h-5 text-amber-600 animate-spin" />
                  <span className="text-amber-800 font-medium">Searching for product...</span>
                </div>
              )}

              {scanResult && scanResult.found && (
                <div className="p-4 bg-green-50 rounded-xl border border-green-200" data-testid="barcode-found">
                  <div className="flex items-start gap-3">
                    {scanResult.image && (
                      <img src={scanResult.image} alt="" className="w-12 h-12 rounded-lg object-cover" />
                    )}
                    <div className="flex-1">
                      <p className="font-medium text-green-800">{scanResult.name}</p>
                      {scanResult.brand && <p className="text-sm text-green-600">{scanResult.brand}</p>}
                      <p className="text-xs text-green-500 mt-1">Found via {scanResult.source}</p>
                    </div>
                  </div>
                </div>
              )}

              {scanResult && !scanResult.found && (
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-200" data-testid="barcode-not-found">
                  <p className="text-amber-800 font-medium text-sm">Product not found for barcode: {scanResult.barcode}</p>
                  <p className="text-amber-600 text-xs mt-1">Enter the product details manually below.</p>
                  <a
                    href={`https://www.google.com/search?q=barcode+${scanResult.barcode}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-2"
                    data-testid="google-search-barcode"
                  >
                    <ExternalLink className="w-3 h-3" />
                    Search Google for this barcode
                  </a>
                </div>
              )}

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
                      min="0"
                      value={form.quantity}
                      onChange={(e) => setForm({ ...form, quantity: e.target.value === '' ? '' : parseInt(e.target.value) || 0 })}
                      placeholder="0"
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

                {/* Manual Barcode Entry */}
                <div>
                  <label className="block text-sm font-medium text-navy mb-2">Barcode (optional)</label>
                  <div className="flex gap-2">
                    <Input
                      value={form.barcode}
                      onChange={(e) => setForm({ ...form, barcode: e.target.value })}
                      placeholder="Enter barcode manually"
                      className="input-cozy flex-1"
                      data-testid="pantry-barcode-input"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      disabled={lookingUp || !form.barcode}
                      onClick={() => lookupBarcode(form.barcode)}
                      className="border-amber-300"
                      data-testid="lookup-barcode-btn"
                    >
                      {lookingUp ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Lookup'}
                    </Button>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
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
                        {item.barcode && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
                            {item.barcode}
                          </span>
                        )}
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
                Point your camera at a barcode — it will close automatically
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Scan Mode */}
      {bulkScanMode && (
        <div className="fixed inset-0 z-50 bg-warm-white flex flex-col" data-testid="bulk-scan-mode">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-amber-200 bg-amber-50">
            <h2 className="font-heading font-bold text-navy flex items-center gap-2">
              <ListPlus className="w-5 h-5 text-teal-500" />
              Bulk Scan
              {bulkItems.length > 0 && (
                <span className="text-sm font-normal bg-teal-100 text-teal-700 px-2 py-0.5 rounded-full">
                  {bulkItems.length} scanned
                </span>
              )}
            </h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={closeBulkScan}
              className="text-navy"
              data-testid="close-bulk-scan-btn"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* Scanner Area */}
          <div className="p-4">
            {bulkScannerActive ? (
              <div className="relative">
                <div className="scanner-viewport bg-navy/10 rounded-2xl max-h-48 overflow-hidden">
                  <video
                    ref={bulkVideoRef}
                    className="w-full h-full object-cover rounded-2xl"
                  />
                  <div className="scanner-line" />
                </div>
                {bulkLookingUp && (
                  <div className="absolute top-2 right-2 bg-white/90 rounded-lg px-3 py-1 flex items-center gap-2 shadow">
                    <Loader2 className="w-4 h-4 animate-spin text-amber-500" />
                    <span className="text-xs text-navy">Looking up...</span>
                  </div>
                )}
                <div className="flex gap-2 mt-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={stopBulkScanner}
                    className="flex-1 border-amber-400 text-amber-600"
                    data-testid="pause-bulk-scanner-btn"
                  >
                    <Camera className="w-4 h-4 mr-1" />
                    Pause Camera
                  </Button>
                </div>
              </div>
            ) : (
              <Button
                variant="outline"
                onClick={startBulkScanner}
                className="w-full border-amber-400 text-amber-600 hover:bg-amber-50"
                data-testid="resume-bulk-scanner-btn"
              >
                <Camera className="w-4 h-4 mr-2" />
                {bulkItems.length > 0 ? 'Resume Scanner' : 'Start Scanner'}
              </Button>
            )}
          </div>

          {/* Scanned Items List */}
          <div className="flex-1 overflow-y-auto px-4 pb-4">
            {bulkItems.length === 0 ? (
              <div className="text-center py-8 text-navy-light">
                <Scan className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Scan barcodes to add items here</p>
                <p className="text-xs mt-1 opacity-60">Items will appear as you scan them</p>
              </div>
            ) : (
              <div className="space-y-3">
                {bulkItems.map((item) => (
                  <div
                    key={item._tempId}
                    className={`p-3 rounded-xl border ${item.found ? 'border-green-200 bg-green-50/50' : 'border-amber-200 bg-amber-50/50'}`}
                    data-testid={`bulk-item-${item._tempId}`}
                  >
                    <div className="flex items-start gap-3">
                      {item.image && (
                        <img src={item.image} alt="" className="w-10 h-10 rounded-lg object-cover shrink-0" />
                      )}
                      <div className="flex-1 space-y-2">
                        <Input
                          value={item.name}
                          onChange={(e) => updateBulkItem(item._tempId, 'name', e.target.value)}
                          placeholder="Enter item name..."
                          className="input-cozy text-sm h-9"
                          data-testid={`bulk-item-name-${item._tempId}`}
                        />
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1">
                            <Button
                              variant="outline"
                              size="icon"
                              className="h-7 w-7 border-gray-300"
                              onClick={() => updateBulkItem(item._tempId, 'quantity', Math.max(1, (item.quantity || 1) - 1))}
                              data-testid={`bulk-item-minus-${item._tempId}`}
                            >
                              <Minus className="w-3 h-3" />
                            </Button>
                            <Input
                              type="number"
                              min="1"
                              value={item.quantity}
                              onChange={(e) => updateBulkItem(item._tempId, 'quantity', parseInt(e.target.value) || 1)}
                              className="input-cozy text-center text-sm h-7 w-14"
                              data-testid={`bulk-item-qty-${item._tempId}`}
                            />
                            <Button
                              variant="outline"
                              size="icon"
                              className="h-7 w-7 border-gray-300"
                              onClick={() => updateBulkItem(item._tempId, 'quantity', (item.quantity || 1) + 1)}
                              data-testid={`bulk-item-plus-${item._tempId}`}
                            >
                              <Plus className="w-3 h-3" />
                            </Button>
                          </div>
                          <Select value={item.category} onValueChange={(v) => updateBulkItem(item._tempId, 'category', v)}>
                            <SelectTrigger className="h-7 text-xs flex-1" data-testid={`bulk-item-cat-${item._tempId}`}>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {categories.map(cat => (
                                <SelectItem key={cat} value={cat} className="text-xs">{cat}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => removeBulkItem(item._tempId)}
                            className="h-7 w-7 text-red-500 hover:bg-red-50 shrink-0"
                            data-testid={`bulk-item-remove-${item._tempId}`}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-navy-light">
                          <span className="bg-gray-100 px-2 py-0.5 rounded">{item.barcode}</span>
                          {item.brand && <span>{item.brand}</span>}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Bottom Actions */}
          {bulkItems.length > 0 && (
            <div className="p-4 border-t border-amber-200 bg-amber-50/50">
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={closeBulkScan}
                  className="flex-1 border-gray-300"
                  data-testid="discard-bulk-btn"
                >
                  Discard All
                </Button>
                <Button
                  onClick={saveBulkItems}
                  disabled={savingBulk}
                  className="flex-1 bg-teal-500 hover:bg-teal-600 text-white"
                  data-testid="save-bulk-btn"
                >
                  {savingBulk ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Check className="w-4 h-4 mr-2" />
                  )}
                  Save {bulkItems.filter(i => i.name.trim()).length} Items
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PantryPage;
