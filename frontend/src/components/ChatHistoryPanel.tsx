import { useState, useEffect } from 'react';
import supabase from '@/lib/supabase';
import { format } from 'date-fns';
import { ChatHistory } from '@/lib/gemini';

interface ChatHistoryPanelProps {
  projectId: number;
  userId: string;
  onLoadConversation: (messages: ChatHistory) => void;
}

interface Conversation {
  session_id: string;
  date: string;
  messages: Array<{
    message_text: string;
    sender_type: string;
    sent_at: string;
  }>;
}

export default function ChatHistoryPanel({ projectId, userId, onLoadConversation }: ChatHistoryPanelProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadChatHistory();
  }, [projectId, userId]);

  const loadChatHistory = async () => {
    try {
      setIsLoading(true);
      setError('');

      const { data, error } = await supabase
        .from('chathistory')
        .select('*')
        .eq('project_id', projectId)
        .eq('user_id', userId)
        .order('sent_at', { ascending: true });

      if (error) throw error;

      // Group messages by session_id
      const groupedMessages = data.reduce((acc: Record<string, {
        messages: Array<{
          message_text: string;
          sender_type: string;
          sent_at: string;
        }>;
        date: string;
      }>, message) => {
        const sessionId = message.session_id || 'default';
        if (!acc[sessionId]) {
          acc[sessionId] = {
            messages: [],
            date: new Date(message.sent_at).toISOString()
          };
        }
        acc[sessionId].messages.push(message);
        return acc;
      }, {});

      // Convert to array format and sort by date (newest first)
      const conversationsArray = Object.entries(groupedMessages).map(([session_id, { messages, date }]) => ({
        session_id,
        date,
        messages
      })).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

      setConversations(conversationsArray);
    } catch (err) {
      console.error('Error loading chat history:', err);
      setError('Failed to load chat history');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadConversation = (messages: any[]) => {
    // Convert messages to ChatHistory format
    const formattedMessages = messages.map(msg => ({
      role: msg.sender_type,
      content: msg.message_text
    }));
    onLoadConversation(formattedMessages);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 p-4">
        {error}
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-white">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-indigo-900 mb-4">Chat History</h2>
        
        {conversations.length === 0 ? (
          <p className="text-gray-500">No chat history available</p>
        ) : (
          <div className="space-y-6">
            {conversations.map((conversation) => (
              <div key={conversation.session_id} className="border border-gray-200 rounded-lg">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                  <h3 className="text-sm font-medium text-gray-700">
                    {format(new Date(conversation.date), 'MMMM d, yyyy')}
                  </h3>
                </div>
                <div className="p-4">
                  <div className="space-y-2">
                    {/* Show first message from user and first response from assistant */}
                    {conversation.messages
                      .filter((msg, index, arr) => {
                        const isFirstOfType = arr.findIndex(m => m.sender_type === msg.sender_type) === index;
                        return isFirstOfType;
                      })
                      .map((msg, j) => (
                        <p key={j} className="text-sm text-gray-600 truncate">
                          <span className="font-medium">
                            {msg.sender_type === 'user' ? 'You' : 'Assistant'}:
                          </span>{' '}
                          {msg.message_text}
                        </p>
                      ))}
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    {conversation.messages.length} messages
                  </div>
                  <button
                    onClick={() => handleLoadConversation(conversation.messages)}
                    className="mt-3 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                  >
                    Load Conversation
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 