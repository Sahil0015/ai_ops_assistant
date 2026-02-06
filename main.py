"""
Multi-Agent AI System using Agno Framework.

This system uses four specialized agents in a sequential pipeline:
  1. Planner Agent   - Analyzes the query and creates an execution plan.
  2. Executor Agent  - Executes the plan using tools (weather, news, GitHub).
  3. Verifier Agent  - Reviews the response for quality and completeness.
  4. Responder Agent - Formats a polished final response for the user.

Pipeline: User Query -> Planner -> Executor -> Verifier (with retry) -> Final Response

Run: streamlit run main.py
"""

import json
import re
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agents.planner_agent import create_planner_agent
from agents.executor_agent import create_executor_agent
from agents.verifier_agent import create_verifier_agent
from agents.responder_agent import create_responder_agent
from tools.cache_manager import cache_manager
from llm.cost_tracker import cost_tracker

MAX_RETRIES = 2


# ── Helper Functions ─────────────────────────────────────────────────────────

def extract_json(text: str) -> dict | None:
    """Extract JSON from LLM response (handles markdown code blocks)."""
    patterns = [r"```json\s*([\s\S]*?)\s*```", r"```\s*([\s\S]*?)\s*```", r"(\{[\s\S]*\})"]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    return None


def format_plan(plan_json: dict) -> str:
    """Format planner JSON output as markdown."""
    if not isinstance(plan_json, dict):
        return str(plan_json)
    lines = []
    # Handle query_analysis (can be string or dict)
    qa = plan_json.get("query_analysis")
    if qa:
        lines.append("**Query Analysis:**")
        if isinstance(qa, str):
            lines.append(f"{qa}")
        elif isinstance(qa, dict):
            lines.append(f"- Intent: {qa.get('intent', 'N/A')}")
        lines.append("")
    # Handle steps
    steps = plan_json.get("steps", [])
    if steps:
        lines.append("**Execution Steps:**")
        for step in steps:
            if not isinstance(step, dict):
                continue
            num = step.get('step_number', step.get('step', '?'))
            desc = step.get('description', step.get('action', 'Unknown'))
            tool = step.get('tool', 'N/A')
            params = step.get('parameters', step.get('input', {}))
            lines.append(f"{num}. **{desc}**")
            lines.append(f"   - Tool: `{tool}`")
            if isinstance(params, dict) and params:
                lines.append(f"   - Params: {params}")
    return "\n".join(lines) if lines else str(plan_json)


def parse_verification(text: str) -> tuple[bool, dict]:
    """Parse verifier output. Returns (passed, verification_dict)."""
    data = extract_json(text)
    if data and isinstance(data, dict):
        # Check for overall pass in various formats
        overall = data.get("overall", "")
        if isinstance(overall, str) and "pass" in overall.lower():
            return True, data
        if isinstance(overall, bool) and overall:
            return True, data
        # Check verification sub-object
        v = data.get("verification", {})
        if isinstance(v, dict):
            for key, val in v.items():
                if isinstance(val, dict) and val.get("status", "").upper() == "FAIL":
                    return False, data
            return True, data
    # Fallback: text-based parsing
    text_lower = text.lower()
    passed = "overall" in text_lower and "pass" in text_lower and "fail" not in text_lower.split("overall")[-1][:30]
    return passed, {"raw": text}


def format_verification(v_data: dict) -> str:
    """Format verification JSON as markdown."""
    if not isinstance(v_data, dict):
        return str(v_data)
    if "raw" in v_data:
        return v_data["raw"]
    v = v_data.get("verification", v_data)
    if not isinstance(v, dict):
        return str(v_data)
    lines = ["**Verification Results:**"]
    for key, val in v.items():
        if isinstance(val, dict):
            status = "✅" if val.get("status", "").upper() == "PASS" else "❌"
            reason = val.get("reason", "")
            lines.append(f"- {key.replace('_', ' ').title()}: {status} {reason}")
    overall = v_data.get("overall", "")
    if overall:
        lines.append(f"\n**Overall:** {'✅ PASS' if 'pass' in str(overall).lower() else '❌ FAIL'}")
    suggestions = v_data.get("suggestions", [])
    if suggestions:
        lines.append(f"\n**Suggestions:** {', '.join(suggestions)}")
    return "\n".join(lines)


def run_with_retry(agent, prompt: str, max_attempts: int = 3, parse_json: bool = False):
    """Run agent with retry on failure. Returns (content, raw_response, error)."""
    for attempt in range(max_attempts):
        try:
            response = agent.run(prompt)
            content = response.content
            if parse_json:
                data = extract_json(content)
                if data:
                    return data, response, None
            return content, response, None
        except Exception as e:
            if attempt == max_attempts - 1:
                return None, None, str(e)
            time.sleep(0.5 * (attempt + 1))
    return None, None, "Max retries exceeded"


