import streamlit as st
import requests
import uuid

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
N8N_WEBHOOK_URL = "https://codequill.app.n8n.cloud/webhook/rag-chatbot-webhook/chat"
COMPANY_NAME    = "NovaTech Solutions"
BOT_AVATAR      = "🤖"
USER_AVATAR     = "🧑"

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title=f"{COMPANY_NAME} — Document Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  FORCE LIGHT THEME + CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Force light background everywhere */
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="block-container"] {
        background-color: #F8FAFC !important;
        color: #1F2937 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB;
    }
    [data-testid="stSidebar"] * { color: #1F2937 !important; }

    /* Hide default chrome */
    #MainMenu {visibility: hidden;}
    footer     {visibility: hidden;}
    header     {visibility: hidden;}

    /* Header card */
    .chat-header {
        background: linear-gradient(135deg, #1A3C6E 0%, #2979FF 100%);
        border-radius: 16px;
        padding: 28px 24px 20px 24px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 4px 16px rgba(26,60,110,0.15);
    }
    .chat-header h1 {
        font-size: 1.7rem; font-weight: 800;
        color: #FFFFFF !important; margin: 0; letter-spacing: -0.3px;
    }
    .chat-header p {
        color: rgba(255,255,255,0.82) !important;
        font-size: 0.9rem; margin: 6px 0 0 0;
    }
    .status-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,0.4);
        border-radius: 20px; padding: 3px 14px;
        font-size: 0.75rem; margin-top: 10px;
    }

    /* Chat messages — light bubbles */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB;
        border-radius: 12px !important;
        margin-bottom: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    [data-testid="stChatMessage"] * { color: #1F2937 !important; }

    /* Chat input */
    [data-testid="stChatInput"] {
        background-color: #FFFFFF !important;
        border: 2px solid #2979FF !important;
        border-radius: 12px !important;
        color: #1F2937 !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #1F2937 !important;
        background-color: #FFFFFF !important;
    }

    /* Spinner */
    [data-testid="stSpinner"] * { color: #2979FF !important; }

    /* Buttons */
    .stButton > button {
        background-color: #1A3C6E !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #2979FF !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="chat-header">
    <h1>🤖 {COMPANY_NAME}</h1>
    <p>Your AI-powered guide to NovaTech products, policies, and support.</p>
    <span class="status-badge">● Online</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
if "messages"   not in st.session_state:
    st.session_state.messages   = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ─────────────────────────────────────────────
#  DISPLAY HISTORY
# ─────────────────────────────────────────────
for msg in st.session_state.messages:
    avatar = BOT_AVATAR if msg["role"] == "assistant" else USER_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ─────────────────────────────────────────────
#  WELCOME MESSAGE
# ─────────────────────────────────────────────
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        st.markdown(
            "Hi there! 👋 I'm the **NovaTech Solutions** Company assistant. "
            "I can answer questions about our products, pricing, support, and HR policies. "
            "What would you like to know?"
        )

# ─────────────────────────────────────────────
#  CALL n8n WEBHOOK
# ─────────────────────────────────────────────
def call_n8n(user_message: str, session_id: str) -> str:
    payload = {
        "chatInput": user_message,
        "sessionId": session_id,
        "action":    "sendMessage",
    }
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=60,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            return data.get("output", data.get("text", data.get("message", str(data))))
        elif isinstance(data, list) and len(data) > 0:
            item = data[0]
            if isinstance(item, dict):
                return item.get("output", item.get("text", str(item)))
        return str(data)

    except requests.exceptions.Timeout:
        return "⏱ Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "🔌 Cannot connect to backend. Check if the workflow is published."
    except requests.exceptions.HTTPError as e:
        return f"❌ HTTP {e.response.status_code} error. Check your n8n workflow logs."
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

# ─────────────────────────────────────────────
#  CHAT INPUT
# ─────────────────────────────────────────────
if prompt := st.chat_input("Ask a question about NovaTech Solutions..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Searching documents..."):
            reply = call_n8n(prompt, st.session_state.session_id)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 NovaTech Assistant")
    st.markdown("Powered by RAG + AI")
    st.divider()

    st.markdown("**Session ID**")
    st.code(st.session_state.session_id[:8] + "...", language=None)

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages   = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.divider()
    st.markdown("**💡 Try asking:**")
    questions = [
        "What is NovaCRM?",
        "Business plan pricing?",
        "Is NovaTech GDPR compliant?",
        "How to raise a support ticket?",
        "Annual leave policy?",
        "Is there a free trial?",
    ]
    for q in questions:
        st.markdown(f"• {q}")

    st.divider()
    st.markdown("**🔧 How it works**")
    st.markdown("""
1. Question → **n8n AI Agent**
2. Cohere embeds it
3. Pinecone finds chunks
4. GPT-4o mini answers
    """)
    st.caption("n8n · Pinecone · Cohere · OpenAI · Streamlit")
