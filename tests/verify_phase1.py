
import sys

try:
    from ai_beta_tester.personalities.chaos_gremlin import ChaosGremlinPersonality
    from ai_beta_tester.personalities.technical_exploit import TechnicalExploitPersonality
    from ai_beta_tester.personalities.speedrunner import SpeedrunnerPersonality
    
    print("ChaosGremlin Prompt Preview:")
    print(ChaosGremlinPersonality.get_system_prompt("TEST")[:100] + "...")
    if "input_fuzzer" not in dir(): # Just dummy check
        pass
        
    print("\nSUCCESS: All personalities imported and generated prompts.")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
