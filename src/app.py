import os
import sys
import base64
import streamlit as st
from pathlib import Path
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.conversation_manager import ConversationManager

# Load environment variables
load_dotenv()

# Add logo path
logo_path = Path(project_root) / "src" / "logo"


def check_environment() -> bool:
    """Check if all required environment variables are set."""
    logger.info("Checking for required environment variables.")
    required_vars = ["OPENROUTER_API_KEY", "OPENROUTER_MODEL", "ENCRYPTION_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        st.error("Missing required environment variables:")
        for var in missing_vars:
            st.error(f"  - {var}")
        st.error(
            "Please check your .env file and ensure all required variables are set."
        )
        st.error(
            "You can use the scripts in the 'scripts/' directory to generate missing keys."
        )
        return False
    logger.info("All required environment variables are present.")
    return True


def setup_page_config():
    """Configure Streamlit page settings and custom CSS."""
    logger.info("Setting up Streamlit page configuration.")
    st.set_page_config(
        page_title="TalentScout Hiring Assistant",
        page_icon=logo_path / "bot.png",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
    <style>
    .main > div { padding: 2rem 1rem; }
    .stApp > header { background-color: transparent; }
    .chat-row { display: flex; align-items: flex-start; margin-bottom: 1rem; }
    .chat-row.user { justify-content: flex-end; }
    .chat-avatar { margin: 0 0.5rem; display: flex; align-items: center; justify-content: center; }
    .chat-avatar img { width: 38px !important; height: 38px !important; object-fit: contain; }
    .chat-avatar.assistant { background-color: transparent; margin-right: 0.5rem; }
    .chat-avatar.user { margin-left: 0.5rem; order: 2; }
    .chat-bubble-container { display: flex; flex-direction: column; max-width: 70%; }
    .chat-row.user .chat-bubble-container { align-items: flex-end; order: 1; }
    .chat-bubble { padding: 0.75rem 1rem; border-radius: 0.75rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); word-wrap: break-word; }
    .chat-bubble.assistant { background: #f3f4f6; color: #111827; }
    .chat-bubble.user { background: #667eea; color: white; }
    .chat-timestamp { font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; padding: 0 0.5rem; }
    .footer-note { text-align: center; font-size: 0.8rem; color: #6b7280; margin-top: 0.5rem; }
    .status-badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.875rem; font-weight: bold; margin: 0.25rem 0; }
    .status-collecting { background-color: #fbbf24; color: #92400e; }
    .status-technical { background-color: #3b82f6; color: white; }
    .status-completed { background-color: #10b981; color: white; }
    div[data-testid="stSidebar"] > div { padding: 1rem; }
    </style>
    """,
        unsafe_allow_html=True,
    )


def initialize_session_state():
    """Initialize or correct Streamlit session state variables."""
    if "conversation_manager" not in st.session_state:
        logger.info("Initializing new ConversationManager for the session.")
        st.session_state.conversation_manager = ConversationManager()

    if "needs_response" not in st.session_state:
        logger.info("Initializing 'needs_response' flag in session state.")
        st.session_state.needs_response = False

    # **FIX**: Check for old session state format and reset if necessary
    if "messages" in st.session_state and st.session_state.messages:
        # Check if the timestamp is an integer (the old format)
        if isinstance(st.session_state.messages[0].get("timestamp"), int):
            logger.warning(
                "Old session state format detected. Resetting messages to fix compatibility."
            )
            st.session_state.messages = []  # Reset the list to fix the error

    # Initialize messages list if it's empty
    if "messages" not in st.session_state or not st.session_state.messages:
        logger.info("Initializing messages list for the new session.")
        st.session_state.messages = []
        initial_response = st.session_state.conversation_manager.handle_message("start")
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": initial_response,
                "timestamp": datetime.now(),
            }
        )


def render_sidebar():
    """Render the sidebar with progress tracking and candidate information."""
    with st.sidebar:
        st.markdown("### 📌 What to Expect")
        st.markdown(
            """
        **Information Gathering**: We'll collect basic information like your contact details, experience, and tech stack.

        **Technical Assessment**: 3–5 technical questions per skill and tailored to your experience.

        **Estimated Time**: 25–30 minutes to complete.
        """
        )

        st.markdown("### 🔎 Screening Progress")
        state_info = st.session_state.conversation_manager.get_conversation_state()
        progress = state_info["completion_percentage"]
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(progress / 100)
        with col2:
            st.markdown(f"**{progress}%**")

        st.markdown("### 💬 Conversation Info")
        state_display = state_info["state"].replace("_", " ").title()
        badge_class = "status-collecting"
        if "technical" in state_info["state"]:
            badge_class = "status-technical"
        elif "completed" in state_info["state"]:
            badge_class = "status-completed"
        st.markdown(
            f'<span class="status-badge {badge_class}">📍 {state_display}</span>',
            unsafe_allow_html=True,
        )


def get_image_as_base64(file):
    """Reads an image file and returns its Base64 encoded string."""
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


def render_chat_interface():
    """Render the main chat interface and handle message flow."""
    # Header
    logo_base64 = get_image_as_base64(logo_path / "bot.png")
    st.markdown(
        f"""
        <div style="display: flex; align-items: center;">
            <img src="data:image/png;base64,{logo_base64}" width="60">
            <h1 style="margin-left: 10px;">TalentScout Hiring Assistant</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "Welcome to our automated screening process! I'll guide you through a brief interview."
    )

    # Render existing messages
    for message in st.session_state.messages:
        role = message["role"]
        avatar_path = (
            logo_path / "assistant.png"
            if role == "assistant"
            else logo_path / "user.png"
        )
        avatar_base64 = get_image_as_base64(avatar_path)
        avatar_html = (
            f'<img src="data:image/png;base64,{avatar_base64}" width="48" height="48">'
        )
        bubble_class = "assistant" if role == "assistant" else "user"

        # Check if timestamp is a valid datetime object before formatting
        if isinstance(message["timestamp"], datetime):
            timestamp = message["timestamp"].strftime("%H:%M")
        else:
            timestamp = ""  # Fallback for any unexpected type

        st.markdown(
            f"""
            <div class="chat-row {bubble_class}">
                <div class="chat-avatar {bubble_class}">{avatar_html}</div>
                <div class="chat-bubble-container">
                    <div class="chat-bubble {bubble_class}">{message['content']}</div>
                    <div class="chat-timestamp">{timestamp}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Handle new input if screening is not completed
    state_info = st.session_state.conversation_manager.get_conversation_state()
    if state_info["state"] != "exit":
        # Use a flag to disable input while the assistant is generating a response
        input_disabled = st.session_state.get("needs_response", False)
        prompt = st.chat_input(
            "Type your response here...", key="chat_input", disabled=input_disabled
        )

        # If we need to generate a response (from a previous run)
        if st.session_state.get("needs_response"):
            st.session_state.needs_response = False  # Reset the flag
            user_prompt = st.session_state.messages[-1]["content"]
            logger.info(f"Generating response for user prompt: '{user_prompt[:50]}...'")

            with st.spinner("Thinking..."):
                response = st.session_state.conversation_manager.handle_message(
                    user_prompt
                )

            st.session_state.messages.append(
                {"role": "assistant", "content": response, "timestamp": datetime.now()}
            )
            st.rerun()

        # If new input was submitted
        elif prompt:
            logger.info(f"New user prompt received: '{prompt[:50]}...'")
            st.session_state.messages.append(
                {"role": "user", "content": prompt, "timestamp": datetime.now()}
            )
            st.session_state.needs_response = True
            st.rerun()

        # Footer
        st.markdown(
            """
            <div class="footer-note" style="position: fixed; bottom: 7rem; width: 100%; left: 0;">
                🔒 Your information is encrypted and securely stored | Built with ❤️ using Streamlit
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_completion_summary():
    """Render completion summary if screening is done."""
    state_info = st.session_state.conversation_manager.get_conversation_state()
    if state_info["state"] == "exit":
        logger.info("Rendering completion summary.")
        st.markdown(
            """
            <div class="footer-note" style="position: fixed; bottom: 2rem; width: 100%; left: 0;">
                🔒 Your information is encrypted and securely stored | Built with ❤️ using Streamlit
            </div>
            """,
            unsafe_allow_html=True,
        )


def main():
    """Main application function."""
    logger.info("Starting main application function.")
    setup_page_config()
    if not check_environment():
        st.stop()

    initialize_session_state()
    render_sidebar()
    render_chat_interface()
    render_completion_summary()
    logger.info("Application render cycle complete.")


if __name__ == "__main__":
    logger.remove()
    logger.add("app.log", rotation="10 MB", level="INFO")
    logger.add(sys.stderr, level="WARNING")
    logger.info("Starting TalentScout Hiring Assistant application.")
    try:
        main()
    except Exception as e:
        logger.exception("An unexpected error occurred in the main application.")
        st.error("An unexpected error occurred. Please refresh the page to try again.")
