1. Introduction
Purpose
This PRD defines the requirements for enhancing the AI Research Assistant application by adding a project dashboard tied to a unique project ID. The dashboard will provide a structured workflow based on the book Research Design: Qualitative, Quantitative, and Mixed Methods Approaches (6th Edition), guiding users through research stages with checkpoints, tailored AI assistance, and context-specific advice via a RAG system. The goal is to streamline the research process, from project definition to proposal compilation, within an interactive and intuitive interface.

Scope
The document covers:

Existing features (e.g., project creation, source ingestion, RAG-based context retrieval).
New features, focusing on the project dashboard within a project ID.
Technical requirements, user experience, and implementation details. It assumes partial implementation (using Google Gemini Flash 2.0, Supabase, and Nomic Embed API) and outlines enhancements to meet your vision.
2. Product Overview
Vision
The AI Research Assistant empowers users to conduct structured research by combining conversational AI with a guided workflow. The project dashboard, accessible via a unique project ID, will serve as a central hub, mirroring the book’s methodology (Parts I and II) to help users define, design, and document their research projects effectively.

Target Audience
Academic Researchers: Professionals crafting research proposals or studies.
Students: Undergraduates, graduates, or doctoral candidates working on theses.
Research-Intensive Professionals: Individuals in fields requiring rigorous methodology.
3. Features and Functionality
Current Features
The application already includes:

Project Creation: Users can create projects with a title, description, and goals.
Questionnaire: Suggests a research type (qualitative, quantitative, mixed methods) based on user input.
Source Ingestion: Uploads and processes PDFs, storing embeddings in Supabase via Nomic Embed API.
Conversational Interface: Provides research guidance through a chat system powered by Google Gemini Flash 2.0.
Context Retrieval (RAG): Retrieves relevant content from uploaded sources and the book for contextual responses.
New Features: Project Dashboard within Project ID
The project dashboard will be a core component tied to each project ID, offering a structured, interactive experience. Below are the key features:

1. Dashboard Interface
Overview: A central hub displaying all research steps/checkpoints for a specific project ID (e.g., /projects/{project_id}/dashboard).
Components:
Step List: Displays 10 steps (detailed below) with status indicators ("Not Started," "In Progress," "Completed").
Input Forms: Fields for project title, description, goals, and initial thoughts (Step 1), plus a dropdown to select research approach (Step 2).
Progress Tracking: A checklist or visual timeline showing completion status.
Chat Panel: A conversational AI interface for step-specific guidance.
Document Workspace: A space to draft and store research sections (e.g., introduction, purpose statement).
2. Steps/Checkpoints
Based on Research Design (6th Edition), the dashboard organizes the research process into 10 steps across two parts:

