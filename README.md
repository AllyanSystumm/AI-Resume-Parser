# AI Radar Resume Parser

An advanced AI-powered resume parser and candidate matching system.

## Features

- **Resume Parsing**: Extracts text and key information from uploaded resumes.
- **AI Analysis**: Uses Groq (LLM) to analyze resumes against job descriptions.
- **Job Management**: Create and manage job postings.
- **Candidate Analyis**: View detailed analysis and scoring of candidates.
- **Chat Interface**: Context-aware chat to query candidate data.
- **Modern UI**: Built with Next.js and Tailwind CSS.

## Tech Stack

- **Frontend**: Next.js, React, Tailwind CSS, TypeScript
- **Backend**: FastAPI, Python, SQLAlchemy, SQLite
- **AI/LLM**: Groq Cloud API
- **Containerization**: Docker, Docker Compose

## Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed.
- [Groq API Key](https://console.groq.com/keys) (for AI functionality).

## Setup & Running

1. **Clone the repository** (if applicable).

2. **Configure Environment Variables**:
   
   Navigate to the `backend` directory and ensure you have a `.env` file with your API keys:
   ```bash
   # backend/.env
   GROQ_API_KEY=your_groq_api_key_here
   HF_TOKEN=your_huggingface_token_here
   ```

3. **Run with Docker Compose**:

   From the project root directory, run:
   ```bash
   docker-compose up --build
   ```

4. **Access the Application**:
   - **Frontend**: [http://localhost:3000](http://localhost:3000)
   - **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Project Structure

- `backend/`: FastAPI application, database models, and services.
- `frontend/`: Next.js frontend application.
- `docker-compose.yml`: Docker services configuration.

## Usage

1. **Create a Job**: Go to the dashboard and post a new job with a description.
2. **Apply**: Use the application form to upload a resume for a specific job.
3. **View Analysis**: Check the job dashboard to see ranked candidates and detailed AI analysis.
4. **Chat**: Use the chat interface to ask questions about the candidates.
   - **Integrated Chatbot**: The recruiter can ask directly, for example: "Give me the top scorer of the graphic designing job". The chatbot has full access to the database and can query candidate information.
<img width="2918" height="1585" alt="Screenshot from 2026-02-19 15-23-04" src="https://github.com/user-attachments/assets/21acb6c1-1264-417b-b2be-3e7c95cfe052" />
