
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from ai_beta_tester.personalities.chaos_gremlin import ChaosGremlinPersonality
from ai_beta_tester.personalities.technical_exploit import TechnicalExploitPersonality
from ai_beta_tester.personalities.speedrunner import SpeedrunnerPersonality

def verify_personality_tools(cls, expected_tools):
    print(f"Verifying {cls.name}...")
    agent_def = cls.to_agent_definition("Test Goal")
    found_tools = [t.name for t in (agent_def.tools or [])]
    
    missing = set(expected_tools) - set(found_tools)
    if missing:
        print(f"FAILED: Missing tools: {missing}")
        return False
    
    print(f"SUCCESS: Found tools: {found_tools}")
    return True

success = True
success &= verify_personality_tools(ChaosGremlinPersonality, ["input_fuzzer", "event_spammer"])
success &= verify_personality_tools(TechnicalExploitPersonality, ["dom_injector", "auth_token_manipulator"])
success &= verify_personality_tools(SpeedrunnerPersonality, ["interaction_latency_profiler"])

if not success:
    sys.exit(1)