def get_partial_data(executor_result: str, query: str) -> str:
    """Graceful fallback: return partial data with warning if verification fails."""
    return (
        f"⚠️ **Note:** Some data may be incomplete or could not be fully verified.\n\n"
        f"**Available Information:**\n{executor_result}\n\n"
        f"*Based on query: {query}*"
    )


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough: 1 token ≈ 4 characters)."""
    return len(text) // 4


def track_agent_cost(agent_name: str, prompt: str, response: str, model: str = "llama-3.3-70b-versatile"):
    """Estimate and track cost for an agent call."""
    input_tokens = estimate_tokens(prompt)
    output_tokens = estimate_tokens(response)
    cost_tracker.track(agent_name, model, input_tokens, output_tokens)


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
    
    # Cache Stats
    st.header("💾 Cache Statistics")
    cache_stats = cache_manager.get_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Cache Size", cache_stats["size"])
        st.metric("Hit Rate", f"{cache_stats['hit_rate']:.1f}%")
    with col2:
        st.metric("Hits", cache_stats["hits"])
        st.metric("Misses", cache_stats["misses"])
    
    if st.button("🗑️ Clear Cache", use_container_width=True):
        cache_manager.clear()
        st.success("Cache cleared!")
        st.rerun()
    
    st.divider()
    
    # Cost Tracking
    st.header("💰 Cost Tracking")
    session_cost = cost_tracker.get_session_cost()
    session_tokens = cost_tracker.get_session_tokens()
    st.metric("Session Cost", f"${session_cost:.6f}")
    st.metric("Session Tokens", f"{session_tokens:,}")
    
    with st.expander("💵 Agent Breakdown", expanded=False):
        breakdown = cost_tracker.get_agent_breakdown()
        for agent, data in breakdown.items():
            if data["calls"] > 0:
                st.text(f"{agent}:")
                st.text(f"  Calls: {data['calls']}")
                st.text(f"  Tokens: {data['input_tokens'] + data['output_tokens']:,}")
                st.text(f"  Cost: ${data['cost']:.6f}")
    
    if st.button("🔄 Reset Session", use_container_width=True):
        cost_tracker.reset_session()
        st.success("Session reset!")
        st.rerun()

    st.divider()
    st.header("💡 Example Queries")
    st.caption("Click to run automatically")
    examples = [
        "Tell me about GitHub user @Sahil0015",
        "Tell me about the GitHub Repo https://github.com/Sahil0015/ai_ops_assistant",
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
            plan_raw = planner_response.content
            plan_json = extract_json(plan_raw)
            plan_display = format_plan(plan_json) if plan_json else plan_raw
            plan = plan_raw  # Keep raw for executor
            
            # Track cost
            track_agent_cost("Planner Agent", query, plan_raw)
            
            elapsed = time.time() - start
            status.update(label=f"📋 Step 1/4 — Planner Agent ({elapsed:.1f}s)", state="complete")
            st.markdown(plan_display)
            with st.expander("🔍 View Raw Planner Output", expanded=False):
                st.code(plan_raw, language="json" if plan_json else "text")
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
                
                # Track cost
                track_agent_cost("Executor Agent", executor_input, result, "qwen/qwen3-32b")
                
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
                verification_raw = verifier_response.content
                verification_passed, v_data = parse_verification(verification_raw)
                verification_display = format_verification(v_data)
                
                # Track cost
                track_agent_cost("Verifier Agent", verifier_input, verification_raw)
                
                elapsed = time.time() - start
                
                if verification_passed:
                    status.update(label=f"🔍 Step 3/4 — Verifier Agent ({elapsed:.1f}s) ✅ PASS", state="complete")
                else:
                    status.update(label=f"🔍 Step 3/4 — Verifier Agent ({elapsed:.1f}s) ❌ FAIL", state="complete")
                
                st.markdown(verification_display)
                with st.expander("🔍 View Raw Verifier Output", expanded=False):
                    st.code(verification_raw, language="json" if "verification" in v_data else "text")
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
            st.warning(f"⚠️ Maximum retries ({MAX_RETRIES}) reached. Using partial data fallback.")

    # ── Step 4: Responder ──
    with st.status("💬 Step 4/4 — Responder Agent formatting final response...", expanded=True) as status:
        start = time.time()
        try:
            # Use partial data fallback if verification failed after all retries
            if not verification_passed:
                result_for_responder = get_partial_data(result, query)
            else:
                result_for_responder = result
            
            responder_input = (
                f"Original User Query: {query}\n\n"
                f"Response:\n{result_for_responder}\n\n"
                f"Verification: {'PASSED' if verification_passed else 'PARTIAL DATA'}\n\n"
                f"Please provide a polished, user-friendly final response."
            )
            responder_response = responder.run(responder_input)
            final_response = responder_response.content
            
            # Track cost
            track_agent_cost("Responder Agent", responder_input, final_response)
            
            elapsed = time.time() - start
            status.update(label=f"💬 Step 4/4 — Responder Agent ({elapsed:.1f}s)", state="complete")
            st.markdown(final_response)
            with st.expander("🔍 View Raw Responder Output", expanded=False):
                st.code(responder_response.content, language="text")
        except Exception as e:
            status.update(label="💬 Step 4/4 — Responder Agent (FAILED)", state="error")
            st.error(f"Responder error: {e}")
            # Graceful fallback: show partial data directly
            final_response = get_partial_data(result, query)
            st.markdown(final_response)

    # ── Final Response ──
    st.divider()
    st.subheader("🎯 Final Response")
    if not verification_passed:
        st.caption("⚠️ Response includes partial data that could not be fully verified.")
    elif retry_count > 0:
        st.caption(f"ℹ️ Required {retry_count} retry(ies) before verification passed.")
    st.markdown(final_response)

elif should_run and not query:
    st.warning("Please enter a query first.")
