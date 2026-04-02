try:
    from ..server.rewards import calculate_reward
except ImportError:
    try:
        from server.rewards import calculate_reward
    except ImportError:
        from rewards import calculate_reward

def _eval_action(action) -> str:
    """Helper to safely extract string from different action representations."""
    if isinstance(action, dict):
        return f"{action.get('command', '')} {action.get('action', '')} {action.get('target', '')}"
    return str(action)

def grade_task1(actions_taken: list, ground_truth: dict) -> float:
    """
    Easy scenario. Full marks possible. Straightforward matching.
    """
    if not actions_taken:
        return 0.0
        
    score = 0.0
    root_service = str(ground_truth.get('root_service', 'web')).lower()
    command = str(ground_truth.get('command', 'restart')).lower()
    
    investigated = False
    resolved = False
    
    for act in actions_taken:
        act_str = _eval_action(act).lower()
        if root_service in act_str:
            investigated = True
        if root_service in act_str and command in act_str:
            resolved = True
            
    if investigated:
        score += 0.4
    if resolved:
        score += 0.6
        
    # Small efficiency penalty to vary scores based on steps taken
    efficiency_penalty = len(actions_taken) * 0.02
    
    final_score = max(0.0, min(1.0, score - efficiency_penalty))
    
    # Ensure some variance for completely random actions
    if final_score == 0.0 and len(actions_taken) > 0:
        final_score = min(0.05, len(actions_taken) * 0.005)
        
    return round(final_score, 4)

def grade_task2(actions_taken: list, ground_truth: dict) -> float:
    """
    Medium scenario. Partial credit if they find root service but wrong version.
    Must require correct rollback to get full remediation points.
    """
    if not actions_taken:
        return 0.0
        
    score = 0.0
    root_service = str(ground_truth.get('root_service', 'auth')).lower()
    correct_version = str(ground_truth.get('correct_version', 'v1.2.0')).lower()
    incorrect_version = str(ground_truth.get('incorrect_version', 'v1.2.1')).lower()
    
    investigated = False
    wrong_rollback = False
    correct_rollback = False
    
    for act in actions_taken:
        act_str = _eval_action(act).lower()
        if root_service in act_str:
            investigated = True
            if 'rollback' in act_str or 'deploy' in act_str:
                if incorrect_version in act_str:
                    wrong_rollback = True
                if correct_version in act_str:
                    correct_rollback = True

    if investigated:
        score += 0.3
    
    # Partial credit vs Full remediation
    if wrong_rollback and not correct_rollback:
        score += 0.2
    elif correct_rollback:
        score += 0.7
        
    penalty = len(actions_taken) * 0.015
    final_score = max(0.0, min(1.0, score - penalty))
    
    if final_score == 0.0 and len(actions_taken) > 0:
        final_score = min(0.07, len(actions_taken) * 0.007)
        
    return round(final_score, 4)

def grade_task3(actions_taken: list, ground_truth: dict) -> float:
    """
    Hard scenario. Penalise heavily for chasing noisy alerts.
    Reward heavily for ignoring noise and finding DB config root cause.
    """
    if not actions_taken:
        return 0.0
        
    score = 0.0
    root_cause = str(ground_truth.get('root_cause', 'db-config')).lower()
    noisy_services = ground_truth.get('noisy_services', ['frontend', 'cache', 'prometheus'])
    noisy_services = [str(n).lower() for n in noisy_services]
    
    noise_count = 0
    found_root = False
    
    for act in actions_taken:
        act_str = _eval_action(act).lower()
        
        for noise in noisy_services:
            if noise in act_str:
                noise_count += 1
                
        if root_cause in act_str or 'database' in act_str or 'pg_hba' in act_str:
            found_root = True

    # Heavy penalty for chasing noisy alerts
    noise_penalty = noise_count * 0.15
    
    if found_root:
        score += 0.9
        # Extra reward if they ignored noise entirely
        if noise_count == 0:
            score += 0.1
            
    final_score = max(0.0, min(1.0, score - noise_penalty))
    
    if final_score == 0.0 and len(actions_taken) > 0:
         final_score = min(0.08, len(actions_taken) * 0.008)
         
    return round(final_score, 4)

def get_grader(scenario_id: str) -> callable:
    """
    Returns the correct grader function for task1/task2/task3.
    """
    scenario_id_low = str(scenario_id).lower()
    if 'task1' in scenario_id_low or 'level1' in scenario_id_low or 'easy' in scenario_id_low:
        return grade_task1
    elif 'task2' in scenario_id_low or 'level2' in scenario_id_low or 'medium' in scenario_id_low:
        return grade_task2
    elif 'task3' in scenario_id_low or 'level3' in scenario_id_low or 'hard' in scenario_id_low:
        return grade_task3
    
    # Default fallback
    return grade_task1
