# Research Assistant - Frontend

A modern, responsive web application built with Next.js that serves as the user interface for the Research Assistant project. This application allows users to interact with AI models for research assistance.

## 🚀 Features

- **AI-Powered Research Assistance**: Leverage Google's Gemini AI model to assist with research tasks
- **RAG Integration**: Connect with the backend for Retrieval-Augmented Generation capabilities
- **Responsive Design**: Built with modern UI principles for seamless experience across devices
- **Markdown Support**: Rich text formatting with syntax highlighting for code snippets
- **Supabase Integration**: Vector database for storing and retrieving research content

## 🛠️ Tech Stack

- **Framework**: [Next.js 15](https://nextjs.org/)
- **UI Library**: [React 19](https://react.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **AI**: [Google Gemini AI](https://deepmind.google/technologies/gemini/)
- **Backend Services**: [FastAPI](https://fastapi.tiangolo.com/) and [Supabase](https://supabase.com/)
- **Rendering**: Server-side and client-side rendering capabilities
- **Development**: TypeScript, ESLint, Turbopack

## 📋 Prerequisites

- Node.js 18.x or later
- npm or yarn
- Google Gemini API key
- Supabase project with appropriate configurations
- Backend API running (see backend README)

## 🔧 Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd frontend
```

2. **Install dependencies**

```bash
npm install
# or
yarn install
```

3. **Environment Setup**

Create a `.env.local` file in the root directory based on the `.env.example` file:

```bash
cp .env.example .env.local
```

Then edit the `.env.local` file with your actual credentials:

```
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key

# Google Gemini API Configuration
NEXT_PUBLIC_GEMINI_API_KEY=your-gemini-api-key
```

## 🚀 Development

Run the development server with Turbopack:

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the application.

## 📁 Project Structure

```
frontend/
├── public/           # Static assets
├── src/
│   ├── app/          # Next.js app router pages and layouts
│   ├── components/   # Reusable UI components
│   └── lib/          # Utility functions, hooks, and services
├── .env.local        # Environment variables (not in repo)
├── next.config.ts    # Next.js configuration
├── tailwind.config.ts # Tailwind CSS configuration
└── tsconfig.json     # TypeScript configuration
```

## 🔄 Backend Integration

This frontend application communicates with the Research Assistant backend API. Make sure the backend is running before starting the frontend application. The backend provides the following endpoints:

- `POST /query`: Query the research assistant with a specific question
- `POST /chat`: Chat with the research assistant, maintaining conversation history
- `POST /upload`: Upload a PDF file for analysis and storage
- `GET /health`: Health check endpoint

See the backend README for more details on setting up and running the backend.

## 🏗️ Building for Production

Build the application for production:

```bash
npm run build
# or
yarn build
```

Start the production server:

```bash
npm run start
# or
yarn start
```

## 🧪 Linting

Run linting checks:

```bash
npm run lint
# or
yarn lint
```

## 🚢 Deployment

The recommended deployment platform is [Vercel](https://vercel.com/), which is optimized for Next.js applications. Simply connect your repository to Vercel for automatic deployments.

Alternative deployment options include:
- Netlify
- AWS Amplify
- Docker containers with Nginx

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the [MIT License](LICENSE)

## 📞 Contact

Project Link: [https://github.com/yourusername/research-assistant](https://github.com/yourusername/research-assistant)
