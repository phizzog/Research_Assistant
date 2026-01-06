import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FiPlus, FiFile, FiCheck, FiEdit2, FiSave, FiRefreshCw, FiX, FiInfo, FiTrash2, FiSearch, FiExternalLink } from 'react-icons/fi';
import supabase from '@/lib/supabase';
import { getProjectById, Source, uploadFile } from '@/lib/api';

// Updated interface to match the new schema
interface SourceWithState extends Source {
  selected?: boolean;
  isEditing?: boolean;
  editName?: string;
  showSummary?: boolean; // New field to control summary visibility
}

interface UploadingFile {
  file: File;
  progress: number;
  name: string;
  id: string;
}

// Add new interface for queued files
interface QueuedFile {
  file: File;
  id: string;
  name: string;
}

interface SourcesPanelProps {
  onFileUpload: (file: File) => void;
  projectId: number;
  refreshSources?: () => void;
  onSourceSelectionChange?: (selectedDocumentIds: string[]) => void;
}

// Knowledge gap interface
interface KnowledgeGap {
  gap_description: string;
  importance: number;
  suggested_queries: string[];
}

// Search result interface
interface SearchResult {
  title: string;
  url: string;
  content: string;
  score: number;
}

const SourcesPanel: React.FC<SourcesPanelProps> = ({ 
  onFileUpload, 
  projectId, 
  refreshSources,
  onSourceSelectionChange 
}) => {
  const [sources, setSources] = useState<SourceWithState[]>([]);
  const [allSelected, setAllSelected] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [suggestingSources, setSuggestingSources] = useState(false);
  
  // Modal states
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [knowledgeGaps, setKnowledgeGaps] = useState<KnowledgeGap[]>([]);
  const [selectedGap, setSelectedGap] = useState<KnowledgeGap | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [activeStep, setActiveStep] = useState<'gaps' | 'results'>('gaps');
  
  // New states for upload modal
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [queuedFiles, setQueuedFiles] = useState<QueuedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const multiFileInputRef = useRef<HTMLInputElement>(null);
  const sourcesLoaded = useRef(false);
  
  // Helper function to get the best display name for a source
  const getDisplayName = (source: Source): string => {
    // Prioritize AI-generated title if available, otherwise fallback to name or document_id
    return source.display_name || source.title || source.name || source.document_id || 'Untitled Source';
  };
  
  // Fetch sources from the project's sources field
  const fetchSources = useCallback(async () => {
    if (!projectId) return;
    
    // Don't fetch if we're already refreshing
    if (refreshing) return;
    
    setRefreshing(true);
    try {
      // First, check if the sources column exists in the projects table
      try {
        const { data: columnData, error: columnError } = await supabase
          .from('projects')
          .select('sources')
          .eq('project_id', projectId)
          .single();
          
        if (columnError) {
        } else {
          
          if (columnData && columnData.sources) {
            
            // Transform the sources to include selected state and editing state
            const sourcesWithSelection = (columnData.sources || []).map((source: Source) => {
              // Get the display name (preferring display_name/title over name)
              const displayName = getDisplayName(source);
              
              return {
                ...source,
                // Ensure name or title is set for display
                name: source.name || displayName,
                title: source.title || displayName,
                display_name: source.display_name || displayName,
                selected: true,
                isEditing: false,
                editName: source.title || source.name || displayName,
                showSummary: false // Always ensure summary is closed by default
              };
            });

            setSources(sourcesWithSelection);
            
            // Immediately notify parent of selected document IDs
            if (onSourceSelectionChange && sourcesWithSelection.length > 0) {
              const selectedIds = sourcesWithSelection
                .filter((source: SourceWithState) => source.selected)
                .map((source: SourceWithState) => source.document_id);
              onSourceSelectionChange(selectedIds);
            } else {
            }
            
            sourcesLoaded.current = true;
            setRefreshing(false);
            setIsLoading(false);
            return;
          } else {
          }
        }
      } catch (error) {
      }
      
      // If direct query fails or returns no sources, try using the API
      try {
        // Get the project data which includes the sources field
        const project = await getProjectById(projectId);
        
        if (project && project.sources) {
          
          // Transform the sources to include selected state and editing state
          const sourcesWithSelection = (project.sources || []).map((source: Source) => {
            // Get the display name (preferring display_name/title over name)
            const displayName = getDisplayName(source);
            
            return {
              ...source,
              // Ensure name or title is set for display
              name: source.name || displayName,
              title: source.title || displayName,
              display_name: source.display_name || displayName,
              selected: true,
              isEditing: false,
              editName: source.title || source.name || displayName,
              showSummary: false // Always ensure summary is closed by default
            };
          });

          setSources(sourcesWithSelection);
          
          // Immediately notify parent of selected document IDs
          if (onSourceSelectionChange && sourcesWithSelection.length > 0) {
            const selectedIds = sourcesWithSelection
              .filter((source: SourceWithState) => source.selected)
              .map((source: SourceWithState) => source.document_id);
            onSourceSelectionChange(selectedIds);
          } else {
          }
        } else {
          setSources([]);
        }
        
        sourcesLoaded.current = true;
      } catch (error) {
        setSources([]);
      }
    } catch (error) {
      setSources([]);
    } finally {
      setRefreshing(false);
      setIsLoading(false);
    }
  }, [projectId, onSourceSelectionChange]);

  // Initial fetch only once
  useEffect(() => {
    if (projectId && !sourcesLoaded.current) {
      fetchSources();
    }
  }, [projectId, fetchSources]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      handleFileUpload(file);
    }
  };
  
  // Handle drag and drop
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  
  // Helper to check if file type is acceptable
  const isValidFileType = (file: File): boolean => {
    const validTypes = [
      'application/pdf',
      'text/plain',
      'text/markdown',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    
    // Also check file extension as a fallback
    const validExtensions = ['.pdf', '.txt', '.md', '.doc', '.docx'];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));
    
    return validTypes.includes(file.type) || hasValidExtension;
  };
  
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      // Filter valid files
      const validFiles = Array.from(e.dataTransfer.files)
        .filter(isValidFileType)
        .map(file => ({
          file,
          id: `queued-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          name: file.name
        }));
      
      if (validFiles.length > 0) {
        setQueuedFiles(prev => [...prev, ...validFiles]);
      }
      
      // Alert if some files were invalid
      const invalidCount = e.dataTransfer.files.length - validFiles.length;
      if (invalidCount > 0) {
        alert(`${invalidCount} ${invalidCount === 1 ? 'file was' : 'files were'} not added because they are not supported. Please use PDF, TXT, MD, DOC, or DOCX files.`);
      }
    }
  };
  
  // New handler for multi-file selection with validation
  const handleMultiFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      // Filter valid files
      const validFiles = Array.from(event.target.files)
        .filter(isValidFileType)
        .map(file => ({
          file,
          id: `queued-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          name: file.name
        }));
      
      if (validFiles.length > 0) {
        setQueuedFiles(prev => [...prev, ...validFiles]);
      }
      
      // Alert if some files were invalid
      const invalidCount = event.target.files.length - validFiles.length;
      if (invalidCount > 0) {
        alert(`${invalidCount} ${invalidCount === 1 ? 'file was' : 'files were'} not added because they are not supported. Please use PDF, TXT, MD, DOC, or DOCX files.`);
      }
      
      // Reset file input
      if (multiFileInputRef.current) multiFileInputRef.current.value = "";
    }
  };
  
  // Remove a file from the queue
  const removeQueuedFile = (id: string) => {
    setQueuedFiles(prev => prev.filter(f => f.id !== id));
  };
  
  // Upload all queued files
  const uploadQueuedFiles = async () => {
    if (queuedFiles.length === 0) return;
    
    setIsUploading(true);
    
    // Process files one by one
    for (const queuedFile of queuedFiles) {
      await handleFileUpload(queuedFile.file);
    }
    
    // Clear queue and close modal
    setQueuedFiles([]);
    setShowUploadModal(false);
    setIsUploading(false);
  };
  
  // Open upload modal
  const openUploadModal = () => {
    setShowUploadModal(true);
    setQueuedFiles([]);
  };
  
  const handleFileUpload = async (file: File) => {
    const fileId = `file-${Date.now()}`;
    // Use original filename for the temporary display
    const fileName = file.name;
    
    // Add to uploading files with 0% progress
    setUploadingFiles(prev => [...prev, {
      file,
      progress: 0,
      name: fileName,
      id: fileId
    }]);
    
    // Reset file input
    if (fileInputRef.current) fileInputRef.current.value = "";
    
    // Simulate progress updates
    const simulateProgress = () => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) {
          clearInterval(interval);
          progress = 90; // Wait at 90% for actual completion
        }
        
        setUploadingFiles(prev => 
          prev.map(item => 
            item.id === fileId ? { ...item, progress: Math.min(progress, 90) } : item
          )
        );
      }, 500);
      
      return interval;
    };
    
    const progressInterval = simulateProgress();
    
    try {
      // Call the onFileUpload function to handle the upload
      await onFileUpload(file);
      
      // Set progress to 100% when complete
      setUploadingFiles(prev => 
        prev.map(item => 
          item.id === fileId ? { ...item, progress: 100 } : item
        )
      );
      
      clearInterval(progressInterval);
      
      // Wait a moment to show 100% before removing
      setTimeout(() => {
        setUploadingFiles(prev => prev.filter(item => item.id !== fileId));
        fetchSources(); // Refresh sources after successful upload
      }, 1000);
    } catch (error) {
      clearInterval(progressInterval);
      
      // Mark as failed
      setUploadingFiles(prev => 
        prev.map(item => 
          item.id === fileId ? { ...item, progress: -1 } : item
        )
      );
      
      // Remove failed upload after a delay
      setTimeout(() => {
        setUploadingFiles(prev => prev.filter(item => item.id !== fileId));
      }, 3000);
    }
  };
  
  const cancelUpload = (fileId: string) => {
    setUploadingFiles(prev => prev.filter(item => item.id !== fileId));
  };

  const toggleSourceSelection = (documentId: string) => {
    const updatedSources = sources.map(source => 
      source.document_id === documentId ? { ...source, selected: !source.selected } : source
    );
    setSources(updatedSources);
    
    // Update allSelected state based on whether all sources are selected
    setAllSelected(updatedSources.every(source => source.selected));
    
    // Directly notify parent of selection change
    if (onSourceSelectionChange) {
      const selectedIds = updatedSources
        .filter((source: SourceWithState) => source.selected)
        .map((source: SourceWithState) => source.document_id);
      onSourceSelectionChange(selectedIds);
    }
  };

  const toggleAllSelection = () => {
    const newSelectedState = !allSelected;
    setAllSelected(newSelectedState);
    const updatedSources = sources.map(source => ({ ...source, selected: newSelectedState }));
    setSources(updatedSources);
    
    // Directly notify parent of selection change
    if (onSourceSelectionChange) {
      const selectedIds = newSelectedState ? 
        updatedSources.map((source: SourceWithState) => source.document_id) : 
        [];
      onSourceSelectionChange(selectedIds);
    }
  };

  // Toggle summary visibility for a source
  const toggleSummary = (documentId: string) => {
    setSources(sources.map(source => 
      source.document_id === documentId
        ? { ...source, showSummary: !source.showSummary }
        : source
    ));
  };

  // Start editing a source name
  const startEditing = (documentId: string) => {
    setSources(sources.map(source => 
      source.document_id === documentId 
        ? { 
            ...source, 
            isEditing: true, 
            editName: source.title || source.display_name || source.name, 
            showSummary: false  // Close summary when editing
          } 
        : { ...source, isEditing: false }
    ));
  };

  // Handle name input change
  const handleNameChange = (documentId: string, value: string) => {
    setSources(sources.map(source => 
      source.document_id === documentId ? { ...source, editName: value } : source
    ));
  };

  // Save the edited name
  const saveSourceName = async (documentId: string) => {
    const sourceToUpdate = sources.find(source => source.document_id === documentId);
    if (!sourceToUpdate) return;

    const newName = sourceToUpdate.editName?.trim();
    if (!newName) return;

    try {
      // Get the current project data
      const { data: projectData, error: projectError } = await supabase
        .from('projects')
        .select('sources')
        .eq('project_id', projectId)
        .single();
        
      if (projectError) {
        return;
      }
      
      // Update the source name in the sources array
      const updatedSources = (projectData.sources || []).map((source: Source) => 
        source.document_id === documentId 
          ? { 
              ...source, 
              title: newName,            // Update title 
              display_name: newName,     // Update display_name
              name: newName              // Keep name for backward compatibility
            } 
          : source
      );
      
      // Update the project with the new sources list
      const { error: updateError } = await supabase
        .from('projects')
        .update({ sources: updatedSources })
        .eq('project_id', projectId);
        
      if (updateError) {
        return;
      }

      // Update local state
      setSources(sources.map(source => 
        source.document_id === documentId 
          ? { 
              ...source, 
              isEditing: false, 
              title: newName,
              display_name: newName,
              name: newName, // Keep name for backward compatibility
              showSummary: false // Close summary after editing
            } 
          : source
      ));
    } catch (error) {
    }
  };

  // Delete a source and its chunks
  const deleteSource = async (documentId: string) => {
    if (!confirm("Are you sure you want to delete this source? This will remove all associated content from the project.")) {
      return;
    }
    
    try {
      
      // Try calling the Supabase function first if it exists
      try {
        const { data: functionData, error: functionError } = await supabase.rpc('delete_source_complete', {
          doc_id: documentId,
          proj_id: projectId
        });
        
        if (!functionError) {
          
          // Update local state
          setSources(sources.filter(source => source.document_id !== documentId));
          
          // Update selection if needed
          if (onSourceSelectionChange) {
            const selectedIds = sources
              .filter(source => source.selected && source.document_id !== documentId)
              .map(source => source.document_id);
            onSourceSelectionChange(selectedIds);
          }
          
          return;
        } else {
        }
      } catch (fnError) {
      }
      
      // Fall back to client-side deletion if the function doesn't exist or fails
      // 1. First get the current project data
      const { data: projectData, error: projectError } = await supabase
        .from('projects')
        .select('sources')
        .eq('project_id', projectId)
        .single();
        
      if (projectError) {
        alert('Error deleting source: Could not fetch project data');
        return;
      }
      
      // 2. Filter out the source to be deleted
      const updatedSources = (projectData.sources || []).filter(
        (source: Source) => source.document_id !== documentId
      );
      
      // 3. Update the project with the filtered sources
      const { error: updateError } = await supabase
        .from('projects')
        .update({ sources: updatedSources })
        .eq('project_id', projectId);
        
      if (updateError) {
        alert('Error deleting source: Could not update project sources');
        return;
      }
      
      // 4. Delete all chunks for this document from the sources table
      const { error: deleteError } = await supabase
        .from('sources')
        .delete()
        .eq('document_id', documentId);
        
      if (deleteError) {
        alert('Source removed from project but some data may remain in the database');
      }
      
      // 5. Update local state to remove the deleted source
      setSources(sources.filter(source => source.document_id !== documentId));
      
      // 6. Update selection if needed
      if (onSourceSelectionChange) {
        const selectedIds = sources
          .filter(source => source.selected && source.document_id !== documentId)
          .map(source => source.document_id);
        onSourceSelectionChange(selectedIds);
      }
      
      
    } catch (error) {
      alert('An error occurred while deleting the source');
    }
  };

  // Function to open the source suggestion modal
  const openSourceSuggestionModal = () => {
    setShowSourceModal(true);
    setKnowledgeGaps([]);
    setSelectedGap(null);
    setSearchResults([]);
    setActiveStep('gaps');
  };

  // Function to identify knowledge gaps
  const identifyKnowledgeGaps = async () => {
    if (!projectId) return;
    
    setAnalysisLoading(true);
    
    try {
      // Fetch project data using getProjectById from API instead of direct Supabase query
      let projectTitle = "";
      let projectGoals = "";
      let projectSources = [];
      
      try {
        // First try using getProjectById from the API
        const project = await getProjectById(projectId);
        if (project) {
          // Use the correct property names from the Project type
          projectTitle = project.project_name || "";
          projectGoals = project.description || "";
          projectSources = project.sources || [];
        }
      } catch (apiError) {
        
        // Fall back to direct Supabase query
        const { data: projectData, error: projectError } = await supabase
          .from('projects')
          .select('*')
          .eq('project_id', projectId)
          .single();
          
        if (projectError) {
          throw new Error("Could not retrieve project data");
        }
        
        if (projectData) {
          projectTitle = projectData.project_name || "";
          projectGoals = projectData.description || "";
          projectSources = projectData.sources || [];
        }
      }
      
      if (!projectTitle) {
        throw new Error("Project title not found");
      }
      
      // Call the backend API endpoint that identifies knowledge gaps
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/identify-gaps`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          project_id: projectId,
          project: {
            title: projectTitle,
            goals: projectGoals
          },
          sources: projectSources || []
        }),
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      // Set the knowledge gaps
      setKnowledgeGaps(result.identified_gaps || []);
      
    } catch (error) {
      alert('Error identifying knowledge gaps. Please try again later.');
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Function to search for sources based on selected gap
  const searchForSources = async (gap: KnowledgeGap) => {
    if (!projectId || !gap) return;
    
    setSelectedGap(gap);
    setSearchLoading(true);
    setActiveStep('results');
    setSearchResults([]);
    
    try {
      // Call the backend API endpoint to search based on the selected gap
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/search-for-gap`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          project_id: projectId,
          gap: gap
        }),
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      // Set the search results
      setSearchResults(result.results || []);
      
    } catch (error) {
      alert('Error searching for sources. Please try again later.');
    } finally {
      setSearchLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-200 w-72 min-w-72 max-w-72">
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-white flex justify-between items-center">
        <h2 className="text-lg font-semibold text-indigo-900">Sources</h2>
        <button 
          onClick={fetchSources} 
          disabled={refreshing}
          className="p-1 text-indigo-600 hover:text-indigo-800 disabled:opacity-50"
          title="Refresh sources"
        >
          <FiRefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>
      
      {/* File Upload Button */}
      <div className="p-3">
        <button 
          className="w-full flex items-center justify-center gap-2 p-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
          onClick={openUploadModal}
          disabled={isLoading}
        >
          <FiPlus className="w-4 h-4" />
          <span>Add source</span>
        </button>
        <input
          ref={fileInputRef}
          id="source-file-upload"
          type="file"
          accept=".pdf,.txt,.md,.doc,.docx"
          className="hidden"
          onChange={handleFileSelect}
          disabled={isLoading}
        />
        
        {/* Hidden multi-file input for modal */}
        <input
          ref={multiFileInputRef}
          id="multi-source-file-upload"
          type="file"
          accept=".pdf,.txt,.md,.doc,.docx"
          multiple
          className="hidden"
          onChange={handleMultiFileSelect}
          disabled={isLoading || isUploading}
        />
        
        {/* Suggest More Sources Button */}
        <button 
          className="w-full flex items-center justify-center gap-2 p-2 mt-2 text-indigo-700 bg-indigo-100 rounded-lg hover:bg-indigo-200 transition-colors disabled:opacity-50"
          onClick={openSourceSuggestionModal}
          disabled={suggestingSources || sources.length === 0 || isLoading}
        >
          <FiSearch className="w-4 h-4" />
          <span>Find knowledge gaps</span>
        </button>
        
        {/* Description of how source titles are generated */}
        <p className="mt-2 text-xs text-gray-500 px-1">
          Sources will be automatically titled and summarized using AI
        </p>
      </div>
      
      {/* Uploading files progress */}
      {uploadingFiles.length > 0 && (
        <div className="px-3 pb-3">
          <div className="bg-gray-50 rounded-md p-2">
            <h3 className="text-xs font-semibold text-gray-700 mb-2">Uploading</h3>
            {uploadingFiles.map((file) => (
              <div key={file.id} className="mb-2 last:mb-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs truncate flex-1">{file.name}</span>
                  {file.progress < 100 && file.progress >= 0 && (
                    <button 
                      onClick={() => cancelUpload(file.id)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <FiX size={14} />
                    </button>
                  )}
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                  {file.progress >= 0 ? (
                    <div 
                      className={`h-full ${file.progress === 100 ? 'bg-green-500' : 'bg-indigo-500'}`}
                      style={{ width: `${file.progress}%` }}
                    ></div>
                  ) : (
                    <div className="h-full bg-red-500" style={{ width: '100%' }}></div>
                  )}
                </div>
                {file.progress < 0 && (
                  <p className="text-xs text-red-500 mt-1">Upload failed</p>
                )}
                {file.progress === 100 && (
                  <p className="text-xs text-green-600 mt-1">Processing with AI...</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Source Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gradient-to-r from-indigo-50 to-white">
              <h2 className="text-lg font-semibold text-indigo-900">Source Upload</h2>
              <button 
                onClick={() => setShowUploadModal(false)}
                className="text-gray-500 hover:text-gray-700"
                disabled={isUploading}
              >
                <FiX className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6">
              {/* File dropzone */}
              <div 
                className={`border-2 border-dashed ${isDragging ? 'border-indigo-500 bg-indigo-100' : 'border-indigo-300 bg-indigo-50 hover:bg-indigo-100'} rounded-lg transition-colors p-8 flex flex-col items-center justify-center cursor-pointer`}
                onClick={() => multiFileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className={`w-20 h-20 ${isDragging ? 'bg-indigo-300' : 'bg-indigo-200'} rounded-full flex items-center justify-center mb-4 transition-colors`}>
                  <FiPlus className={`w-10 h-10 ${isDragging ? 'text-indigo-700' : 'text-indigo-600'}`} />
                </div>
                <p className="text-indigo-800 font-medium mb-1">
                  {isDragging ? 'Drop Files Here' : 'Add Source Files'}
                </p>
                <p className="text-gray-600 text-sm text-center">
                  {isDragging ? 'Release to add files' : 'Click to browse or drag files here'}<br />
                  Support PDF, Word, TXT, and Markdown files
                </p>
              </div>
              
              {/* Queued files list */}
              {queuedFiles.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Files to Upload ({queuedFiles.length})</h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {queuedFiles.map((file) => (
                      <div key={file.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                        <div className="flex items-center gap-2 overflow-hidden flex-1">
                          <FiFile className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                          <span className="text-sm text-black truncate">{file.name}</span>
                        </div>
                        {!isUploading && (
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              removeQueuedFile(file.id);
                            }}
                            className="text-gray-400 hover:text-red-600 p-1"
                          >
                            <FiX size={16} />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-4 border-t border-gray-200">
              {isUploading ? (
                <div>
                  <p className="text-sm text-gray-600 mb-2">Uploading sources...</p>
                  <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-indigo-500 animate-pulse"
                      style={{ width: '100%' }}
                    ></div>
                  </div>
                </div>
              ) : (
                <div className="flex gap-3">
                  <button
                    className="flex-1 p-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                    onClick={() => setShowUploadModal(false)}
                  >
                    Cancel
                  </button>
                  <button 
                    className="flex-1 flex items-center justify-center gap-2 p-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={uploadQueuedFiles}
                    disabled={queuedFiles.length === 0}
                  >
                    <span>Upload {queuedFiles.length > 0 ? `(${queuedFiles.length})` : ''}</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Select all option */}
      {sources.length > 0 && (
        <div className="p-2 border-b border-gray-200">
          <div 
            className="flex items-center gap-2 p-2 cursor-pointer hover:bg-gray-50 rounded-md"
            onClick={toggleAllSelection}
          >
            <div className={`w-5 h-5 flex items-center justify-center rounded border ${allSelected ? 'bg-indigo-600 border-indigo-600' : 'border-gray-400'}`}>
              {allSelected && <FiCheck className="w-3 h-3 text-white" />}
            </div>
            <span className="text-sm text-gray-700">Select all sources</span>
          </div>
        </div>
      )}
      
      {/* Sources list */}
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading && sources.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500 mb-2"></div>
            <p className="text-sm text-gray-500">Loading sources...</p>
          </div>
        ) : sources.length > 0 ? (
          sources.map(source => (
            <div key={source.document_id} className="mb-2 last:mb-0">
              <div 
                className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded-md group"
                title={getDisplayName(source)}
              >
                <div 
                  className={`w-5 h-5 flex items-center justify-center rounded border ${source.selected ? 'bg-indigo-600 border-indigo-600' : 'border-gray-400'} cursor-pointer`}
                  onClick={() => toggleSourceSelection(source.document_id)}
                >
                  {source.selected && <FiCheck className="w-3 h-3 text-white" />}
                </div>
                <FiFile className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                
                {source.isEditing ? (
                  <div className="flex-1 flex items-center">
                    <input
                      type="text"
                      value={source.editName || ''}
                      onChange={(e) => handleNameChange(source.document_id, e.target.value)}
                      className="flex-1 text-sm p-1 border border-gray-300 rounded"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          saveSourceName(source.document_id);
                        }
                      }}
                    />
                    <button 
                      onClick={() => saveSourceName(source.document_id)}
                      className="ml-1 p-1 text-indigo-600 hover:text-indigo-800"
                    >
                      <FiSave className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <span className="text-sm text-gray-700 flex-1 flex items-center relative group">
                      <span className="truncate max-w-[140px]">{getDisplayName(source)}</span>
                      <div className="absolute hidden group-hover:block bg-gray-800 text-white text-xs p-2 rounded z-10 top-full left-0 mt-1 max-w-[250px] break-words shadow-md">
                        {getDisplayName(source)}
                      </div>
                    </span>
                    <div className="flex opacity-0 group-hover:opacity-100 transition-opacity">
                      {source.summary && (
                        <button 
                          onClick={() => toggleSummary(source.document_id)}
                          className={`p-1 ${source.showSummary ? 'text-indigo-600' : 'text-gray-400 hover:text-indigo-600'}`}
                          title={source.showSummary ? "Hide summary" : "View summary"}
                        >
                          <FiInfo className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button 
                        onClick={() => startEditing(source.document_id)}
                        className="p-1 text-gray-400 hover:text-indigo-600"
                      >
                        <FiEdit2 className="w-3.5 h-3.5" />
                      </button>
                      <button 
                        onClick={() => deleteSource(source.document_id)}
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="Delete source"
                      >
                        <FiTrash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </>
                )}
              </div>
              
              {/* Summary section */}
              {source.showSummary && source.summary && (
                <div className="mt-1 ml-9 p-2 bg-indigo-50 border border-indigo-100 rounded-md text-xs text-black">
                  {source.summary}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 text-sm p-4 text-center">
            <p>No sources added yet</p>
            <p className="mt-2">Upload files to add them as sources</p>
          </div>
        )}
      </div>
      
      {/* Knowledge Gap Modal */}
      {showSourceModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-3xl max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-indigo-900">
                {activeStep === 'gaps' ? 'Knowledge Gaps' : 'Search Results'}
              </h2>
              <button 
                onClick={() => setShowSourceModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <FiX className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4">
              {activeStep === 'gaps' ? (
                <>
                  <div className="mb-4">
                    <p className="text-gray-700 mb-2">
                      Identify knowledge gaps in your project and find sources to fill them.
                    </p>
                    <button 
                      className="flex items-center justify-center gap-2 p-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
                      onClick={identifyKnowledgeGaps}
                      disabled={analysisLoading}
                    >
                      {analysisLoading ? (
                        <>
                          <div className="w-4 h-4 border-t-2 border-b-2 border-white rounded-full animate-spin"></div>
                          <span>Analyzing project...</span>
                        </>
                      ) : (
                        <>
                          <FiSearch className="w-4 h-4" />
                          <span>Find knowledge gaps</span>
                        </>
                      )}
                    </button>
                  </div>
                  
                  {knowledgeGaps.length > 0 ? (
                    <div>
                      <h3 className="text-md font-semibold text-gray-700 mb-2">Identified Knowledge Gaps:</h3>
                      <div className="space-y-3">
                        {knowledgeGaps.map((gap, index) => (
                          <div 
                            key={index}
                            className="p-3 border border-gray-200 rounded-lg hover:bg-indigo-50 cursor-pointer transition-colors"
                            onClick={() => searchForSources(gap)}
                          >
                            <div className="flex items-start gap-2">
                              <div className="w-6 h-6 flex items-center justify-center bg-indigo-600 text-white rounded-full flex-shrink-0 mt-0.5">
                                {index + 1}
                              </div>
                              <div>
                                <h4 className="font-medium text-gray-800">{gap.gap_description}</h4>
                                <div className="mt-1 text-sm text-gray-600">
                                  <span className="inline-block bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full text-xs mr-2">
                                    Importance: {gap.importance}/10
                                  </span>
                                  <span className="text-xs">Click to search for sources</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : !analysisLoading && (
                    <div className="text-center text-gray-500 py-8">
                      Click "Find knowledge gaps" to analyze your project
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div className="mb-4 flex items-center">
                    <button 
                      className="mr-2 p-1 text-indigo-600 hover:text-indigo-800 border border-indigo-200 rounded"
                      onClick={() => setActiveStep('gaps')}
                    >
                      <FiX className="w-4 h-4" />
                    </button>
                    <h3 className="text-md font-medium text-gray-700">
                      {selectedGap?.gap_description}
                    </h3>
                  </div>
                  
                  {searchLoading ? (
                    <div className="flex flex-col items-center justify-center py-8">
                      <div className="w-8 h-8 border-t-2 border-b-2 border-indigo-500 rounded-full animate-spin mb-2"></div>
                      <p className="text-gray-600">Searching for sources...</p>
                    </div>
                  ) : searchResults.length > 0 ? (
                    <div className="space-y-4">
                      {searchResults.map((result, index) => (
                        <div key={index} className="p-3 border border-gray-200 rounded-lg">
                          <div className="flex justify-between items-start">
                            <h4 className="font-medium text-gray-800 mb-1">{result.title}</h4>
                            <a 
                              href={result.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-indigo-600 hover:text-indigo-800 p-1"
                              title="Open in new tab"
                            >
                              <FiExternalLink className="w-4 h-4" />
                            </a>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{result.content}</p>
                          <div className="flex items-center text-xs text-gray-500">
                            <span className="inline-block bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full mr-2">
                              Relevance: {Math.round(result.score * 100)}%
                            </span>
                            <a 
                              href={result.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-indigo-600 hover:underline"
                            >
                              {result.url.substring(0, 50)}{result.url.length > 50 ? '...' : ''}
                            </a>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center text-gray-500 py-8">
                      No results found. Try a different knowledge gap.
                    </div>
                  )}
                </>
              )}
            </div>
            
            <div className="p-4 border-t border-gray-200">
              <button
                className="w-full p-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                onClick={() => setShowSourceModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SourcesPanel;
