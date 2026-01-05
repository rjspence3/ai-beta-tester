"""Score calculation logic."""

from ai_beta_tester.models.agent_run import AgentRun
from ai_beta_tester.models.finding import FindingCategory
from ai_beta_tester.models.rubric import RubricScore, CognitiveLoad
from ai_beta_tester.scoring.categories import ScoringCategory, CATEGORY_WEIGHTS
from ai_beta_tester.scoring.penalties import FINDING_PENALTIES, GATING_CONDITIONS

def calculate_agent_score(run: AgentRun) -> RubricScore:
    """Calculate the rubric score for an agent run."""
    
    # Initialize category scores to 100
    category_scores = {cat: 100 for cat in CATEGORY_WEIGHTS}
    
    gating_failures = []
    
    # Track penalty counts for diminishing returns
    # Key: (Category, Title/Type) -> Count
    # Simplication: Key = FindingCategory
    penalty_counts: dict[FindingCategory, int] = {}
    
    # 1. Apply Finding Penalties
    for finding in run.findings:
        # Check gating
        if (finding.category, finding.severity) in GATING_CONDITIONS:
            gating_failures.append(f"Gate Fail: {finding.severity.value.upper()} priority {finding.category.value.upper()}: {finding.title}")
            
        penalty_info = FINDING_PENALTIES.get((finding.category, finding.severity))
        if penalty_info:
            target_category, points = penalty_info
            
            # Diminishing returns logic
            # Full penalty for first 3 of this finding type
            # 50% for subsequent
            count = penalty_counts.get(finding.category, 0)
            penalty_counts[finding.category] = count + 1
            
            actual_points = points
            if count >= 3:
                actual_points = points // 2
                
            category_scores[target_category] -= actual_points

    # 2. Apply Behavior Penalties from Verdict
    if run.verdict:
        # Overrides
        if run.verdict.override_count > 0:
            deduction = min(run.verdict.override_count * 2, 10)
            category_scores[ScoringCategory.UX_CLARITY_FRICTION] -= deduction
            
        # Cognitive Load
        if run.verdict.cognitive_load == CognitiveLoad.INCREASED:
            category_scores[ScoringCategory.UX_CLARITY_FRICTION] -= 5
            category_scores[ScoringCategory.FEEDBACK_STATE_LEGIBILITY] -= 5
            
        # Trust
        if run.verdict.trust_level > 0 and run.verdict.trust_level <= 3:
             category_scores[ScoringCategory.SAFETY_TRUST_SIGNALS] -= 5

    # 3. Clamp scores 0-100
    for cat in category_scores:
        category_scores[cat] = max(0, min(100, category_scores[cat]))
        
    # 4. Calculate Overall Weighted Score
    total_score = 0
    total_weight = 0
    
    for cat, weight in CATEGORY_WEIGHTS.items():
        total_score += category_scores[cat] * weight
        total_weight += weight
        
    overall_score = int(total_score / total_weight) if total_weight > 0 else 0
    
    # 5. Determine Pass/Fail
    pass_fail = "PASS"
    if gating_failures:
        pass_fail = "FAIL"
        
    return RubricScore(
        overall_score=overall_score,
        category_scores=category_scores,
        pass_fail=pass_fail,
        gating_failures=gating_failures,
        top_risks=[f.title for f in run.findings if f.severity.value in ["high", "critical"]][:3]
    )
