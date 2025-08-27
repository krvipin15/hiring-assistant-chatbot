# TalentScout Hiring Assistant Chatbot

An intelligent hiring assistant chatbot for "TalentScout," a fictional recruitment agency. This project, part of the AI/ML Intern Assignment, is designed to conduct the initial screening of candidates by gathering essential information and assessing their technical skills through a conversational UI.

![Chatbot Interface](https://github.com/krvipin15/hiring-assistant-chatbot/blob/main/src/img/image.png)

## 🌟 Project Overview

The TalentScout Hiring Assistant is a sophisticated chatbot built to streamline the initial phase of the recruitment process. It interacts with candidates in a user-friendly chat interface, collects crucial information, and dynamically generates technical questions based on their declared technology stack. The primary goal is to automate and enhance the efficiency of candidate screening, ensuring a consistent and fair evaluation process while maintaining a positive candidate experience.

### ✨ Key Features

-   **🤖 Interactive Chat Interface:** A clean and intuitive UI built with Streamlit, providing a seamless and engaging experience for candidates.
-   **🗂️ Automated Information Gathering:** Collects essential candidate details, including name, contact information, years of experience, desired positions, and current location.
-   **🧠 Dynamic Technical Question Generation:** Leverages a Large Language Model (LLM) to generate relevant technical questions tailored to the candidate's specific tech stack and experience level.
-   **🔒 Secure Data Handling:** All sensitive candidate information (phone number, email, location) is encrypted before being stored in a secure SQLite database, ensuring data privacy and compliance with best practices.
-   **⚙️ State-of-the-art Conversation Management:** A robust state machine tracks the conversation's progress, guiding the candidate through the screening process in a structured and coherent manner.
-   **✅ Input Validation:** Implements real-time validation for inputs like email addresses, phone numbers, and locations to ensure data accuracy.
-   **📊 Progress Tracking:** A visual progress bar and status indicator keep the candidate informed about their progress through the screening process.

## 🛠️ Technical Details

This project is built with a modular and scalable architecture, ensuring maintainability and readability. The core logic is separated into distinct managers responsible for conversation flow, database interactions, AI model management, and data encryption.

### 📚 Libraries & Tools

-   **Frontend:** `streamlit`
-   **LLM Integration:** `openai` (for OpenRouter API)
-   **Database:** `sqlite3`
-   **Encryption:** `cryptography` (Fernet)
-   **Data Validation:** `email-validator`, `phonenumbers`, `requests`
-   **Configuration:** `python-dotenv`
-   **Logging:** `loguru`

### 🏛️ Architecture

-   **`app.py`**: The main entry point for the Streamlit application. It handles the UI rendering, session state, and user interaction.
-   **`core/conversation_manager.py`**: The brain of the chatbot. It manages the conversation state, orchestrates the flow, and integrates with other core modules.
-   **`core/model_manager.py`**: Interfaces with the OpenRouter API to generate AI-driven responses and technical questions.
-   **`core/database_manager.py`**: Manages all database operations, including creating the schema and saving candidate data.
-   **`core/encryption_handler.py`**: Handles the symmetric encryption and decryption of sensitive data.
-   **`core/data_validator.py`**: Provides utility functions to validate candidate-provided data against standard formats.
-   **`scripts/`**: Contains helper scripts for generating the encryption key and decrypting the database for review.

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### 📋 Prerequisites

-   Python 3.10 or higher
-   `uv` (or `pip` and `venv`)

### ⚙️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/vipinkumarec/hiring-assistant-chatbot.git
    cd hiring-assistant-chatbot
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    uv pip install -e .
    ```

4.  **Generate an encryption key:**
    Run the following command. It will print a key to the console and create a `.env` file.
    ```bash
    generate-key --write
    ```

5.  **Configure environment variables:**
    Open the newly created `.env` file and add your OpenRouter API key and the desired model name:
    ```env
    ENCRYPTION_KEY=your_generated_key_is_already_here
    OPENROUTER_API_KEY=your_openrouter_api_key_here
    OPENROUTER_MODEL=google/gemma-7b-it
    DATABASE_URL=sqlite:///candidates.db
    ```

### ▶️ Running the Application

Once the installation is complete, run the following command to start the Streamlit application:

```bash
streamlit run src/app.py
```

The application will open in your default web browser.

## 🐳 Docker Usage

You can also build and run the application using Docker. This is a convenient way to manage dependencies and ensure a consistent environment.

1.  **Build the Docker image:**
    From the project root directory, run the following command:
    ```bash
    sudo docker build -t hiring-assistant-chatbot .
    ```

2.  **Prepare the `.env` file:**
    Make sure you have a `.env` file in the project root, as described in the installation guide. Docker will use this file to provide environment variables to the container.

3.  **Run the Docker container:**
    This command will start the application and map port `8501` on your local machine to the container's port.
    ```bash
    sudo docker run --rm -p 8501:8501 --env-file .env hiring-assistant-chatbot
    ```
    You can then access the application at `http://localhost:8501`.

### Accessing the Database

The application stores candidate data in a SQLite database file named `candidates.db`. When running the application inside a Docker container, this database file is created within the container's filesystem at `/app/candidates.db`.

By default, this file is ephemeral and will be lost when the Docker container is stopped and removed. To make the database persistent and access it on your host machine, you should use a Docker bind mount.

Modify your `docker run` command to mount a local file to the database file's location inside the container:

```bash
sudo docker run --rm -p 8501:8501 --env-file .env -v "$(pwd)/candidates.db:/app/candidates.db" hiring-assistant-chatbot
```

This command will create a `candidates.db` file in your project's root directory on your host machine. This file is synchronized with the database inside the container, allowing you to access it directly.

## 📖 Usage Guide

-   **Candidate Interaction:** Simply follow the chatbot's prompts. Provide your information as requested and answer the technical questions to the best of your ability.
-   **Exiting the Chat:** You can type `exit` or `quit` at any time to end the conversation. Your progress will be saved.
-   **Decrypting the Database:** To view the collected data in a decrypted format, run the `decrypt-db` script. This will create a `decrypt_candidates.db` file.
    ```bash
    decrypt-db
    ```

## 🧠 Prompt Design

The effectiveness of the chatbot relies heavily on carefully crafted prompts. The prompt engineering strategy focuses on several key areas:

1.  **System Prompt:** A master prompt in `model_manager.py` defines the AI's persona—a professional, friendly, and efficient hiring assistant. It sets the ground rules for the conversation, ensuring a positive candidate experience.
2.  **Contextual Question Generation:** Prompts for technical questions are dynamically generated in `conversation_manager.py`. They include crucial context such as the candidate's years of experience, the specific technology being discussed, and even previous responses to generate highly relevant and appropriately leveled questions.
3.  **Follow-up Questions:** The system assesses the quality and depth of a candidate's answer. If a response is brief or particularly interesting, a specific prompt is used to generate a follow-up question, allowing for a deeper dive into the candidate's knowledge.
4.  **State-Driven Prompts:** Each state in the conversation flow has a unique set of prompts designed to guide the user to the next stage, ensuring a logical and smooth progression.

## 🎯 Challenges & Solutions

-   **Challenge:** Ensuring the privacy and security of sensitive candidate data.
    -   **Solution:** Implemented robust, end-to-end encryption for all personally identifiable information (PII) using the `cryptography` library. Data is encrypted before it touches the database and is only decrypted via a secure script, never in the main application.

-   **Challenge:** Maintaining a coherent, context-aware conversation that doesn't feel robotic.
    -   **Solution:** A finite state machine was designed and implemented in the `ConversationManager`. This allows the chatbot to track its position in the screening process, handle unexpected inputs gracefully, and transition smoothly between collecting information and technical assessment.

-   **Challenge:** Generating high-quality, relevant technical questions for a diverse range of technologies and experience levels.
    -   **Solution:** Developed a dynamic prompt generation system that feeds the LLM with rich context, including the candidate's experience level and tech stack. This ensures questions are not generic but are tailored to assess the candidate's true proficiency.

-   **Challenge:** Gracefully handling invalid or unexpected user inputs without frustrating the user.
    -   **Solution:** Integrated a data validation layer (`data_validator.py`) that provides real-time checks for common inputs like emails and phone numbers. When validation fails, the `ConversationManager` re-prompts the user with clear, helpful instructions, preventing bad data from entering the system and improving the user experience.