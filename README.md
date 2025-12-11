# Hybrid Search Orchestrator

A powerful job search agent that orchestrates a hybrid search workflow using Large Language Models (LLMs) and Elasticsearch. This project demonstrates an agentic architecture where an LLM dynamically plans and executes search strategies.

## 🚀 Features

- **Agentic Orchestration**: Uses `qwen2.5:3b-instruct` to intelligently plan search workflows based on user queries.
- **Hybrid Search**: Combines keyword search (BM25) and vector semantic search for optimal results.
- **Query Understanding**: Automatically rewrites and expands user queries to improve recall.
- **Re-ranking**: sophisticated re-ranking of results to ensure relevance.
- **Containerized Architecture**: Fully Dockerized setup with Elasticsearch, Kibana, Encryption/Embedding services, and the Orchestrator.
- **Interactive UI**: Clean Streamlit interface for interacting with the agent.

## 🏗️ Architecture

The system consists of several microservices orchestrated via Docker Compose:

- **Orchestrator**: The core Python application that interfaces with the LLM and executes workflows.
- **Embeddings Service**: A dedicated FastAPI service serving `sentence-transformers/all-MiniLM-L6-v2` for vector generation.
- **Elasticsearch**: specialized search engine for storing job data and performing hybrid search.
- **Kibana** (Optional): UI for visualizing Elasticsearch data.
- **Streamlit UI**: User-friendly frontend for the application.
- **Ollama** (External): Runs the LLM on the host machine.

## 🛠️ Prerequisites

- **Docker** & **Docker Compose**
- **Ollama** running locally with the `qwen2.5:3b-instruct` model pulled.
  ```bash
  ollama pull qwen2.5:3b-instruct
  ```

## ⚡ Quick Start

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd orchestrator-agent
    ```

2.  **Start Services**
    ```bash
    docker-compose up --build
    ```
    *Note: Ensure Ollama is running on your host machine.*

3.  **Index Data**
    (Upon first run, you need to populate Elasticsearch)
    ```bash
    # You may need to run this from outside the container or exec into the orchestrator container
    docker exec -it orchestrator python scripts/index_jobs.py
    ```

4.  **Access the UI**
    Open your browser and navigate to: [http://localhost:8501](http://localhost:8501)

## 📂 Project Structure

- `src/orchestrator`: Core agent logic (Model communication, Prompting, Routing).
- `src/executor`: Execution engine for workflows.
- `src/tools`: Implementation of individual capabilities (Search, Rewrite, Rerank).
- `src/ui`: Streamlit frontend.
- `embeddings/`: Code for the standalone embeddings service.
- `scripts/`: Data management and indexing scripts.

## 🔧 Workflow

1.  **User Input**: User asks a question (e.g., "Find me a remote python developer job").
2.  **Planning**: The LLM analyzes the request and generates a JSON workflow (e.g., Rewrite -> Search -> Rerank).
3.  **Execution**: The Router executes the tools in the defined order.
    - *Query Rewrite*: Optimizes the search strings.
    - *Job Search*: Queries Elasticsearch (Vector + Keyword).
    - *Rerank*: Scores results for final presentation.
4.  **Response**: The system returns the structured job listings.
