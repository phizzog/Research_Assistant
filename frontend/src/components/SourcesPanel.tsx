import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FiPlus, FiFile, FiCheck, FiEdit2, FiSave, FiRefreshCw, FiX, FiInfo, FiTrash2 } from 'react-icons/fi';
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

interface SourcesPanelProps {
  onFileUpload: (file: File) => void;
  projectId: number;
  refreshSources?: () => void;
  onSourceSelectionChange?: (selectedDocumentIds: string[]) => void;
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
  const fileInputRef = useRef<HTMLInputElement>(null);
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
    
    console.log(`Fetching sources for project ${projectId}`);
    setRefreshing(true);
    try {
      // First, check if the sources column exists in the projects table
      try {
        console.log(`Querying Supabase directly for project ${projectId} sources`);
        const { data: columnData, error: columnError } = await supabase
          .from('projects')
          .select('sources')
          .eq('project_id', projectId)
          .single();
          
        if (columnError) {
          console.error('Error checking sources column:', columnError);
        } else {
          console.log(`Supabase response for project ${projectId}:`, columnData);
          
          if (columnData && columnData.sources) {
            console.log(`Sources from Supabase for project ${projectId}:`, columnData.sources);
            
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

            console.log(`Transformed sources with selection:`, sourcesWithSelection);
            setSources(sourcesWithSelection);
            
            // Immediately notify parent of selected document IDs
            if (onSourceSelectionChange && sourcesWithSelection.length > 0) {
              const selectedIds = sourcesWithSelection
                .filter((source: SourceWithState) => source.selected)
                .map((source: SourceWithState) => source.document_id);
              console.log('Initial source selection:', selectedIds);
              onSourceSelectionChange(selectedIds);
            } else {
              console.log('No sources to select or onSourceSelectionChange not provided');
            }
            
            sourcesLoaded.current = true;
            setRefreshing(false);
            setIsLoading(false);
            return;
          } else {
            console.log(`No sources found in columnData or columnData.sources is null/undefined`);
          }
        }
      } catch (error) {
        console.error('Error in direct Supabase query:', error);
      }
      
      // If direct query fails or returns no sources, try using the API
      try {
        console.log(`Falling back to API getProjectById(${projectId})`);
        // Get the project data which includes the sources field
        const project = await getProjectById(projectId);
        console.log(`API response for project ${projectId}:`, project);
        
        if (project && project.sources) {
          console.log(`Sources from API for project ${projectId}:`, project.sources);
          
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

          console.log(`Transformed sources with selection from API:`, sourcesWithSelection);
          setSources(sourcesWithSelection);
          
          // Immediately notify parent of selected document IDs
          if (onSourceSelectionChange && sourcesWithSelection.length > 0) {
            const selectedIds = sourcesWithSelection
              .filter((source: SourceWithState) => source.selected)
              .map((source: SourceWithState) => source.document_id);
            console.log('Initial source selection (from API):', selectedIds);
            onSourceSelectionChange(selectedIds);
          } else {
            console.log('No sources to select from API or onSourceSelectionChange not provided');
          }
        } else {
          console.log(`No sources found in project response from API`);
          setSources([]);
        }
        
        sourcesLoaded.current = true;
      } catch (error) {
        console.error('Error fetching project via API:', error);
        setSources([]);
      }
    } catch (error) {
      console.error('Error in fetchSources:', error);
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
      console.error('Error uploading file:', error);
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
      console.log('Source selection toggled:', selectedIds);
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
      console.log('All sources toggled:', selectedIds);
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
        console.error('Error fetching project:', projectError);
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
        console.error('Error updating source name:', updateError);
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
      console.error('Error saving source name:', error);
    }
  };

  // Delete a source and its chunks
  const deleteSource = async (documentId: string) => {
    if (!confirm("Are you sure you want to delete this source? This will remove all associated content from the project.")) {
      return;
    }
    
    try {
      console.log(`Deleting source with document_id: ${documentId}`);
      
      // Try calling the Supabase function first if it exists
      try {
        console.log('Attempting to use Supabase function for deletion');
        const { data: functionData, error: functionError } = await supabase.rpc('delete_source_complete', {
          doc_id: documentId,
          proj_id: projectId
        });
        
        if (!functionError) {
          console.log('Source deleted successfully via Supabase function:', functionData);
          
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
          console.log('Supabase function not available or failed, falling back to client-side deletion');
          console.error('Function error:', functionError);
        }
      } catch (fnError) {
        console.log('Supabase function not found, using client-side deletion instead');
      }
      
      // Fall back to client-side deletion if the function doesn't exist or fails
      // 1. First get the current project data
      const { data: projectData, error: projectError } = await supabase
        .from('projects')
        .select('sources')
        .eq('project_id', projectId)
        .single();
        
      if (projectError) {
        console.error('Error fetching project for deletion:', projectError);
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
        console.error('Error updating project sources:', updateError);
        alert('Error deleting source: Could not update project sources');
        return;
      }
      
      // 4. Delete all chunks for this document from the sources table
      const { error: deleteError } = await supabase
        .from('sources')
        .delete()
        .eq('document_id', documentId);
        
      if (deleteError) {
        console.error('Error deleting source chunks:', deleteError);
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
      
      console.log(`Source ${documentId} deleted successfully via client-side deletion`);
      
    } catch (error) {
      console.error('Error in deleteSource:', error);
      alert('An error occurred while deleting the source');
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
          onClick={() => fileInputRef.current?.click()}
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
    </div>
  );
};

export default SourcesPanel;