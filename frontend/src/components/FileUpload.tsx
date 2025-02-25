import React from 'react';

interface FileUploadProps {
  onFileUpload: (file: File) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload }) => {
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      onFileUpload(event.target.files[0]);
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
    </div>
  );
};

export default FileUpload;
