import React, { useState, useEffect } from 'react';
import { ShoppingCart, Plus, Trash2, Check, X } from 'lucide-react';
import { shoppingAPI } from '../lib/api';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Checkbox } from '../components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

const categories = ['General', 'Produce', 'Dairy', 'Meat', 'Bakery', 'Frozen', 'Beverages', 'Snacks', 'Cleaning', 'Personal Care'];

const ShoppingPage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newItem, setNewItem] = useState({ name: '', quantity: '1', category: 'General' });

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    try {
      const response = await shoppingAPI.getItems();
      setItems(response.data);
    } catch (error) {
      toast.error('Failed to load shopping list');
    }
    setLoading(false);
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newItem.name.trim()) return;

    try {
      await shoppingAPI.createItem(newItem);
      setNewItem({ name: '', quantity: '1', category: 'General' });
      loadItems();
      toast.success('Item added!');
    } catch (error) {
      toast.error('Failed to add item');
    }
  };

  const handleToggle = async (item) => {
    try {
      await shoppingAPI.updateItem(item.id, { ...item, checked: !item.checked });
      loadItems();
    } catch (error) {
      toast.error('Failed to update item');
    }
  };

  const handleDelete = async (id) => {
    try {
      await shoppingAPI.deleteItem(id);
      loadItems();
      toast.success('Item removed');
    } catch (error) {
      toast.error('Failed to delete item');
    }
  };

  const handleClearChecked = async () => {
    try {
      await shoppingAPI.clearChecked();
      loadItems();
      toast.success('Checked items cleared');
    } catch (error) {
      toast.error('Failed to clear items');
    }
  };

  const groupedItems = items.reduce((acc, item) => {
    const cat = item.category || 'General';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(item);
    return acc;
  }, {});

  const uncheckedCount = items.filter(i => !i.checked).length;
  const checkedCount = items.filter(i => i.checked).length;

  return (
    <div className="space-y-6" data-testid="shopping-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-navy flex items-center gap-3">
            <ShoppingCart className="w-8 h-8 text-sage" />
            Shopping List
          </h1>
          <p className="text-navy-light mt-1">
            {uncheckedCount} items to buy • {checkedCount} checked
          </p>
        </div>
        
        {checkedCount > 0 && (
          <Button
            variant="outline"
            onClick={handleClearChecked}
            className="border-sage text-sage hover:bg-sage/10"
            data-testid="clear-checked-btn"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Clear Checked
          </Button>
        )}
      </div>

      {/* Add item form */}
      <form onSubmit={handleAdd} className="card-cozy">
        <div className="flex flex-col sm:flex-row gap-3">
          <Input
            value={newItem.name}
            onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
            placeholder="Add an item..."
            className="input-cozy flex-1"
            data-testid="shopping-item-input"
          />
          <Input
            value={newItem.quantity}
            onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
            placeholder="Qty"
            className="input-cozy w-20"
            data-testid="shopping-quantity-input"
          />
          <Select value={newItem.category} onValueChange={(v) => setNewItem({ ...newItem, category: v })}>
            <SelectTrigger className="w-40 input-cozy" data-testid="shopping-category-select">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              {categories.map(cat => (
                <SelectItem key={cat} value={cat}>{cat}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button type="submit" className="btn-primary" data-testid="add-shopping-btn">
            <Plus className="w-4 h-4 mr-2" />
            Add
          </Button>
        </div>
      </form>

      {/* Items list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="spinner" />
        </div>
      ) : items.length === 0 ? (
        <div className="card-cozy text-center py-12">
          <ShoppingCart className="w-16 h-16 text-sunny mx-auto mb-4" />
          <h3 className="text-xl font-heading font-bold text-navy mb-2">List is empty</h3>
          <p className="text-navy-light font-handwritten text-lg">Add items to your shopping list above!</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedItems).map(([category, categoryItems]) => (
            <div key={category} className="card-cozy">
              <h2 className="font-heading font-bold text-navy mb-4 flex items-center gap-2">
                <span className="w-3 h-3 bg-sage rounded-full" />
                {category}
                <span className="text-sm font-normal text-navy-light">
                  ({categoryItems.filter(i => !i.checked).length})
                </span>
              </h2>
              <div className="space-y-2">
                {categoryItems.map((item) => (
                  <div
                    key={item.id}
                    className={`flex items-center gap-3 p-3 rounded-xl transition-all ${
                      item.checked ? 'bg-sage/10' : 'bg-cream hover:bg-sunny/20'
                    }`}
                    data-testid={`shopping-item-${item.id}`}
                  >
                    <Checkbox
                      checked={item.checked}
                      onCheckedChange={() => handleToggle(item)}
                      className="border-sage data-[state=checked]:bg-sage"
                      data-testid={`checkbox-${item.id}`}
                    />
                    <span className={`flex-1 ${item.checked ? 'line-through text-navy-light' : 'text-navy'}`}>
                      {item.name}
                    </span>
                    {item.quantity !== '1' && (
                      <span className="text-sm text-navy-light bg-sunny/30 px-2 py-1 rounded-lg">
                        {item.quantity}
                      </span>
                    )}
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="p-1 hover:bg-red-100 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      data-testid={`delete-shopping-${item.id}`}
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ShoppingPage;
