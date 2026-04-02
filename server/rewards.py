import json

def diagnosis_matches(actions: list, root_cause: str) -> bool:
    if not root_cause:
        return False
    
    root_cause_lower = str(root_cause).lower()
    for action in actions:
        if action.get("action_type") == "diagnose":
            # Extract diagnosis attempt from summary or payload
            attempt_str = str(action.get("diagnosis_attempt", action.get("summary", ""))).lower()
            if root_cause_lower in attempt_str or attempt_str in root_cause_lower:
                return True
            # Check target as well, in case target is the root cause
            target = str(action.get("target", "")).lower()
            if target and (root_cause_lower in target or target in root_cause_lower):
                return True
    return False

def remediation_matches(actions: list, remediation: str) -> bool:
    if not remediation:
        return False
        
    remediation_lower = str(remediation).lower()
    for action in actions:
        if action.get("action_type") == "remediate":
            attempt_str = str(action.get("remediation_attempt", action.get("summary", ""))).lower()
            target = str(action.get("target", "")).lower()
            if remediation_lower in attempt_str or attempt_str in remediation_lower:
                return True
            if remediation_lower in target or target in remediation_lower:
                return True
    return False

def severity_matches(actions: list, severity: str) -> bool:
    if not severity:
        return False
        
    severity_lower = str(severity).lower()
    for action in actions:
        if action.get("action_type") == "escalate":
            # Check severity payload or summary
            attempt_sev = str(action.get("severity", action.get("summary", ""))).lower()
            if severity_lower in attempt_sev or attempt_sev in severity_lower:
                return True
    return False

def count_relevant_investigations(actions: list, ground_truth: dict) -> int:
    affected_services = ground_truth.get("affected_services", [])
    if isinstance(affected_services, str):
        affected_services = [affected_services]
        
    affected_services = [s.lower() for s in affected_services]
    root_cause = ground_truth.get("root_cause", "")
    if root_cause and str(root_cause).lower() not in affected_services:
        affected_services.append(str(root_cause).lower())
        
    count = 0
    for action in actions:
        if action.get("action_type") == "investigate":
            target = str(action.get("target", "")).lower()
            if any(target in s or s in target for s in affected_services if target and s):
                count += 1
    return count

def count_irrelevant_investigations(actions: list, ground_truth: dict) -> int:
    affected_services = ground_truth.get("affected_services", [])
    if isinstance(affected_services, str):
        affected_services = [affected_services]
        
    affected_services = [s.lower() for s in affected_services]
    root_cause = ground_truth.get("root_cause", "")
    if root_cause and str(root_cause).lower() not in affected_services:
        affected_services.append(str(root_cause).lower())
        
    count = 0
    for action in actions:
        if action.get("action_type") == "investigate":
            target = str(action.get("target", "")).lower()
            is_relevant = any(target in s or s in target for s in affected_services if target and s)
            if not is_relevant:
                count += 1
    return count

def calculate_reward(actions_taken: list, ground_truth: dict, scenario_id: str) -> float:
    score = 0.0
    
    # +0.1 per relevant investigation (max +0.2 total)
    relevant_inv = count_relevant_investigations(actions_taken, ground_truth)
    score += min(relevant_inv * 0.1, 0.2)
    
    # +0.3 if diagnosis matches ground_truth["root_cause"]
    root_cause = ground_truth.get("root_cause", "")
    if diagnosis_matches(actions_taken, root_cause):
        score += 0.3
        
    # +0.2 if remediation matches ground_truth["remediation"]
    remediation = ground_truth.get("remediation", "")
    if remediation_matches(actions_taken, remediation):
        score += 0.2
        
    # +0.1 if severity matches ground_truth["severity"]
    severity = ground_truth.get("severity", "")
    if severity_matches(actions_taken, severity):
        score += 0.1
        
    # +0.1 if communicate action exists with non-empty value
    for action in actions_taken:
        if action.get("action_type") == "communicate":
            comm_val = action.get("communication_summary", action.get("summary", ""))
            if comm_val and str(comm_val).strip():
                score += 0.1
                break
                
    # -0.05 per irrelevant investigation (service not in ground_truth affected services)
    irrelevant_inv = count_irrelevant_investigations(actions_taken, ground_truth)
    score -= irrelevant_inv * 0.05
    
    # -0.1 per wrong remediation attempt
    wrong_remediations = 0
    remediation_str = str(ground_truth.get("remediation", "")).lower()
    for action in actions_taken:
        if action.get("action_type") == "remediate":
            attempt_str = str(action.get("remediation_attempt", action.get("summary", ""))).lower()
            target = str(action.get("target", "")).lower()
            match = False
            if remediation_str:
                if remediation_str in attempt_str or attempt_str in remediation_str:
                    match = True
                elif remediation_str in target or target in remediation_str:
                    match = True
            if not match:
                wrong_remediations += 1
                
    score -= wrong_remediations * 0.1
    
    # Clamp final score to [0.0, 1.0]
    return max(0.0, min(1.0, float(score)))
