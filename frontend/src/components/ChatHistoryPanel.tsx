import { useState, useEffect } from 'react';
import supabase from '@/lib/supabase';
import { format } from 'date-fns';
import { ChatHistory, ChatMessage } from '@/lib/gemini';
import { FiTrash2 } from 'react-icons/fi';

interface ChatHistoryPanelProps {
  projectId: number;
  userId: string;
  onLoadConversation: (messages: ChatHistory, sessionId: string) => void;
  showNewChat?: boolean;
}

interface Conversation {
  sessionId: string;
  messages: ChatMessage[];
  lastMessage: string;
  timestamp: Date;
}

export default function ChatHistoryPanel({ 
  projectId, 
  userId, 
  onLoadConversation,
  showNewChat = false 
}: ChatHistoryPanelProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchHistory = async () => {
      if (!projectId || !userId) {
        setIsLoading(false);
        return;
      }
      
      try {
        setIsLoading(true);
        console.log('Fetching chat history for:', { projectId, userId });
        
        const { data, error } = await supabase
          .from('chathistory')
          .select('*')
          .eq('project_id', projectId)
          .eq('user_id', userId)
          .order('sent_at', { ascending: false });

        if (error) {
          console.error('Error fetching chat history:', error);
          setError('Failed to load chat history');
          return;
        }

        console.log('Raw chat history data:', data);

        // Group messages by session_id
        const groupedMessages = data.reduce((acc, message) => {
          if (!acc[message.session_id]) {
            acc[message.session_id] = [];
          }
          acc[message.session_id].push(message);
          return acc;
        }, {} as Record<string, any[]>);

        // Convert to array of conversations
        const conversations = Object.entries(groupedMessages).map(([sessionId, messages]) => {
          const typedMessages = messages as any[];
          // Sort messages by sent_at
          const sortedMessages = typedMessages.sort((a: any, b: any) => 
            new Date(a.sent_at).getTime() - new Date(b.sent_at).getTime()
          );

          // Convert to ChatMessage format
          const chatMessages: ChatMessage[] = sortedMessages.map((msg: any) => ({
            role: msg.sender_type === 'User' ? 'user' : 'assistant',
            content: msg.message_text
          }));

          return {
            sessionId,
            messages: chatMessages,
            lastMessage: chatMessages[chatMessages.length - 1].content,
            timestamp: new Date(sortedMessages[sortedMessages.length - 1].sent_at)
          };
        });

        console.log('Fetched conversations:', conversations);
        setConversations(conversations);
        setError('');
      } catch (error) {
        console.error('Error fetching chat history:', error);
        setError('Failed to load chat history');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();

    // Add event listener for refreshHistory event
    const handleRefreshHistory = () => {
      console.log('Refreshing chat history...');
      fetchHistory();
    };

    window.addEventListener('refreshHistory', handleRefreshHistory);
    return () => {
      window.removeEventListener('refreshHistory', handleRefreshHistory);
    };
  }, [projectId, userId]);

  const handleLoadConversation = (messages: ChatMessage[], sessionId: string) => {
    console.log('Loading conversation:', messages);
    onLoadConversation(messages, sessionId);
  };

  const handleDeleteConversation = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      console.log('Deleting conversation:', sessionId);
      const { error } = await supabase
        .from('chathistory')
        .delete()
        .eq('project_id', projectId)
        .eq('user_id', userId)
        .eq('session_id', sessionId);

      if (error) throw error;

      // Remove the conversation from the local state
      setConversations(prev => prev.filter(conv => conv.sessionId !== sessionId));
      console.log('Conversation deleted successfully');
    } catch (error) {
      console.error('Error deleting conversation:', error);
      alert('Failed to delete conversation. Please try again.');
    }
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
    <div data-testid="chat-history-panel" className="h-full overflow-y-auto bg-white">
      <div className="p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-indigo-900">Chat History</h2>
          {showNewChat && (
            <button
              onClick={() => onLoadConversation([], '')}
              className="px-3 py-1 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
            >
              New Chat
            </button>
          )}
        </div>
        
        {conversations.length === 0 ? (
          <p className="text-gray-500">No chat history available</p>
        ) : (
          <div className="space-y-6">
            {conversations.map((conversation) => (
              <div key={conversation.sessionId} className="border border-gray-200 rounded-lg">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 flex justify-between items-center">
                  <h3 className="text-sm font-medium text-gray-700">
                    {format(conversation.timestamp, 'MMMM d, yyyy')}
                  </h3>
                  <button
                    onClick={() => handleDeleteConversation(conversation.sessionId)}
                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                    title="Delete conversation"
                  >
                    <FiTrash2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="p-4">
                  <div className="space-y-2">
                    {/* Show last message from user and last response from assistant */}
                    {conversation.messages
                      .slice()
                      .reverse()
                      .filter((msg, index, arr) => {
                        const isLastOfType = arr.findIndex(m => m.role === msg.role) === index;
                        return isLastOfType;
                      })
                      .reverse()
                      .map((msg, j) => (
                        <p key={j} className="text-sm text-gray-600 truncate">
                          <span className="font-medium">
                            {msg.role === 'user' ? 'You' : 'Assistant'}:
                          </span>{' '}
                          {msg.content}
                        </p>
                      ))}
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    {conversation.messages.length} messages
                  </div>
                  <button
                    onClick={() => handleLoadConversation(conversation.messages, conversation.sessionId)}
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