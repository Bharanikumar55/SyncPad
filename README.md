# 🚀 Real-Time Collaborative Code Interview Platform

A full-stack web application for conducting live technical interviews with real-time code collaboration, secure execution, video communication, and **AI-powered resume analysis**.

> ⚠️ **Team Hackathon Project (2025)** > This repository is maintained for **portfolio and learning purposes**, highlighting my personal contributions to a collaborative project.

---

## ✨ Features

- 🔴 Real-time collaborative coding using **Monaco Editor**
- ⚡ Secure multi-language code execution (Python, JavaScript, C++, Java)
- 📹 Video conferencing integration (WebRTC)
- 🤖 AI-powered resume analysis and skill extraction
- 📊 Interviewer dashboard with live monitoring
- 🎥 Session recording and replay
- ✅ Hidden and visible test cases for fair assessment

---

## 🏗️ Architecture (Microservices)

```
syncpad/
├── SyncPad_candidate/        # Candidate Portal (localhost:3001)
├── SyncPad_interviewer/      # Interviewer Dashboard (localhost:3002)
└── resume_analyser/          # Resume Analyzer API (localhost:8000)
```

---

## 🛠️ Tech Stack

- **Frontend**: React, Monaco Editor, Tailwind CSS
- **Backend**: Node.js, FastAPI
- **Real-time**: Socket.io, Liveblocks
- **AI / ML**: Ollama, Hugging Face Transformers
- **Code Execution**: Judge0 API (sandboxed)
- **Database**: MongoDB
- **Authentication**: JWT / Clerk

---

## 🚀 Local Setup

### Prerequisites

```
Node.js 18+
Python 3.10+
MongoDB
```

### Resume Analyzer API

```bash
cd resume_analyser/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Candidate Portal

```bash
cd SyncPad_candidate
npm install
npm start   # http://localhost:3001
```

### Interviewer Dashboard

```bash
cd SyncPad_interviewer
npm install
npm start   # http://localhost:3002
```

---

## 🤝 Collaboration & My Contribution

This project was developed as a **collaborative hackathon project**.

My contributions focused on:

* Building the **AI Resume Analyzer** using **FastAPI**
* Integrating AI models with **Ollama** and **Hugging Face Transformers**
* Assisting with the **Monaco Editor** setup for live code collaboration
* Supporting cross-service integration and AI feature design

The final system integration and orchestration were completed collaboratively by the team.

---

## ⚠️ Project Context

* Built during a hackathon as a team project
* Developed rapidly under time constraints
* Organized and published later for portfolio presentation
* Code reflects learning, experimentation, and collaboration

---

⭐ Star the repository if you find it useful!
