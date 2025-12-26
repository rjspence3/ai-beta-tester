import pytest
from types import SimpleNamespace
from ai_beta_tester.personalities import (
    CalmOperator,
    OverloadedManager,
    MethodicalNewcomer,
    PrivacyParanoid,
    AdhdFounder
)

def test_calm_operator_behavior():
    """Test Calm Operator's patience and low override tendency."""
    agent = CalmOperator()
    context = SimpleNamespace(stuck_count=0)
    
    # Assertion 1: Should not override normally
    assert agent.should_override(context) is False
    
    # Assertion 2: Only overrides when significantly stuck
    context.stuck_count = 6
    assert agent.should_override(context) is True

def test_overloaded_manager_behavior():
    """Test Overloaded Manager's impatience."""
    agent = OverloadedManager()
    context = SimpleNamespace(action_count=0, confusion_level=0)
    
    # Assertion 1: Should not override initially
    assert agent.should_override(context) is False
    
    # Assertion 2: Overrides if too many actions taken
    context.action_count = 6
    assert agent.should_override(context) is True
    
    # Assertion 3: Overrides if confusion is high
    context.action_count = 0
    context.confusion_level = 3
    assert agent.should_override(context) is True

def test_methodical_newcomer_behavior():
    """Test Methodical Newcomer's reliance on help."""
    agent = MethodicalNewcomer()
    context = SimpleNamespace(help_visible=False, help_opened=False)
    
    # Assertion 1: Should not check help if not visible
    assert agent.should_open_help(context) is False
    
    # Assertion 2: Should check help if visible and not yet opened
    context.help_visible = True
    assert agent.should_open_help(context) is True
    
    # Assertion 3: Should not open help if already opened
    context.help_opened = True
    assert agent.should_open_help(context) is False
    
    # Assertion 4: Should never override
    assert agent.should_override(context) is False

def test_privacy_paranoid_behavior():
    """Test Privacy Paranoid's trust verification."""
    agent = PrivacyParanoid()
    context = SimpleNamespace(privacy_checked=False, privacy_link_visible=False, unexplained_data=False, privacy_policy_found=False)
    
    # Assertion 1: Should not check privacy if not visible
    assert agent.should_check_privacy(context) is False
    
    # Assertion 2: Checks privacy link if visible
    context.privacy_link_visible = True
    assert agent.should_check_privacy(context) is True
    
    # Assertion 3: Stops checking once checked
    context.privacy_checked = True
    assert agent.should_check_privacy(context) is False
    
    # Assertion 4: Trust evaluation logic
    context.unexplained_data = True
    assert agent.evaluate_trust(context) == 1
    
    context.unexplained_data = False
    context.privacy_policy_found = True
    assert agent.evaluate_trust(context) == 4

def test_adhd_founder_behavior():
    """Test ADHD Founder's switching and boredom."""
    agent = AdhdFounder()
    context = SimpleNamespace(shiny_feature_visible=False, boredom_level=0)
    
    # Assertion 1: Switches context if shiny feature visible
    assert agent.should_switch_context(context) is False
    context.shiny_feature_visible = True
    assert agent.should_switch_context(context) is True
    
    # Assertion 2: Overrides if bored
    assert agent.should_override(context) is False
    context.boredom_level = 4
    assert agent.should_override(context) is True
