"""Aggregate score calculation logic."""

from ai_beta_tester.models.session import Session
from ai_beta_tester.models.rubric import AggregateRubricScore
from ai_beta_tester.scoring.categories import CATEGORY_WEIGHTS


def calculate_aggregate_score(session: Session) -> AggregateRubricScore:
    """Calculate the aggregate score for a session."""
    
    agent_scores = {}
    agent_verdicts = {}
    all_gating_failures = []
    
    # Collect individual scores
    for run in session.agent_runs:
        if run.score:
            agent_scores[run.personality] = run.score
            all_gating_failures.extend(
                [f"{run.personality}: {fail}" for fail in run.score.gating_failures]
            )
        if run.verdict:
            agent_verdicts[run.personality] = run.verdict

    if not agent_scores:
        return AggregateRubricScore()
        
    # Calculate Aggregate Category Scores
    # Strategy: Average of the bottom 2 scores (or min if < 2 agents) to penalize risk
    agg_category_scores = {}
    
    for cat in CATEGORY_WEIGHTS:
        scores = [s.category_scores.get(cat, 100) for s in agent_scores.values()]
        scores.sort() # Ascending
        
        if not scores:
            agg = 0
        elif len(scores) == 1:
            agg = scores[0]
        else:
            # Average of worst 2
            agg = int((scores[0] + scores[1]) / 2)
            
        agg_category_scores[cat] = agg
        
    # Calculate Overall Weighted Score
    total_score = 0
    total_weight = 0
    
    for cat, weight in CATEGORY_WEIGHTS.items():
        total_score += agg_category_scores[cat] * weight
        total_weight += weight
        
    overall_score = int(total_score / total_weight) if total_weight > 0 else 0
    
    # Determine Pass/Fail
    pass_fail = "PASS"
    if all_gating_failures:
        pass_fail = "FAIL"
        
    return AggregateRubricScore(
        overall_score=overall_score,
        category_scores=agg_category_scores,
        pass_fail=pass_fail,
        gating_failures=all_gating_failures,
        agent_scores=agent_scores,
        agent_verdicts=agent_verdicts,
        notes=["Aggregated using Top-2 Worst strategy"]
    )
