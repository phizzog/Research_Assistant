# Research Assistant

A comprehensive platform for academic research workflow management, powered by AI and built on a modern tech stack. This system guides researchers through the structured process outlined in "Research Design: Qualitative, Quantitative, and Mixed Methods Approaches" by John W. Creswell and J. David Creswell.

![Research Assistant Platform](https://example.com/research-assistant-screenshot.png)

## 🌟 Overview

The Research Assistant serves as an intelligent companion for academic researchers, providing:

- **Structured Research Guidance**: A 10-step workflow based on established research methodology
- **AI-Powered Assistance**: Context-aware AI that understands research design principles
- **Document Management**: PDF processing, semantic search, and document organization
- **Research Methodology Support**: Specialized guidance for qualitative, quantitative, and mixed methods approaches
- **Collaborative Environment**: Project-based workflow with history tracking and context retention

## 🏛️ System Architecture

The system consists of two main components:

### Frontend (Next.js)

A modern, responsive web application built with:
- Next.js 15 and React 19
- Tailwind CSS for styling
- TypeScript for type safety
- Supabase Auth for authentication
- Client-side integration with Gemini AI

### Backend (FastAPI)

A robust API service built with:
- FastAPI for high-performance API endpoints
- Supabase for database and vector storage
- Google Gemini API for AI reasoning
- Nomic Embed API for document embeddings
- PDF processing pipeline for document ingestion

### System Interaction Diagram

```
┌─────────────┐      HTTP/JSON      ┌─────────────┐
│             │◄───────────────────►│             │
│   Frontend  │                     │   Backend   │
│  (Next.js)  │                     │  (FastAPI)  │
│             │                     │             │
└─────────────┘                     └─────────────┘
       ▲                                   ▲
       │                                   │
       ▼                                   ▼
┌─────────────┐                     ┌─────────────┐
│  Supabase   │◄───────────────────►│ Google AI   │
│  (Auth/DB)  │                     │ (Gemini)    │
└─────────────┘                     └─────────────┘
                                           ▲
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │ Nomic Embed │
                                    │    API      │
                                    └─────────────┘
```

## ✨ Key Features

### 1. Research Project Management

- Create and manage multiple research projects
- Track progress through research stages
- Store project metadata and research parameters

### 2. Intelligent Research Methodology Guidance

- AI-driven selection of appropriate research methodologies
- Tailored guidance based on research questions and goals
- Step-by-step walkthrough of research design process

### 3. Document Management

- Upload and process research papers and documents
- Automatic text extraction and semantic chunking
- Vector embeddings for semantic search
- Document selection for contextual queries

### 4. AI Research Assistant

- Context-aware conversations with Gemini AI
- Document-grounded responses to research questions
- Markdown formatting with code syntax highlighting
- Session persistence for continued conversations

### 5. RAG Implementation

- Retrieval-Augmented Generation for research-specific knowledge
- Pre-processed embeddings of research methodology textbook
- Dynamic retrieval of relevant context for each query
- Project-specific context inclusion

## 🚀 Getting Started

### Prerequisites

To run the complete Research Assistant platform, you'll need:

- Python 3.9+
- Node.js 18+
- Supabase account
- Google Gemini API key
- Nomic Embed API access
- Tavily API key (optional, for enhanced search)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/research-assistant.git
cd research-assistant
```

2. **Set up the backend**

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and credentials
```

3. **Set up the frontend**

```bash
cd ../frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env.local
# Edit .env.local with your API keys and credentials
```

4. **Start the services**

In one terminal (backend):
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m main
```

In another terminal (frontend):
```bash
cd frontend
npm run dev
```

5. **Access the application**

Open your browser and navigate to [http://localhost:3000](http://localhost:3000)

## 🔄 Project Workflow

The Research Assistant guides users through a structured 10-step process:

1. **Project Initialization**: Define project title, description, and goals
2. **Research Approach Selection**: Choose between qualitative, quantitative, or mixed methods
3. **Literature Review**: Upload and analyze relevant literature
4. **Theory Selection**: Identify and integrate appropriate theoretical frameworks
5. **Ethics Planning**: Address research ethics and compliance
6. **Introduction Drafting**: Create a compelling research introduction
7. **Purpose Statement**: Craft a clear, focused purpose statement
8. **Research Questions/Hypotheses**: Formulate precise research questions
9. **Methodology Design**: Define data collection and analysis methods
10. **Proposal Compilation**: Finalize and review the complete research proposal

## 🧠 AI Capabilities

The Research Assistant leverages Google's Gemini AI to provide:

- **Research Design Expertise**: Guidance based on established methodology
- **Literature Analysis**: Help with synthesizing research papers
- **Contextual Assistance**: Answers informed by both the research textbook and user uploads
- **Method-Specific Advice**: Tailored guidance for qualitative, quantitative, or mixed methods
- **Writing Support**: Help with formulating research questions, purpose statements, etc.

## 🔧 Technical Details

### Database Schema

The system uses Supabase with the following main tables:

- **projects**: Stores research project metadata
- **sources**: Contains document chunks and embeddings
- **chatmessages**: Archives conversation history by project
- **pdfs**: Tracks uploaded documents and their metadata

### API Endpoints

The backend provides RESTful endpoints for:

- **Project Management**: Create and update research projects
- **Document Processing**: Upload and analyze PDFs and other documents
- **AI Interaction**: Query the AI assistant with project context
- **Document Retrieval**: Search for relevant information across documents

### Authentication Flow

The system uses Supabase Auth for:

- User registration and login
- Session management
- Route protection for authenticated resources
- Project access control

## 📊 Performance Optimization

The Research Assistant is optimized for:

- **Efficient Document Processing**: Multi-stage PDF processing pipeline
- **Fast Semantic Search**: Vector embeddings with optimized similarity search
- **Responsive UI**: Split client/server rendering with Next.js
- **AI Response Speed**: Optimized context retrieval and prompt engineering
- **Scalable Architecture**: Clean separation of concerns between frontend and backend

## 🔐 Security Features

The system implements several security best practices:

- API keys stored as environment variables
- User authentication and authorization controls
- Input validation on all endpoints
- Secure document storage with access controls
- Error handling that prevents information leakage

## 🚀 Deployment

### Backend Deployment

The backend can be deployed using:

```bash
# Build the Docker image
docker build -t research-assistant-backend ./backend

# Run the container
docker run -p 8000:8000 --env-file ./backend/.env research-assistant-backend
```

### Frontend Deployment

The frontend is best deployed on Vercel:

1. Connect your GitHub repository to Vercel
2. Configure environment variables in Vercel dashboard
3. Deploy with the default Next.js settings

Alternative deployment options include Netlify, AWS Amplify, or Docker containers.

## 📚 Resources

- [Research Design: Qualitative, Quantitative, and Mixed Methods Approaches](https://us.sagepub.com/en-us/nam/research-design/book255675)
- [Google Gemini AI Documentation](https://ai.google.dev/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🤝 Contributing

We welcome contributions to the Research Assistant platform:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 🙏 Acknowledgements

- John W. Creswell and J. David Creswell for their research methodology framework
- The developers of the open-source libraries used in this project
- All contributors who have helped improve the Research Assistant platform
