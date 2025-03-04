# Research Assistant - Development Instructions

This document serves as a guide for the ongoing development of the Research Assistant project. It outlines the goals, architecture, database schema, and API structure to ensure consistent development.

## 🎯 Project Goal

The Research Assistant is designed to streamline the research process by allowing users to:

1. Upload and analyze research sources (PDFs, web pages, text documents)
2. Interact with an AI assistant that guides them through the research process
3. Organize their research projects and sources in one place
4. Generate insights and connections between different sources

## 🏗️ Architecture Overview

The application consists of several key components:

### Frontend (Next.js)
- Modern, responsive UI built with Next.js and React
- Split-pane layout with source viewer on the left and chat interface on the right
- Project management dashboard for organizing research activities
- Source upload and management interface

### Backend Services
- Firebase Authentication for user management
- Cloud Functions for serverless API endpoints
- Storage for source documents (PDFs, documents, etc.)
- Vector database for semantic search of document content

### AI Components
- Google Gemini AI (current implementation for development)
- Future: Custom-trained models for research assistance
- Vector embeddings for semantic search of sources
- Document parsing and chunking for proper indexing

## 📊 Database Schema

### Users Collection
```
users/
├── userId/
│   ├── email: string
│   ├── displayName: string
│   ├── photoURL: string (optional)
│   ├── createdAt: timestamp
│   ├── lastLogin: timestamp
```

### Projects Collection
```
projects/
├── projectId/
│   ├── name: string
│   ├── description: string
│   ├── ownerId: string (reference to users)
│   ├── createdAt: timestamp
│   ├── updatedAt: timestamp

```

### Sources Collection
```
sources/
├── sourceId/
│   ├── projectId: string (reference to projects)
│   ├── title: string
│   ├── type: string (pdf, webpage, text, etc.)
│   ├── originalUrl: string (optional)
│   ├── uploadedBy: string (reference to users)
│   ├── uploadedAt: timestamp
│   ├── fileSize: number
│   ├── fileUrl: string (storage reference)
│   ├── processingStatus: string (pending, processing, completed, error)
│   ├── metadata: {
│   │   ├── pageCount: number (for PDFs)
│   │   ├── author: string
│   │   ├── publishedDate: date
│   │   └── keywords: array<string>
│   │}
│   └── extractedText: string (or reference to larger text store)
```

### Chat Sessions Collection
```
chatSessions/
├── sessionId/
│   ├── projectId: string (reference to projects)
│   ├── userId: string (reference to users)
│   ├── title: string
│   ├── createdAt: timestamp
│   ├── updatedAt: timestamp
│   └── messages: array<{
│       ├── role: string (user, assistant)
│       ├── content: string
│       ├── timestamp: timestamp
│       └── sourceCitations: array<{
│           ├── sourceId: string
│           ├── pageNumber: number (optional)
│           └── textSnippet: string
│       }>
│   }>
```

### Vector Database
```
embeddings/
├── embeddingId/
│   ├── sourceId: string (reference to sources)
│   ├── chunkId: string (internal identifier)
│   ├── textChunk: string
│   ├── embedding: vector
│   ├── metadata: {
│   │   ├── pageNumber: number (optional)
│   │   ├── position: number (sequence in document)
│   │   └── context: string (surrounding text or section title)
│   │}
│   └── updatedAt: timestamp
```

## 🔄 API Structure

### Authentication Endpoints
- `POST /api/auth/signup` - Create a new user account
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/user` - Get current user information

### Projects Endpoints
- `GET /api/projects` - List user's projects
- `POST /api/projects` - Create a new project
- `GET /api/projects/:projectId` - Get project details
- `PUT /api/projects/:projectId` - Update project
- `DELETE /api/projects/:projectId` - Delete project
- `GET /api/projects/:projectId/collaborators` - List project collaborators
- `POST /api/projects/:projectId/collaborators` - Add collaborator

### Sources Endpoints
- `GET /api/projects/:projectId/sources` - List sources for a project
- `POST /api/projects/:projectId/sources` - Upload a new source
- `GET /api/sources/:sourceId` - Get source details
- `DELETE /api/sources/:sourceId` - Delete a source
- `GET /api/sources/:sourceId/content` - Get parsed content of a source
- `GET /api/sources/:sourceId/download` - Download original source file

### Chat Endpoints
- `GET /api/projects/:projectId/chat-sessions` - List chat sessions for a project
- `POST /api/projects/:projectId/chat-sessions` - Create a new chat session
- `GET /api/chat-sessions/:sessionId` - Get chat session details
- `POST /api/chat-sessions/:sessionId/messages` - Send a message
- `GET /api/chat-sessions/:sessionId/messages` - Get messages in a chat session

### Search Endpoints
- `POST /api/projects/:projectId/search` - Search across project sources
- `POST /api/sources/:sourceId/search` - Search within a specific source

## 🚀 Implementation Roadmap

### Phase 1: Basic Functionality
- User authentication
- Project creation and management
- Basic source uploading (PDF, text)
- Simple chat interface with Google Gemini

### Phase 2: Enhanced Source Management
- Document parsing and text extraction
- Vector database integration
- Source viewer implementation
- Basic semantic search

### Phase 3: Advanced Research Features
- Source citation in chat
- Research insights and connections
- Collaborative features
- Custom AI model integration

### Phase 4: Polish and Optimization
- UI/UX improvements
- Performance optimizations
- Advanced search features
- Export and sharing options

## 💻 Development Guidelines

### Code Organization
- Follow the established Next.js app directory structure
- Use TypeScript interfaces for all data models
- Implement proper error handling and loading states
- Create reusable components with proper documentation

### AI Integration
- Implement a provider pattern for AI services to allow easy switching
- Handle rate limits and API errors gracefully
- Implement streaming responses for better UX
- Ensure proper context handling for conversations

### Security Considerations
- Implement proper authentication checks for all API routes
- Sanitize user inputs to prevent injection attacks
- Follow Firebase security rules best practices
- Handle sensitive information securely

## 🧪 Testing Strategy

- Unit tests for components and utility functions
- Integration tests for API endpoints
- E2E tests for critical user flows
- Performance testing for large documents and vector searches

## 📘 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Firebase Documentation](https://firebase.google.com/docs)
- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Vector Database Resources](https://www.pinecone.io/learn/vector-database)
- [Research on RAG (Retrieval Augmented Generation)](https://www.promptingguide.ai/techniques/rag) 