Part I: Preliminary Considerations
Step 1: Define Your Research Project
Checkpoint: Input title, description, goals, and thoughts.
Book Reference: Chapter 2 (pp. 26–28) – crafting a title and identifying significance.
Task: Enter project details (e.g., Title: "Exploring Student Resilience").
AI Guidance: "Let’s refine your title (p. 26). Is it concise and focused? What problem are you addressing?"
Step 2: Select a Research Approach
Checkpoint: Choose qualitative, quantitative, or mixed methods.
Book Reference: Chapter 1 (pp. 4–22) – approach selection criteria.
Task: Select an approach based on goals and problem.
AI Guidance: "Qualitative explores meanings, quantitative tests theories (p. 5). Which fits your project?"
Step 3: Conduct a Literature Review
Checkpoint: Summarize literature and create a literature map.
Book Reference: Chapter 2 (pp. 28–49) – literature review steps.
Task: List key sources and draft a literature map.
AI Guidance: "Search keywords like ‘resilience’ (p. 34). Need a literature map template (p. 40)?"
Step 4: Decide on the Use of Theory
Checkpoint: Determine theory’s role (if any).
Book Reference: Chapter 3 (pp. 53–73) – theory in different approaches.
Task: Identify a relevant theory or framework.
AI Guidance: "For qualitative, theory emerges later (p. 64). What concepts relate to your topic?"
Step 5: Plan Writing and Ethical Considerations
Checkpoint: Outline proposal and address ethics.
Book Reference: Chapter 4 (pp. 79–104) – writing and ethics.
Task: Draft an outline and note ethical issues (e.g., consent).
AI Guidance: "Your outline needs sections like purpose (p. 80). Any ethical concerns (p. 93)?"
Part II: Designing Research
Step 6: Write the Introduction
Checkpoint: Draft an introduction with problem and significance.
Book Reference: Chapter 5 (pp. 107–121) – introduction structure.
Task: Write an abstract and introduction.
AI Guidance: "Hook your reader with the problem (p. 112). Why does this matter?"
Step 7: Craft a Purpose Statement
Checkpoint: Write a tailored purpose statement.
Book Reference: Chapter 6 (pp. 123–141) – purpose statement scripts.
Task: Use approach-specific scripts (e.g., qualitative, p. 127).
AI Guidance: "For qualitative, focus on a phenomenon (p. 125). What’s your study’s core?"
Step 8: Formulate Research Questions and Hypotheses
Checkpoint: Develop questions/hypotheses.
Book Reference: Chapter 7 (pp. 143–155) – question types.
Task: Write approach-specific questions (e.g., qualitative, p. 146).
AI Guidance: "Questions narrow your purpose (p. 143). What do you want to explore?"
Step 9: Define Methods
Checkpoint: Detail data collection and analysis.
Book Reference: Chapters 8–10 (pp. 157–259) – methods by approach.
Task: Specify population, sampling, and procedures.
AI Guidance: "For quantitative, define variables (p. 159). Who’s your population?"
Step 10: Finalize and Review
Checkpoint: Compile and review the proposal.
Book Reference: Integrates all chapters, writing tips (pp. 84–92).
Task: Assemble sections and ensure coherence.
AI Guidance: "Does it flow (p. 88)? Are ethical issues covered (p. 93)?"
3. RAG Integration
Functionality: Retrieves book content (indexed by chapter/section) based on:
Current step (e.g., Chapter 5 for Step 6).
Research approach (e.g., Chapter 9 for qualitative).
User input (e.g., "resilience" → pp. 60–64).
Example: Query: "How do I write a qualitative purpose statement?" → Retrieves script from p. 127 and adapts it.
4. Document Workspace
Features:
Draft sections (e.g., introduction) tied to each step and project ID.
AI suggestions within the workspace (e.g., "Add a hook here, p. 112").
Compile all drafts into a final proposal with a "Compile" button.
5. Progress Tracking
Options:
Checklist: Checkboxes for each step (e.g., "Step 3 [ ]").
Timeline: Visual progress bar (e.g., "Preliminary Considerations: 80%").
Behavior: Steps unlock sequentially or auto-update based on drafts.
4. Technical Requirements
Architecture
Frontend: React or Vue.js for the dashboard, chat, and workspace.
Backend: FastAPI (existing) with new endpoints for dashboard features.
Database: Supabase (existing) for project data and drafts.
Vector Database: Supabase (existing) or Pinecone for RAG embeddings.
LLM: Google Gemini Flash 2.0 (existing).
Embeddings: Nomic Embed API (existing).
Data Flow
Project Initialization:
User creates a project, generating a project_id.
Dashboard loads at /projects/{project_id}/dashboard.
Step Progression:
User interacts with steps, updating status in project_steps.
Chat and drafts saved per step and project ID.
RAG Retrieval:
Queries combine step context, approach, and user input to fetch book content.
Compilation:
Final proposal assembled from drafts linked to project_id.
Detailed Requirements
Dashboard Components
UI: Step list, progress tracker, input forms, chat panel, workspace.
Routing: /projects/{project_id}/dashboard as the entry point.
Step Workspaces
Chat: Step-specific threads with tailored prompts (e.g., "For qualitative, p. 207").
Editor: Text fields for drafts with real-time AI suggestions.
RAG System
Indexing: Preprocess book PDF, embedding sections with Nomic Embed API.
Retrieval: Top-k passages based on step and user query.
Database Schema Updates
Existing Tables (assumed):
projects: project_id, title, description, goals, research_type.
chathistory: chat_id, project_id, message, timestamp.
New Tables:
project_steps: project_id, step_id, status, completed_at.
drafts: draft_id, project_id, step_id, content, created_at, updated_at.
API Endpoints
GET /projects/{project_id}/dashboard: Fetch dashboard data (steps, status, drafts).
POST /projects/{project_id}/steps/{step_id}/chat: Submit chat messages.
PUT /projects/{project_id}/steps/{step_id}/draft: Save draft content.
POST /projects/{project_id}/compile: Generate final proposal.
5. Non-Functional Requirements
Usability: Clear navigation, intuitive step progression.
Performance: Chat responses < 2 seconds, draft saves < 1 second.
Security: Authentication to protect project IDs and data.
Scalability: Handle multiple projects/users concurrently.
6. Implementation Plan
Phase 1: Dashboard Foundation
Build dashboard UI with step list and progress tracking.
Integrate with existing project creation and questionnaire.
Phase 2: Step Workspaces
Add chat and document workspace per step.
Enhance RAG to retrieve step-specific book content.
Phase 3: Progress and Compilation
Implement status updates and draft management.
Add proposal compilation feature.
Phase 4: Testing and Refinement
Test UX with sample users.
Optimize performance and secure data access.
7. Database Design Insights
Tables:
project_steps: Tracks step status per project ID.
drafts: Stores step-specific drafts.
Relationships:
project_steps.project_id → projects.project_id.
drafts.project_id → projects.project_id.
drafts.step_id → project_steps.step_id.
Indexes: On project_id and step_id for quick lookups.
Timestamps: created_at, updated_at in drafts for versioning.