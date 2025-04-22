# Research Assistant - Frontend

A modern, responsive Next.js web application that serves as the user interface for the Research Assistant platform. The frontend provides a comprehensive environment for conducting structured research with AI assistance, document management, and methodology guidance based on "Research Design: Qualitative, Quantitative, and Mixed Methods Approaches."

## 🚀 System Overview

The Research Assistant frontend provides a complete user interface for:

1. Managing research projects with structured workflow
2. Interacting with AI research assistants through a conversational interface
3. Uploading, managing, and exploring research documents (PDFs, papers, etc.)
4. Determining appropriate research methodologies (Qualitative, Quantitative, Mixed Methods)
5. Creating research questions, literature reviews, and methodology sections

## 💻 Architecture

The frontend is built on a modern, component-based architecture:

- **Next.js App Router**: Modern routing with file-based page organization
- **React 19 Components**: Reusable UI components with TypeScript
- **Supabase Integration**: Authentication and data storage
- **Google Gemini AI**: Integration for research assistance
- **Tailwind CSS**: Responsive styling with utility classes
- **Server/Client Components**: Optimized rendering strategy

## ✨ Key Features

- **Project Dashboard**: Create, manage, and organize research projects
- **Research Workflow**: Guided 10-step research process based on methodology
- **AI-Powered Chat**: Contextual research assistance with markdown support
- **Document Management**: Upload, view, and analyze research documents
- **Source Panel**: Select and filter documents for targeted research questions
- **Chat History**: Save and restore conversations for continued work
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Authentication**: Secure user accounts with Supabase authentication

## 🔧 Tech Stack

