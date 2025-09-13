# app.py

import streamlit as st
from helpers import init_profile, get_response
import datetime
import uuid

# --- Page Configuration ---
st.set_page_config(
    page_title="FinBot Pro",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Chat Bubbles and Background ---
st.markdown("""
<style>
    /* Professional Gradient Background */
    .stApp {
        background: linear-gradient(to right, #0a0e1a, #1a2238);
        color: #f0f2f6; /* Light gray text for contrast */
    }
    
    /* General app-wide text color for better readability on dark background */
    body {
        color: #f0f2f6;
    }

    /* --- Chat Bubbles (Updated) --- */
    .chat-container { 
        display: flex; 
        flex-direction: column; 
    }
    .chat-message { 
        padding: 1rem; 
        border-radius: 1rem; 
        margin-bottom: 1rem; 
        width: fit-content; 
        max-width: 80%;
    }
    .user-message { 
        background-color: #2b313e; 
        color: #ffffff; 
        float: right; /* Pushes the message to the right side */
        clear: both; /* Prevents overlap with previous messages */
    }
    .assistant-message { 
        background-color: #4e5563; 
        color: #ffffff; 
        float: left; /* Pushes the message to the left side */
        clear: both; /* Prevents overlap with previous messages */
    }

    /* Clearfix to ensure the container wraps around the floated elements */
    .st-emotion-cache-1c7y2n2 {
        display: flow-root;
    }
    
    /* Style for the feature buttons container */
    .features-container {
        padding: 1rem;
        border: 1px solid #4e5563;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Home page styles */
    .main-page {
        text-align: center;
        padding-top: 5rem;
        color: #f0f2f6; /* Ensures text is visible on the dark background */
    }
</style>
""", unsafe_allow_html=True)


# --- History Management Functions ---
def save_current_chat():
    """Saves the current chat to history if it's not empty."""
    if st.session_state.messages and len(st.session_state.messages) > 1: # Check for at least one user message
        title = st.session_state.messages[1]['content'][:50] + "..." if len(st.session_state.messages) > 1 else "New Chat"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        st.session_state.chat_history.append({
            "id": str(uuid.uuid4()),
            "title": title,
            "timestamp": timestamp,
            "messages": st.session_state.messages
        })
    # Reset chat
    st.session_state.messages = []
    st.session_state.profile = init_profile()
    st.session_state.messages.append(
        {"role": "assistant", "content": "Hello! 👋 I’m your Personal Finance Assistant. How can I help you today? Choose an option below or type your question."}
    )
    st.session_state.user_action = None

def navigate_to(page):
    """Sets the current page and handles saving the current chat."""
    if st.session_state.current_page == "chatbot" and page != "chatbot":
        save_current_chat()
    st.session_state.current_page = page
    st.rerun()

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []
    st.session_state["profile"] = init_profile()
    st.session_state["messages"].append(
        {"role": "assistant", "content": "Hello! 👋 I’m your Personal Finance Assistant. How can I help you today? Choose an option below or type your question."}
    )
if "user_action" not in st.session_state:
    st.session_state.user_action = None
if "show_home" not in st.session_state:
    st.session_state.show_home = True
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"


# --- Sidebar Content ---
with st.sidebar:
    st.title("FinBot Pro 🤖")
    st.markdown("Your intelligent assistant for mastering personal finance.")
    
    st.markdown("---")
    st.subheader("Navigation")
    if st.button("🏠 Home", use_container_width=True):
        navigate_to("home")
    if st.button("💬 Chatbot", use_container_width=True):
        navigate_to("chatbot")
    if st.button("📜 History", use_container_width=True):
        navigate_to("history")
    
    st.markdown("---")
    st.markdown("Built with ❤️ using [Streamlit](https://streamlit.io/)")


# --- Main Application Logic (Page Routing) ---
if st.session_state.current_page == "home":
    # Get current time to determine the greeting
    now = datetime.datetime.now()
    if now.hour < 12:
        greeting = "Good Morning"
    elif 12 <= now.hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"
        
    st.markdown(f"""
    <div class="main-page">
        <h1>{greeting}! Welcome to FinBot Pro 🤖</h1>
        <p>Your personal finance journey starts here. Let's get your money in order and work towards your goals.</p>
        <br>
        <p>Ready to get started?</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Let's Get Started", use_container_width=True):
        navigate_to("chatbot")


elif st.session_state.current_page == "chatbot":
    st.header("Your Personal Finance Chat")
    st.markdown("Let's manage your money and achieve your financial goals together!")
    st.divider()
    
    # --- Display "Back to Features" button if a conversation is active ---
    if st.session_state.profile.get("conversation_state"):
        if st.button("⬅️ Back to Features"):
            st.session_state.user_action = "back"
            st.rerun()

    # --- Display Feature Buttons for New Chats ---
    if len(st.session_state.messages) <= 1 or not st.session_state.profile.get("conversation_state"):
        with st.container():
            st.markdown("<div class='features-container'>", unsafe_allow_html=True)
            st.subheader("What would you like to do?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Create a Budget", use_container_width=True):
                    st.session_state.user_action = "Create a budget"
                    st.rerun()
                if st.button("🆘 Calculate Emergency Fund", use_container_width=True):
                    st.session_state.user_action = "Calculate my emergency fund"
                    st.rerun()
            with col2:
                if st.button("🎯 Set a Savings Goal", use_container_width=True):
                    st.session_state.user_action = "Set a savings goal"
                    st.rerun()
                if st.button("📈 Get Investment Advice", use_container_width=True):
                    st.session_state.user_action = "Give me investment advice"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # Display previous messages from session state
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><span>{msg["content"]}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><span>{msg["content"]}</span></div>', unsafe_allow_html=True)

    # --- User Input and Chat Logic ---
    user_input = st.chat_input("Ask me about your finances...")

    if st.session_state.user_action:
        user_input = st.session_state.user_action
        st.session_state.user_action = None # Reset it after use

    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        
        with st.spinner("Thinking..."):
            bot_reply = get_response(user_input, st.session_state["profile"])
            st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        
        st.rerun()


elif st.session_state.current_page == "history":
    st.header("Chat History 📜")
    st.markdown("Review all your past conversations with FinBot Pro.")
    st.divider()

    if not st.session_state.chat_history:
        st.info("No chat history available. Start a new conversation to save your history!")
    else:
        for chat in reversed(st.session_state.chat_history):
            with st.expander(f'**{chat["title"]}** - _{chat["timestamp"]}_'):
                for msg in chat["messages"]:
                    if msg["role"] == "user":
                        st.markdown(f'<div class="chat-message user-message"><span>{msg["content"]}</span></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-message assistant-message"><span>{msg["content"]}</span></div>', unsafe_allow_html=True)