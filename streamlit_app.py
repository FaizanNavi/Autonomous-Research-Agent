import streamlit as st
import requests

st.set_page_config(page_title="Autonomous Research Agent", page_icon="🔬", layout="wide")

st.title("🔬 Autonomous Research Agent")
st.markdown(
    "Give it a topic → 5 agents (**Planner → Search → Summarizer → Critic → Synthesizer**) "
    "with a **reflection loop** produce a verified research report."
)

BACKEND = "http://127.0.0.1:8003"

# Sidebar info
with st.sidebar:
    st.header("🔄 How the Reflection Loop Works")
    st.markdown("""
1. **Planner** breaks topic into 5 sub-questions
2. **Search** queries DuckDuckGo for each
3. **Summarizer** compresses findings
4. **Critic** scores the research (1-10)
    - ✅ Score high → move to Synthesizer
    - ❌ Gaps found → send back to Planner
5. Repeat up to **3 cycles**
6. **Synthesizer** writes the final report
    """)
    st.divider()

    st.header("📚 Example Topics")
    examples = [
        "Impact of AI on job markets in 2025",
        "Climate change policies in Southeast Asia",
        "Quantum computing breakthroughs 2024",
        "Microplastics in ocean ecosystems",
        "Central bank digital currencies adoption",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=ex):
            st.session_state.prefill = ex

# Main research area
if "messages" not in st.session_state:
    st.session_state.messages = []
if "prefill" not in st.session_state:
    st.session_state.prefill = ""

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Enter a research topic...")

# Handle prefill from sidebar buttons
if st.session_state.prefill and not prompt:
    prompt = st.session_state.prefill
    st.session_state.prefill = ""

if prompt:
    st.chat_message("user").markdown(f"**Research Topic:** {prompt}")
    st.session_state.messages.append({"role": "user", "content": f"**Research Topic:** {prompt}"})

    try:
        with st.spinner("🔍 Researching... (this takes 30-90 seconds depending on reflection cycles)"):
            res = requests.post(
                f"{BACKEND}/research",
                json={"topic": prompt},
                timeout=180
            )

        if res.status_code == 200:
            data = res.json()
            report = data.get("report", "No report generated.")
            iterations = data.get("iterations", 0)
            critic_score = data.get("critic_score")
            status = data.get("status", "complete")

            with st.chat_message("assistant"):
                st.markdown(report)
                with st.expander("🤖 Agent Metadata"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Reflection Cycles", iterations)
                    col2.metric("Critic Quality Score", f"{critic_score}/10" if critic_score else "N/A")
                    col3.metric("Final Status", status)

            st.session_state.messages.append({"role": "assistant", "content": report})
        else:
            st.error(f"Backend error {res.status_code}: {res.text}")

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Is `uvicorn app.main:app --port 8003` running?")
    except requests.exceptions.Timeout:
        st.error("Request timed out (180s). The research loop may still be running — try again with a simpler topic.")
    except Exception as e:
        st.error(f"Error: {e}")