- **Framework**: [Next.js 15](https://nextjs.org/)
- **UI Library**: [React 19](https://reactjs.org/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **State Management**: React Context and Hooks
- **Authentication**: [Supabase Auth](https://supabase.com/auth)
- **Database**: [Supabase PostgreSQL](https://supabase.com/database)
- **AI Models**: [Google Gemini AI](https://deepmind.google/technologies/gemini/)
- **Vector Embeddings**: Nomic Embed API via backend
- **Development**: TypeScript, ESLint, Turbopack

## 📋 Prerequisites

Before setting up the frontend, ensure you have:

- Node.js 18.x or later
- npm or yarn package manager
- Supabase project with appropriate configuration
- Backend API running (see backend README.md)
- Google Gemini API key for AI features

## 🛠️ Installation & Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Research-Assistant/frontend
   ```

2. **Install dependencies**

   ```bash
   npm install
   # or
   yarn install
   ```

3. **Environment Configuration**

   Create a `.env.local` file in the root directory based on the `.env.example` file:

   ```bash
   cp .env.example .env.local
   ```

   Update the `.env.local` file with your specific credentials:

   ```
   # API Configuration
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   
   # Supabase Configuration
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-project-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   
   # Google Gemini API Configuration
   NEXT_PUBLIC_GEMINI_API_KEY=your-gemini-api-key
   ```

4. **Start the development server**

   ```bash
   npm run dev
   # or
   yarn dev
   ```

   This starts the application with Turbopack for faster development.

5. **Open the application**

   Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

```
frontend/
├── public/                # Static assets and files
├── src/
│   ├── app/               # Next.js app router pages
│   │   ├── dashboard/     # Project dashboard pages
│   │   ├── research/      # Research workspace
│   │   ├── signin/        # Authentication pages
│   │   ├── signup/        # User registration
│   │   └── layout.tsx     # Root layout
│   ├── components/        # Reusable UI components
│   │   ├── Chat.tsx               # Chat interface
│   │   ├── SourcesPanel.tsx       # Document management
│   │   ├── CreateProjectForm.tsx  # Project creation
│   │   ├── FileUpload.tsx         # Document upload
│   │   ├── ResearchTypeSelector.tsx # Research methodology
│   │   └── ...                    # Additional components
│   ├── lib/               # Utilities and services
│   │   ├── api.ts         # Backend API integration
│   │   ├── supabase.ts    # Supabase client
│   │   └── gemini.ts      # Google Gemini integration
│   ├── types/             # TypeScript type definitions
│   └── middleware.ts      # Next.js middleware for auth
├── .env.local             # Environment variables (not in repo)
├── next.config.ts         # Next.js configuration
├── tailwind.config.ts     # Tailwind CSS configuration
└── tsconfig.json          # TypeScript configuration
```

## 🖥️ Core Components

### Research Workspace

The main research environment (`src/app/research/page.tsx`) provides a complete workspace for conducting research:

- Split-pane interface with sources and chat
- Document upload and management
- AI-assisted conversation
- Research methodology selection
- Session management

### Chat Interface

The chat component (`src/components/Chat.tsx`) handles conversations with the AI research assistant:

- Message history display with markdown rendering
- User input handling
- File attachment support
- Automatic scrolling to new messages
- Session management

### Sources Panel

The sources panel (`src/components/SourcesPanel.tsx`) manages research documents:

- Document listing and selection
- Upload interface
- Filtering and searching
- Document preview
- Context selection for research questions

### Research Forms

Multiple form components guide users through the research process:

- `ResearchForm.tsx`: Initial project setup
- `ResearchQuestionsForm.tsx`: Research question definition
- `ResearchTypeSelector.tsx`: Methodology selection

## 🔌 API Integration

The frontend communicates with the backend API through services defined in `src/lib/api.ts`:

### Key API Functions

- `queryBackend`: Send single queries to the AI assistant
- `sendChatMessage`: Send messages with conversation history
- `uploadFile`: Upload and process research documents
- `getUserProjects`: Retrieve user's research projects
- `createProject`: Create new research projects
- `updateProject`: Update project details
- `getProjectById`: Load specific project data

### Backend Integration

The frontend connects to the Research Assistant backend API endpoints:

- `POST /query`: Ask questions with document context
- `POST /chat`: Chat with conversation history
- `POST /ingest`: Upload and process documents
- `POST /chat-with-project`: Project-specific conversations
- `GET /health`: Backend health checks

## 🔒 Authentication

Authentication is implemented using Supabase Auth:

- User registration and sign-in
- Session management
- Protected routes
- Auth state persistence

The authentication flow is implemented in the following files:

- `src/app/signin/page.tsx`: Login page
- `src/app/signup/page.tsx`: Registration page
- `src/middleware.ts`: Route protection
- `src/lib/supabase.ts`: Supabase client configuration

## 🔄 User Workflows

### Project Creation Flow

1. User creates a new project in the dashboard
2. System prompts for project details (title, description)
3. User completes research questionnaire
4. AI suggests appropriate research methodology
5. User confirms or changes methodology
6. Research workspace is initialized

### Document Management Flow

1. User uploads documents via SourcesPanel
2. Backend processes documents (text extraction, chunking, embedding)
3. Documents appear in the sources panel
4. User can select documents to provide context for queries
5. AI uses selected documents when answering research questions

### Research Assistant Interaction

1. User asks research-related questions in chat
2. System retrieves relevant context from selected documents
3. AI generates response with markdown formatting
4. User can iterate on questions, refining research
5. Conversations can be saved and restored

## 🎨 UI/UX Design

The interface uses a clean, focused design optimized for research:

- Split-panel layout separates sources from conversation
- Markdown formatting enhances readability
- Syntax highlighting for code snippets
- Responsive design adapts to screen size
- Clear visual hierarchy with Tailwind CSS

## 🧪 Testing

For testing the application:

```bash
# Run linting
npm run lint
# or
yarn lint
```

## 🚀 Deployment

### Building for Production

```bash
# Create production build
npm run build
# or
yarn build

# Start production server
npm run start
# or
yarn start
```

### Deployment Options

The recommended deployment platform is [Vercel](https://vercel.com/), which offers:

- Optimized Next.js hosting
- Automatic deployments from GitHub
- Environment variable management
- Edge functions support

Alternative deployment options:

- Netlify
- AWS Amplify
- Docker containers with Nginx

## 🔧 Performance Optimization

The application is optimized for performance through:

1. **Component Code-Splitting**: Lazy-loading of components
2. **Server Components**: Where applicable for faster loading
3. **Turbopack**: For faster development and rebuilds
4. **Tailwind CSS**: Minimal CSS footprint
5. **Image Optimization**: Via Next.js Image component

## 🧩 Integration with Backend

The frontend integrates with the Research Assistant backend:

1. All API calls pass through the functions in `src/lib/api.ts`
2. Documents are uploaded to the `/ingest` endpoint for processing
3. Queries use the `/query` endpoint with project context
4. Chat uses `/chat` for maintaining conversation history

## 📚 Research Methodology

The frontend guides users through research based on "Research Design: Qualitative, Quantitative, and Mixed Methods Approaches":

1. **Project Definition**: Setting goals and research questions
2. **Methodology Selection**: Guided by AI analysis of requirements
3. **Literature Review**: Document management and analysis
4. **Research Design**: Guided by the selected methodology
5. **Data Collection Planning**: Based on methodology
6. **Data Analysis Strategy**: AI assistance with appropriate techniques
7. **Results Presentation**: Guidance on reporting findings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
