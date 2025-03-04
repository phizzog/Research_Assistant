# Research Assistant - Frontend

A modern, responsive web application built with Next.js that serves as the user interface for the Research Assistant project. This application allows users to interact with AI models for research assistance.

## 🚀 Features

- **AI-Powered Research Assistance**: Leverage Google's Gemini AI model to assist with research tasks
- **Responsive Design**: Built with modern UI principles for seamless experience across devices
- **Markdown Support**: Rich text formatting with syntax highlighting for code snippets
- **Firebase Integration**: Authentication and data storage with Firebase

## 🛠️ Tech Stack

- **Framework**: [Next.js 15](https://nextjs.org/)
- **UI Library**: [React 19](https://react.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **AI**: [Google Gemini AI](https://deepmind.google/technologies/gemini/)
- **Backend Services**: [Firebase](https://firebase.google.com/)
- **Rendering**: Server-side and client-side rendering capabilities
- **Development**: TypeScript, ESLint, Turbopack

## 📋 Prerequisites

- Node.js 18.x or later
- npm or yarn
- Google Gemini API key
- Firebase project with appropriate configurations

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

Create a `.env.local` file in the root directory with the following variables:

```
NEXT_PUBLIC_GEMINI_API_KEY=your_gemini_api_key
```

Additionally, you'll need the Firebase admin SDK configuration file.

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
- Firebase Hosting
- Netlify
- AWS Amplify

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
