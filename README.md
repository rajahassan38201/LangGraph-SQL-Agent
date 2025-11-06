# LangGraph SQL Agent Chatbot

This project is a web-based chatbot that acts as an intelligent SQL Agent. It uses **LangGraph** to create a stateful agent that can understand natural language, generate its own SQL queries, and interact with a **SQLite** database to answer questions.

The backend is built with **FastAPI** and streams responses using Server-Sent Events (SSE). The frontend is a single, self-contained **HTML file** using **Tailwind CSS** that provides a clean, real-time chat interface.

## 🚀 Features

  * **Natural Language Queries**: Ask "Who has the highest salary?" instead of writing `SELECT Name FROM Employees ORDER BY Salary DESC LIMIT 1`.
  * **Streaming Responses**: The AI's answer streams back token-by-token, just like modern chatbots.
  * **Agent "Thinking" UI**: The frontend shows the agent's process (e.g., "Executing SQL Query", "Received Result") so you can see its work.
  * **Conversation Memory**: The agent remembers the context of the conversation (e.g., if you ask "who is he?" about a previous answer).
  * **Simple Stack**: Built with only three main files (`app.py`, `sql.py`, `index.html`). No complex frontend frameworks.
  * **Self-Contained Database**: Automatically creates and populates a `company.db` (SQLite) file on the first run.

-----

## 🛠️ How It Works

1.  **Frontend (`index.html`):** The user sends a message from the HTML/Tailwind interface.
2.  **API (`app.py`):** A FastAPI endpoint (`/chat_stream/...`) receives the message.
3.  **LangGraph (`app.py`):** The message is passed to the LangGraph agent.
4.  **LLM (Model Node):** The AI model (GPT-4o) receives the chat history and the new message. It decides if it can answer directly or if it needs to use a tool.
5.  **Tool Call (Router Node):** The agent decides to call a SQL tool.
6.  **Tool Execution (`sql.py`):**
      * The agent first calls `sql_db_list_tables` to see what tables are available.
      * It then generates and executes a query using `sql_db_query`.
7.  **Database (`company.db`):** The SQL query is run against the SQLite database.
8.  **Response (Model Node):** The SQL result (e.g., `[('David Brown',)]`) is sent back to the LLM. The LLM then formulates a natural language answer (e.g., "The employee with the highest salary is David Brown.").
9.  **Stream (FastAPI):** This final answer is streamed back to the frontend, along with all the intermediate tool steps.

-----

## ⚙️ Setup and Installation

### 1\. Project Files

You will have three main files in your project directory:

  * `sql.py`: Handles database connection, creation, and LangChain tool setup.
  * `app.py`: Contains the FastAPI server and the LangGraph agent logic.
  * `index.html`: The complete frontend (UI, styling, and JavaScript).

### 2\. Install Dependencies

Install all the required Python packages.

```bash
pip install "langgraph[all]" langchain-openai "langchain-community[sql]" fastapi uvicorn "sse-starlette" python-dotenv
```

### 3\. Set Environment Variables

You must create a file named `.env` in the same directory. This file stores your OpenAI API key.

**.env**

```
OPENAI_API_KEY=sk-YourOpenAIKey...
```

-----

## 🏃‍♂️ How to Run

### Step 1: Start the Backend Server

Run the `app.py` file from your terminal.

```bash
python app.py
```

The server will start on `http://127.0.0.1:8000`. You will also see a console message confirming that the database is ready:
`Database 'company.db' is ready.`

### Step 2: Open the Frontend

**Simply open the `index.html` file in your web browser.**

That's it\! The JavaScript inside `index.html` is configured to communicate with the backend server running on `http://127.0.0.1:8000`.

### Step 3: Start Chatting\!

You can now ask questions about the employee database.

**Example Questions:**

  * "Who has the highest salary?"
  * "List all employees in the Engineering department."
  * "What is the average age of the employees?"
  * "How many people work in Sales?"
  * "What is Alice Smith's email?"
