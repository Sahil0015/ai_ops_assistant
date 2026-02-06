"""
Multi-Agent AI System using Agno Framework.

This system uses four specialized agents in a sequential pipeline:
  1. Planner Agent   - Analyzes the query and creates an execution plan.
  2. Executor Agent  - Executes the plan using tools (weather, news, GitHub).
  3. Verifier Agent  - Reviews the response for quality and completeness.
  4. Responder Agent - Formats a polished final response for the user.

Pipeline: User Query -> Planner -> Executor -> Verifier (with retry) -> Responder -> Final Response

The Verifier checks if the response passes quality criteria. If it fails,
the Executor retries up to 2 times before passing to the Responder.

Run: streamlit run main.py
"""

import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agents.planner_agent import create_planner_agent
from agents.executor_agent import create_executor_agent
from agents.verifier_agent import create_verifier_agent
from agents.responder_agent import create_responder_agent

MAX_RETRIES = 2  # Maximum retry attempts for Executor when verification fails


# ── Streamlit UI ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Multi-Agent AI System",
    page_icon="🤖",
    layout="wide",
)

# ── Header ──
st.title("🤖 Multi-Agent AI System")
st.caption("Powered by **Agno Framework** + **Groq (LLaMA 3.3 70B)**")

# Pipeline diagram
cols = st.columns([1, 0.2, 1, 0.2, 1, 0.2, 1])
with cols[0]:
    st.info("📋 **Planner**\n\nCreates plan")
with cols[1]:
    st.markdown("<div style='text-align:center; padding-top:25px; font-size:20px'>→</div>", unsafe_allow_html=True)
with cols[2]:
    st.success("⚡ **Executor**\n\nRuns tools")
with cols[3]:
    st.markdown("<div style='text-align:center; padding-top:25px; font-size:20px'>→</div>", unsafe_allow_html=True)
with cols[4]:
    st.warning("🔍 **Verifier**\n\nChecks quality")
with cols[5]:
    st.markdown("<div style='text-align:center; padding-top:25px; font-size:20px'>→</div>", unsafe_allow_html=True)
with cols[6]:
    st.error("💬 **Responder**\n\nFinal answer")

st.divider()

# ── Initialize session state ──
if "query_input" not in st.session_state:
    st.session_state["query_input"] = ""
if "run_query" not in st.session_state:
    st.session_state["run_query"] = False

# ── Sidebar ──
with st.sidebar:
    st.header("🔧 Tools Available")
    st.markdown("""
    | Tool | Description |
    |------|-------------|
    | 🌤️ Weather | Current weather for any city |
    | 📰 News | Latest news on any topic |
    | 🐙 GitHub | User profiles, repositories |
    """)

    st.divider()
    st.header("💡 Example Queries")
    st.caption("Click to run automatically")
    examples = [
        "Tell me about GitHub user torvalds",
        "Get info about the facebook/react repository",
        "Search for machine learning repos on GitHub",
        "What's the weather in Tokyo?",
        "Get me the latest AI news",
        "Weather in New York and latest tech news",
        "News on AI startups and trending AI repos on GitHub",
    ]

    for ex in examples:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state["query_input"] = ex
            st.session_state["run_query"] = True
            st.rerun()

# ── Init agents once (cached in session state) ──
if "agents_ready" not in st.session_state:
    st.session_state["agents_ready"] = False

if not st.session_state["agents_ready"]:
    try:
        st.session_state["planner"] = create_planner_agent()
        st.session_state["executor"] = create_executor_agent()
        st.session_state["verifier"] = create_verifier_agent()
        st.session_state["responder"] = create_responder_agent()
        st.session_state["agents_ready"] = True
    except Exception as e:
        st.error(f"Failed to initialize agents: {e}")
        st.stop()

# ── Query input ──
query = st.text_input(
    "Enter your query:",
    value=st.session_state.get("query_input", ""),
    placeholder="e.g. What's the weather in London and latest news about AI?",
    key="query_box",
)

run_btn = st.button("🚀 Run Pipeline", type="primary", use_container_width=True)

# Check if we should auto-run from example click
should_run = run_btn or st.session_state.get("run_query", False)
if st.session_state.get("run_query", False):
    st.session_state["run_query"] = False
    query = st.session_state.get("query_input", "")

