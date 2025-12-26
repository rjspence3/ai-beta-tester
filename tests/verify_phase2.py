
import sys

try:
    from ai_beta_tester.personalities.privacy_paranoid import PrivacyParanoid
    from ai_beta_tester.personalities.overloaded_manager import OverloadedManager
    from ai_beta_tester.personalities.hybrid_auditor import HybridAuditor
    
    print("PrivacyParanoid Prompt Preview:")
    print(PrivacyParanoid.get_system_prompt("TEST")[:100] + "...")

    print("OverloadedManager Prompt Preview:")
    print(OverloadedManager.get_system_prompt("TEST")[:100] + "...")

    print("HybridAuditor Prompt Preview:")
    print(HybridAuditor.get_system_prompt("TEST")[:100] + "...")

    print("\nSUCCESS: All personalities imported and generated prompts.")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
