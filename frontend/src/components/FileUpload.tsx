import React, { useState } from 'react';
import supabase from '@/lib/supabase';
import { API_BASE_URL } from '@/lib/api';

interface FileUploadProps {
  onFileUpload: (file: File) => void;
  projectId?: number;
  onUploadSuccess?: (result: any) => void;
  refreshSources?: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload, projectId, onUploadSuccess, refreshSources }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState('');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      handleFileUpload(event.target.files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);
    console.log(`Starting upload of file ${file.name} for project ${projectId}`);
    
    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      
      // Add simple_mode=true to maintain compatibility with the old /upload endpoint
      formData.append('simple_mode', 'true');
      
      // Add project_id if available
      if (projectId) {
        formData.append('project_id', projectId.toString());
        console.log(`Added project_id ${projectId} to form data`);
      } else {
        console.warn('No project_id available for file upload');
      }
      
      // Add user_id if available
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user?.id) {
        formData.append('user_id', session.user.id);
        console.log(`Added user_id ${session.user.id} to form data`);
      } else {
        console.warn('No user_id available for file upload');
      }
      
      // Upload the file
      console.log(`Sending request to ${API_BASE_URL}/ingest`);
      const response = await fetch(`${API_BASE_URL}/ingest`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Upload failed: ${response.statusText}`, errorText);
        throw new Error(`Upload failed: ${response.statusText}. ${errorText}`);
      }
      
      const result = await response.json();
      console.log('Upload response:', result);
      
      // If the upload was successful, show success message
      if (result.status === 'success') {
        setUploadStatus('success');
        setUploadMessage(`Successfully uploaded and processed ${file.name}`);
        
        // If onUploadSuccess callback is provided, call it with the result
        if (onUploadSuccess) {
          onUploadSuccess(result);
        }
        
        // Check if sources were updated
        console.log('Checking if sources were updated:', result.sources_updated);
        
        // If the response includes sources, refresh the sources panel
        if (result.sources) {
          console.log('Sources from response:', result.sources);
          if (refreshSources) {
            console.log('Refreshing sources panel with sources from response');
            refreshSources();
          }
        } else if (result.sources_updated) {
          console.log('Sources were updated according to response');
          if (refreshSources) {
            console.log('Refreshing sources panel because sources_updated is true');
            refreshSources();
          }
        } else {
          console.log('No sources in response and sources_updated is not true');
          
          // Try refreshing anyway after a delay
          if (refreshSources) {
            console.log('Refreshing sources panel after delay as fallback');
            setTimeout(() => {
              refreshSources?.();
            }, 2000);
          }
        }
      } else {
        setUploadStatus('error');
        setUploadMessage(`Error: ${result.message}`);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setUploadStatus('error');
      setUploadMessage(`Error uploading file: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setIsUploading(false);
      setUploadProgress(100);
      
      // Reset status after a delay
      setTimeout(() => {
        setUploadStatus(null);
        setUploadMessage('');
      }, 5000);
    }
  };

  return (
    <div className="flex items-center">
      <label htmlFor="file-upload" className="cursor-pointer">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6 text-gray-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M16.5 6.5l-7.12 7.12c-.78.78-.78 2.05 0 2.83.78.78 2.05.78 2.83 0l5.29-5.29c1.17-1.17 1.17-3.07 0-4.24-1.17-1.17-3.07-1.17-4.24 0L6.34 12.34a3.5 3.5 0 004.95 4.95l5.29-5.29"
          />
        </svg>
      </label>
      <input
        id="file-upload"
        type="file"
        className="hidden"
        onChange={handleFileChange}
      />
      {uploadStatus && (
        <div className={`ml-2 text-sm ${uploadStatus === 'success' ? 'text-green-600' : 'text-red-600'}`}>
          {uploadMessage}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
