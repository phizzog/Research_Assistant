import React, { useState, useEffect, useCallback } from 'react';
import { FiPlus, FiFile, FiCheck, FiEdit2, FiSave, FiRefreshCw } from 'react-icons/fi';
import supabase from '@/lib/supabase';
import { uploadFile, getProjectById, Source } from '@/lib/api';

interface SourceWithState extends Source {
  selected?: boolean;
  isEditing?: boolean;
  editName?: string;
}

interface SourcesPanelProps {
  onFileUpload: (file: File) => void;
  projectId: number;
  refreshSources?: () => void;
}

const SourcesPanel: React.FC<SourcesPanelProps> = ({ onFileUpload, projectId, refreshSources }) => {
  const [sources, setSources] = useState<SourceWithState[]>([]);
  const [allSelected, setAllSelected] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [debugInfo, setDebugInfo] = useState<string | null>(null);

  // Fetch sources from the project's sources field
  const fetchSources = useCallback(async () => {
    if (!projectId) return;
    
    setRefreshing(true);
    try {
      console.log(`Fetching sources for project ${projectId}`);
      
      // First, check if the sources column exists in the projects table
      try {
        const { data: columnData, error: columnError } = await supabase
          .from('projects')
          .select('sources')
          .eq('project_id', projectId)
          .single();
          
        if (columnError) {
          console.error('Error checking sources column:', columnError);
          setDebugInfo(prev => `${prev || ''}\nError checking sources column: ${columnError.message}`);
        } else {
          console.log('Direct Supabase query result:', columnData);
          setDebugInfo(prev => `${prev || ''}\nDirect Supabase query result: ${JSON.stringify(columnData)}`);
          
          if (columnData && columnData.sources) {
            console.log('Sources from direct query:', columnData.sources);
            
            // Transform the sources to include selected state and editing state
            const sourcesWithSelection = (columnData.sources || []).map((source: Source) => {
              // Find if we already have this source in our state
              const existingSource = sources.find(s => s.document_id === source.document_id);
              
              return {
                ...source,
                // Keep existing selection state if available
                selected: existingSource ? existingSource.selected : true,
                isEditing: false,
                editName: source.name
              };
            });

            setSources(sourcesWithSelection);
            setDebugInfo(prev => `${prev || ''}\nFound ${sourcesWithSelection.length} sources for project ${projectId} via direct query`);
            setRefreshing(false);
            setIsLoading(false);
            return;
          }
        }
      } catch (error) {
        console.error('Error in direct Supabase query:', error);
        setDebugInfo(prev => `${prev || ''}\nError in direct Supabase query: ${error instanceof Error ? error.message : String(error)}`);
      }
      
      // If direct query fails or returns no sources, try using the API
      try {
        // Get the project data which includes the sources field
        const project = await getProjectById(projectId);
        console.log('Project data from API:', project);
        
        if (project && project.sources) {
          console.log(`Found ${project.sources.length} sources for project ${projectId} via API:`, project.sources);
          
          // Transform the sources to include selected state and editing state
          const sourcesWithSelection = (project.sources || []).map((source: Source) => {
            // Find if we already have this source in our state
            const existingSource = sources.find(s => s.document_id === source.document_id);
            
            return {
              ...source,
              // Keep existing selection state if available
              selected: existingSource ? existingSource.selected : true,
              isEditing: false,
              editName: source.name
            };
          });

          setSources(sourcesWithSelection);
          setDebugInfo(prev => `${prev || ''}\nFound ${sourcesWithSelection.length} sources for project ${projectId} via API`);
        } else {
          console.log(`No sources found for project ${projectId} via API`);
          setDebugInfo(prev => `${prev || ''}\nNo sources found for project ${projectId} via API. Project data: ${JSON.stringify(project)}`);
          setSources([]);
        }
      } catch (error) {
        console.error('Error fetching project via API:', error);
        setDebugInfo(prev => `${prev || ''}\nError fetching project via API: ${error instanceof Error ? error.message : String(error)}`);
        setSources([]);
      }
    } catch (error) {
      console.error('Error in fetchSources:', error);
      setDebugInfo(prev => `${prev || ''}\nError fetching sources: ${error instanceof Error ? error.message : String(error)}`);
      setSources([]);
    } finally {
      setRefreshing(false);
      setIsLoading(false);
    }
  }, [projectId, sources]);

  // Initial fetch only
  useEffect(() => {
    if (projectId) {
      fetchSources();
    }
  }, [projectId, fetchSources]);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setIsLoading(true);
      setDebugInfo(`Uploading file: ${file.name}`);
      
      try {
        // Call the onFileUpload function to handle the upload
        onFileUpload(file);
        
        // Wait a moment for the backend to process the file
        setDebugInfo(prev => `${prev}\nWaiting for backend to process the file...`);
        setTimeout(() => {
          setDebugInfo(prev => `${prev}\nRefreshing sources...`);
          fetchSources();
        }, 5000); // Give the backend 5 seconds to process the file
      } catch (error) {
        console.error('Error uploading file:', error);
        setDebugInfo(prev => `${prev}\nError uploading file: ${error instanceof Error ? error.message : String(error)}`);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const toggleSourceSelection = (documentId: string) => {
    const updatedSources = sources.map(source => 
      source.document_id === documentId ? { ...source, selected: !source.selected } : source
    );
    setSources(updatedSources);
    
    // Update allSelected state based on whether all sources are selected
    setAllSelected(updatedSources.every(source => source.selected));
  };

  const toggleAllSelection = () => {
    const newSelectedState = !allSelected;
    setAllSelected(newSelectedState);
    setSources(sources.map(source => ({ ...source, selected: newSelectedState })));
  };

  // Start editing a source name
  const startEditing = (documentId: string) => {
    setSources(sources.map(source => 
      source.document_id === documentId 
        ? { ...source, isEditing: true } 
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
          ? { ...source, name: newName } 
          : source
      );
      
      // Update the project with the new sources array
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
              name: newName 
            } 
          : source
      ));
    } catch (error) {
      console.error('Error saving source name:', error);
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
      
      <div className="p-3">
        <button 
          className="w-full flex items-center justify-center gap-2 p-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
          onClick={() => document.getElementById('source-file-upload')?.click()}
          disabled={isLoading}
        >
          <FiPlus className="w-4 h-4" />
          <span>{isLoading ? 'Uploading...' : 'Add source'}</span>
        </button>
        <input
          id="source-file-upload"
          type="file"
          accept=".pdf,.txt,.md,.doc,.docx"
          className="hidden"
          onChange={handleFileChange}
          disabled={isLoading}
        />
      </div>
      
      {debugInfo && (
        <div className="p-2 border-b border-gray-200 bg-gray-50">
          <details>
            <summary className="text-xs text-gray-500 cursor-pointer">Debug Info</summary>
            <pre className="text-xs text-gray-600 mt-1 whitespace-pre-wrap">{debugInfo}</pre>
          </details>
        </div>
      )}
      
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
      
      <div className="flex-1 overflow-y-auto p-2">
        {isLoading && sources.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500 mb-2"></div>
            <p className="text-sm text-gray-500">Loading sources...</p>
          </div>
        ) : sources.length > 0 ? (
          sources.map(source => (
            <div 
              key={source.document_id}
              className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded-md group"
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
                  <span className="text-sm text-gray-700 truncate flex-1">{source.name}</span>
                  <button 
                    onClick={() => startEditing(source.document_id)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-indigo-600 transition-opacity"
                  >
                    <FiEdit2 className="w-3.5 h-3.5" />
                  </button>
                </>
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