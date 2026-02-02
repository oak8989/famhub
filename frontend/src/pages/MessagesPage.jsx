import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, Send } from 'lucide-react';
import { messagesAPI } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { ScrollArea } from '../components/ui/scroll-area';

const MessagesPage = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadMessages();
    // Poll for new messages every 5 seconds
    const interval = setInterval(loadMessages, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadMessages = async () => {
    try {
      const response = await messagesAPI.getMessages();
      setMessages(response.data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
    setLoading(false);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      await messagesAPI.sendMessage({
        content: newMessage,
        sender_id: user?.id || 'guest',
        sender_name: user?.name || 'Family Member'
      });
      setNewMessage('');
      loadMessages();
    } catch (error) {
      toast.error('Failed to send message');
    }
    setSending(false);
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';
    return date.toLocaleDateString();
  };

  // Group messages by date
  const groupedMessages = messages.reduce((groups, message) => {
    const date = formatDate(message.timestamp);
    if (!groups[date]) groups[date] = [];
    groups[date].push(message);
    return groups;
  }, {});

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col" data-testid="messages-page">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b border-sunny/30">
        <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
          <MessageCircle className="w-6 h-6 text-blue-500" />
        </div>
        <div>
          <h1 className="text-2xl font-heading font-bold text-navy">Family Chat</h1>
          <p className="text-sm text-navy-light">Stay connected with your family</p>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 py-4">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="spinner" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <MessageCircle className="w-16 h-16 text-sunny mb-4" />
            <h3 className="text-xl font-heading font-bold text-navy mb-2">No messages yet</h3>
            <p className="text-navy-light font-handwritten text-lg">Start the conversation!</p>
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedMessages).map(([date, dateMessages]) => (
              <div key={date}>
                <div className="flex justify-center mb-4">
                  <span className="text-xs text-navy-light bg-cream px-3 py-1 rounded-full">
                    {date}
                  </span>
                </div>
                <div className="space-y-3">
                  {dateMessages.map((message) => {
                    const isSent = message.sender_id === user?.id;
                    return (
                      <div
                        key={message.id}
                        className={`flex items-end gap-2 ${isSent ? 'flex-row-reverse' : ''}`}
                        data-testid={`message-${message.id}`}
                      >
                        {!isSent && (
                          <Avatar className="w-8 h-8">
                            <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${message.sender_id}`} />
                            <AvatarFallback className="bg-sage text-white text-xs">
                              {message.sender_name?.charAt(0) || 'U'}
                            </AvatarFallback>
                          </Avatar>
                        )}
                        <div className={`message-bubble ${isSent ? 'sent' : 'received'}`}>
                          {!isSent && (
                            <p className="text-xs text-terracotta font-medium mb-1">
                              {message.sender_name}
                            </p>
                          )}
                          <p className="text-sm">{message.content}</p>
                          <p className={`text-xs mt-1 ${isSent ? 'text-white/70' : 'text-navy-light'}`}>
                            {formatTime(message.timestamp)}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </ScrollArea>

      {/* Input */}
      <form onSubmit={handleSend} className="pt-4 border-t border-sunny/30">
        <div className="flex gap-3">
          <Input
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="input-cozy flex-1"
            data-testid="message-input"
          />
          <Button
            type="submit"
            disabled={!newMessage.trim() || sending}
            className="btn-primary"
            data-testid="send-message-btn"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </form>
    </div>
  );
};

export default MessagesPage;