if should_run and query:
    st.divider()

    planner = st.session_state["planner"]
    executor = st.session_state["executor"]
    verifier = st.session_state["verifier"]
    responder = st.session_state["responder"]

    # ── Step 1: Planner ──
    with st.status("📋 Step 1/4 — Planner Agent analyzing query...", expanded=True) as status:
        start = time.time()
        try:
            planner_response = planner.run(query)
            plan = planner_response.content
            raw_planner = planner_response
            elapsed = time.time() - start
            status.update(label=f"📋 Step 1/4 — Planner Agent ({elapsed:.1f}s)", state="complete")
            st.markdown(plan)
            with st.expander("🔍 View Raw Planner Output", expanded=False):
                st.code(repr(raw_planner), language="python")
        except Exception as e:
            status.update(label="📋 Step 1/4 — Planner Agent (FAILED)", state="error")
            st.error(f"Planner error: {e}")
            st.stop()

    # ── Step 2 & 3: Executor + Verifier with retry loop ──
    verification_passed = False
    retry_count = 0
    
    for attempt in range(MAX_RETRIES + 1):
        retry_count = attempt
        retry_label = f" (Retry {attempt})" if attempt > 0 else ""
        
        # ── Step 2: Executor ──
        with st.status(f"⚡ Step 2/4 — Executor Agent executing plan...{retry_label}", expanded=True) as status:
            start = time.time()
            try:
                executor_input = (
                    f"User Query: {query}\n\n"
                    f"Execution Plan:\n{plan}\n\n"
                    f"Execute the above plan using the available tools and provide a comprehensive response."
                )
                if attempt > 0:
                    executor_input += f"\n\nNote: Previous attempt failed verification. This is retry attempt {attempt}. Please address any issues and provide a better response."
                
                executor_response = executor.run(executor_input)
                result = executor_response.content
                raw_executor = executor_response
                elapsed = time.time() - start
                status.update(label=f"⚡ Step 2/4 — Executor Agent ({elapsed:.1f}s){retry_label}", state="complete")
                st.markdown(result)
                with st.expander("🔍 View Raw Executor Output", expanded=False):
                    st.code(repr(raw_executor), language="python")
            except Exception as e:
                status.update(label=f"⚡ Step 2/4 — Executor Agent (FAILED){retry_label}", state="error")
                st.error(f"Executor error: {e}")
                st.stop()

        # ── Step 3: Verifier ──
        with st.status(f"🔍 Step 3/4 — Verifier Agent reviewing response...{retry_label}", expanded=True) as status:
            start = time.time()
            try:
                verifier_input = (
                    f"Original User Query: {query}\n\n"
                    f"Executor's Response:\n{result}\n\n"
                    f"Please verify the response quality and completeness."
                )
                verifier_response = verifier.run(verifier_input)
                verification = verifier_response.content
                raw_verifier = verifier_response
                elapsed = time.time() - start
                
                # Check if verification passed (flexible matching)
                verification_lower = verification.lower()
                if "overall: pass" in verification_lower or "overall:pass" in verification_lower or ("overall" in verification_lower and "pass" in verification_lower.split("overall")[-1][:20]):
                    verification_passed = True
                    status.update(label=f"🔍 Step 3/4 — Verifier Agent ({elapsed:.1f}s) ✅ PASS", state="complete")
                else:
                    status.update(label=f"🔍 Step 3/4 — Verifier Agent ({elapsed:.1f}s) ❌ FAIL", state="complete")
                
                st.markdown(verification)
                with st.expander("🔍 View Raw Verifier Output", expanded=False):
                    st.code(repr(raw_verifier), language="python")
            except Exception as e:
                status.update(label=f"🔍 Step 3/4 — Verifier Agent (FAILED){retry_label}", state="error")
                st.error(f"Verifier error: {e}")
                st.stop()

        # If passed or max retries reached, break out of loop
        if verification_passed:
            break
        elif attempt < MAX_RETRIES:
            st.warning(f"⚠️ Verification failed. Retrying... (Attempt {attempt + 2}/{MAX_RETRIES + 1})")
        else:
            st.warning(f"⚠️ Maximum retries ({MAX_RETRIES}) reached. Proceeding to Responder Agent.")

    # ── Step 4: Responder ──
    with st.status("💬 Step 4/4 — Responder Agent formatting final response...", expanded=True) as status:
        start = time.time()
        try:
            responder_input = (
                f"Original User Query: {query}\n\n"
                f"Verified Response:\n{result}\n\n"
                f"Verification Notes:\n{verification}\n\n"
                f"Please provide a polished, user-friendly final response."
            )
            responder_response = responder.run(responder_input)
            final_response = responder_response.content
            raw_responder = responder_response
            elapsed = time.time() - start
            status.update(label=f"💬 Step 4/4 — Responder Agent ({elapsed:.1f}s)", state="complete")
            st.markdown(final_response)
            with st.expander("🔍 View Raw Responder Output", expanded=False):
                st.code(repr(raw_responder), language="python")
        except Exception as e:
            status.update(label="💬 Step 4/4 — Responder Agent (FAILED)", state="error")
            st.error(f"Responder error: {e}")
            st.stop()

    # ── Final Response ──
    st.divider()
    st.subheader("🎯 Final Response")
    if retry_count > 0:
        st.caption(f"ℹ️ Required {retry_count} retry(ies) before verification passed." if verification_passed else f"ℹ️ Required {retry_count} retry(ies). Max retries reached.")
    st.markdown(final_response)

elif should_run and not query:
    st.warning("Please enter a query first.")
