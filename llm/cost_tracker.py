"""
Cost Tracker for LLM API usage.
Tracks token usage and calculates costs for Groq models.
"""

import time
import json
from pathlib import Path
from typing import Dict


class CostTracker:
    """Track token usage and costs for Groq API calls."""
    
    # Groq pricing (as of Feb 2026) - dollars per 1M tokens
    PRICING = {
        "llama-3.3-70b-versatile": {
            "input": 0.59,
            "output": 0.79
        },
        "qwen/qwen3-32b": {
            "input": 0.35,
            "output": 0.44
        },
        "llama3-70b-8192": {
            "input": 0.59,
            "output": 0.79
        },
        "default": {
            "input": 0.50,
            "output": 0.70
        }
    }
    
    def __init__(self):
        self.sessions = []
        self.current_session = {
            "start_time": time.time(),
            "agents": {
                "Planner Agent": {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "calls": 0},
                "Executor Agent": {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "calls": 0},
                "Verifier Agent": {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "calls": 0},
                "Responder Agent": {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "calls": 0}
            },
            "total_cost": 0.0
        }
        self.total_lifetime_cost = 0.0
    
    def track(self, agent_name: str, model: str, input_tokens: int, output_tokens: int):
        """
        Track token usage for an agent.
        
        Args:
            agent_name: Name of the agent (e.g., "Planner Agent")
            model: Model identifier (e.g., "llama-3.3-70b-versatile")
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
        """
        # Get pricing for this model
        pricing = self.PRICING.get(model, self.PRICING["default"])
        
        # Calculate cost (pricing is per 1M tokens)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Update session data
        if agent_name in self.current_session["agents"]:
            agent_data = self.current_session["agents"][agent_name]
            agent_data["input_tokens"] += input_tokens
            agent_data["output_tokens"] += output_tokens
            agent_data["cost"] += total_cost
            agent_data["calls"] += 1
        
        self.current_session["total_cost"] += total_cost
        self.total_lifetime_cost += total_cost
    
    def get_session_cost(self) -> float:
        """Get total cost for current session."""
        return self.current_session["total_cost"]
    
    def get_session_tokens(self) -> int:
        """Get total tokens used in current session."""
        total = 0
        for agent_data in self.current_session["agents"].values():
            total += agent_data["input_tokens"] + agent_data["output_tokens"]
        return total
    
    def get_agent_breakdown(self) -> Dict:
        """Get detailed breakdown by agent."""
        return self.current_session["agents"].copy()
    
    def reset_session(self):
        """Start a new session (saves current session to history)."""
        if self.current_session["total_cost"] > 0:
            self.current_session["end_time"] = time.time()
            self.sessions.append(self.current_session.copy())
        
        self.current_session = {
            "start_time": time.time(),
            "agents": {
                "Planner Agent": {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "calls": 0},
                "Executor Agent": {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "calls": 0},
                "Verifier Agent": {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "calls": 0},
                "Responder Agent": {"input_tokens": 0, "output_tokens": 0, "cost": 0.0, "calls": 0}
            },
            "total_cost": 0.0
        }
    
    def get_stats(self) -> Dict:
        """Get comprehensive statistics."""
        return {
            "current_session": {
                "cost": self.current_session["total_cost"],
                "tokens": self.get_session_tokens(),
                "agents": self.current_session["agents"]
            },
            "lifetime": {
                "total_cost": self.total_lifetime_cost,
                "total_sessions": len(self.sessions) + (1 if self.current_session["total_cost"] > 0 else 0)
            }
        }
    
    def save_to_file(self, filepath: str = "cost_log.json"):
        """Save tracking data to file."""
        data = {
            "sessions": self.sessions,
            "current_session": self.current_session,
            "lifetime_cost": self.total_lifetime_cost
        }
        Path(filepath).write_text(json.dumps(data, indent=2))
    
    def load_from_file(self, filepath: str = "cost_log.json"):
        """Load tracking data from file."""
        if Path(filepath).exists():
            data = json.loads(Path(filepath).read_text())
            self.sessions = data.get("sessions", [])
            self.current_session = data.get("current_session", self.current_session)
            self.total_lifetime_cost = data.get("lifetime_cost", 0.0)


# Global cost tracker instance
cost_tracker = CostTracker()
