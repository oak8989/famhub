import React, { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, Plus, X, Clock, Edit2, Trash2, RefreshCw, Link2, Unlink } from 'lucide-react';
import { calendarAPI } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Calendar } from '../components/ui/calendar';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { format, isSameDay, parseISO } from 'date-fns';

const eventColors = [
  { name: 'Terracotta', value: '#E07A5F' },
  { name: 'Sage', value: '#81B29A' },
  { name: 'Sunny', value: '#F2CC8F' },
  { name: 'Purple', value: '#9B5DE5' },
  { name: 'Blue', value: '#00BBF9' },
];

const CalendarPage = () => {
  const { user, refreshUser } = useAuth();
  const [events, setEvents] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [form, setForm] = useState({ title: '', description: '', time: '', color: '#E07A5F' });
  const [syncing, setSyncing] = useState(false);

  const isGoogleConnected = !!user?.google_tokens;

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const response = await calendarAPI.getEvents();
      setEvents(response.data);
    } catch (error) {
      toast.error('Failed to load events');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) {
      toast.error('Please enter an event title');
      return;
    }

    try {
      const eventData = {
        ...form,
        date: format(selectedDate, 'yyyy-MM-dd'),
      };

      if (editingEvent) {
        await calendarAPI.updateEvent(editingEvent.id, { ...eventData, id: editingEvent.id });
        toast.success('Event updated!');
      } else {
        await calendarAPI.createEvent(eventData);
        toast.success('Event created!');
      }
      
      setDialogOpen(false);
      setEditingEvent(null);
      setForm({ title: '', description: '', time: '', color: '#E07A5F' });
      loadEvents();
    } catch (error) {
      toast.error('Failed to save event');
    }
  };

  const handleDelete = async (id) => {
    try {
      await calendarAPI.deleteEvent(id);
      toast.success('Event deleted');
      loadEvents();
    } catch (error) {
      toast.error('Failed to delete event');
    }
  };

  const openEditDialog = (event) => {
    setEditingEvent(event);
    setForm({
      title: event.title,
      description: event.description || '',
      time: event.time || '',
      color: event.color || '#E07A5F',
    });
    setSelectedDate(parseISO(event.date));
    setDialogOpen(true);
  };

  const handleConnectGoogle = async () => {
    try {
      const res = await calendarAPI.googleAuth();
      window.location.href = res.data.auth_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Google Calendar not configured. Ask the hub owner to set it up in Server settings.');
    }
  };

  const handleSyncGoogle = async () => {
    setSyncing(true);
    try {
      const res = await calendarAPI.googleSync();
      toast.success(res.data.message || 'Calendar synced!');
      loadEvents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Sync failed');
    }
    setSyncing(false);
  };

  const handleDisconnectGoogle = async () => {
    try {
      await calendarAPI.googleDisconnect();
      toast.success('Google Calendar disconnected');
      await refreshUser();
    } catch (error) {
      toast.error('Failed to disconnect');
    }
  };

  const eventsForSelectedDate = events.filter(e => 
    isSameDay(parseISO(e.date), selectedDate)
  );

  const datesWithEvents = events.map(e => parseISO(e.date));

  return (
    <div className="space-y-6" data-testid="calendar-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold text-navy flex items-center gap-3">
            <CalendarIcon className="w-8 h-8 text-terracotta" />
            Family Calendar
          </h1>
          <p className="text-navy-light mt-1">Keep track of everyone's events</p>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button 
              className="btn-primary"
              onClick={() => {
                setEditingEvent(null);
                setForm({ title: '', description: '', time: '', color: '#E07A5F' });
              }}
              data-testid="add-event-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Event
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-warm-white border-sunny/50">
            <DialogHeader>
              <DialogTitle className="font-heading text-navy">
                {editingEvent ? 'Edit Event' : 'New Event'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-navy mb-2">Title</label>
                <Input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="Event title"
                  className="input-cozy"
                  data-testid="event-title-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-2">Description</label>
                <Input
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Optional description"
                  className="input-cozy"
                  data-testid="event-description-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-2">Time</label>
                <Input
                  type="time"
                  value={form.time}
                  onChange={(e) => setForm({ ...form, time: e.target.value })}
                  className="input-cozy"
                  data-testid="event-time-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-2">Color</label>
                <div className="flex gap-2">
                  {eventColors.map((color) => (
                    <button
                      key={color.value}
                      type="button"
                      onClick={() => setForm({ ...form, color: color.value })}
                      className={`w-8 h-8 rounded-full transition-all ${
                        form.color === color.value ? 'ring-2 ring-offset-2 ring-navy' : ''
                      }`}
                      style={{ backgroundColor: color.value }}
                      data-testid={`color-${color.name.toLowerCase()}`}
                    />
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-navy mb-2">
                  Date: {format(selectedDate, 'MMMM d, yyyy')}
                </label>
              </div>
              <div className="flex gap-3">
                <Button type="submit" className="btn-primary flex-1" data-testid="save-event-btn">
                  {editingEvent ? 'Update' : 'Create'} Event
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
                  className="border-sunny"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Google Calendar Connection */}
      <div className="card-cozy flex flex-col sm:flex-row sm:items-center justify-between gap-3" data-testid="google-calendar-section">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isGoogleConnected ? 'bg-green-100' : 'bg-gray-100'}`}>
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
          </div>
          <div>
            <p className="font-medium text-navy text-sm">Google Calendar</p>
            <p className="text-xs text-navy-light">
              {isGoogleConnected ? 'Connected — sync your events' : 'Connect to import & sync events'}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {isGoogleConnected ? (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSyncGoogle}
                disabled={syncing}
                className="border-sage text-sage hover:bg-sage/10"
                data-testid="sync-google-btn"
              >
                <RefreshCw className={`w-4 h-4 mr-1.5 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Sync Now'}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDisconnectGoogle}
                className="text-red-500 hover:bg-red-50"
                data-testid="disconnect-google-btn"
              >
                <Unlink className="w-4 h-4 mr-1.5" />
                Disconnect
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={handleConnectGoogle}
              className="border-blue-400 text-blue-600 hover:bg-blue-50"
              data-testid="connect-google-btn"
            >
              <Link2 className="w-4 h-4 mr-1.5" />
              Connect Google
            </Button>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <div className="lg:col-span-2 card-cozy">
          <Calendar
            mode="single"
            selected={selectedDate}
            onSelect={(date) => date && setSelectedDate(date)}
            className="w-full"
            modifiers={{ hasEvent: datesWithEvents }}
            modifiersStyles={{
              hasEvent: { fontWeight: 'bold', textDecoration: 'underline', textDecorationColor: '#E07A5F' }
            }}
          />
        </div>

        {/* Events for selected date */}
        <div className="card-cozy">
          <h2 className="font-heading font-bold text-navy mb-4">
            {format(selectedDate, 'MMMM d, yyyy')}
          </h2>
          
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="spinner" />
            </div>
          ) : eventsForSelectedDate.length === 0 ? (
            <div className="text-center py-8">
              <CalendarIcon className="w-12 h-12 text-sunny mx-auto mb-3" />
              <p className="text-navy-light font-handwritten text-lg">No events this day</p>
              <Button
                variant="ghost"
                onClick={() => setDialogOpen(true)}
                className="mt-2 text-terracotta"
                data-testid="add-event-empty"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add one
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {eventsForSelectedDate.map((event) => (
                <div
                  key={event.id}
                  className="p-4 rounded-xl bg-cream border-l-4 group"
                  style={{ borderLeftColor: event.color || '#E07A5F' }}
                  data-testid={`event-${event.id}`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-medium text-navy">{event.title}</h3>
                      {event.time && (
                        <p className="text-sm text-navy-light flex items-center gap-1 mt-1">
                          <Clock className="w-3 h-3" />
                          {event.time}
                        </p>
                      )}
                      {event.description && (
                        <p className="text-sm text-navy-light mt-1">{event.description}</p>
                      )}
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => openEditDialog(event)}
                        className="p-1 hover:bg-sage/20 rounded"
                        data-testid={`edit-event-${event.id}`}
                      >
                        <Edit2 className="w-4 h-4 text-sage" />
                      </button>
                      <button
                        onClick={() => handleDelete(event.id)}
                        className="p-1 hover:bg-red-100 rounded"
                        data-testid={`delete-event-${event.id}`}
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
      </div>
    </div>
  );
};

export default CalendarPage;
