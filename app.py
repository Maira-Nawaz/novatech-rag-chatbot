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
)

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer     {visibility: hidden;}
    header     {visibility: hidden;}

    .chat-header {
        text-align: center;
        padding: 24px 0 12px 0;
        border-bottom: 2px solid #1A3C6E;
        margin-bottom: 20px;
    }
    .chat-header h1 { font-size: 1.7rem; font-weight: 700; margin: 0; color: #1A3C6E; }
    .chat-header p  { color: #6B7280; font-size: 0.9rem; margin: 4px 0 0 0; }
    .status-badge {
        display: inline-block;
        background: #d4edda; color: #155724;
        border-radius: 20px; padding: 2px 14px;
        font-size: 0.75rem; margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="chat-header">
    <h1>🤖 {COMPANY_NAME} — Document Assistant</h1>
    <p>Ask me anything about NovaTech Solutions — products, pricing, support, HR policies and more.</p>
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
            "Hi there! 👋 I'm the **NovaTech Solutions** document assistant. "
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

        # n8n AI Agent returns { "output": "..." }
        if isinstance(data, dict):
            return data.get("output", data.get("text", data.get("message", str(data))))
        return str(data)

    except requests.exceptions.Timeout:
        return "⏱ Request timed out. The AI is still processing — please try again."
    except requests.exceptions.ConnectionError:
        return "🔌 Could not connect to the backend. Please check the workflow is published and active."
    except requests.exceptions.HTTPError as e:
        return f"❌ Server error {e.response.status_code}. Check your n8n workflow logs."
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

# ─────────────────────────────────────────────
#  CHAT INPUT
# ─────────────────────────────────────────────
if prompt := st.chat_input("Ask a question about NovaTech Solutions..."):
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # Bot response
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Searching documents..."):
            reply = call_n8n(prompt, st.session_state.session_id)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Session Info")
    st.markdown("**Session ID**")
    st.code(st.session_state.session_id[:8] + "...", language=None)

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages   = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.divider()
    st.markdown("""
**💡 Try asking:**
- What is NovaCRM?
- How much does the Business plan cost?
- Is NovaTech GDPR compliant?
- How do I raise a support ticket?
- What is the annual leave policy?
- Do you offer a free trial?
    """)

    st.divider()
    st.markdown("""
**🔧 How it works**
1. Your question → **n8n AI Agent**
2. Cohere embeds the question
3. Pinecone finds relevant chunks
4. GPT-4o mini generates the answer
    """)
    st.caption("Built with n8n · Pinecone · Cohere · OpenAI · Streamlit")
