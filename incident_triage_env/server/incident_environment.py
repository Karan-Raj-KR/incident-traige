import json
import os
import random
from typing import Optional

try:
    from openenv.core import Environment
except ImportError:
    class Environment:
        pass

try:
    from ..models import IncidentAction, IncidentObservation, IncidentState
except ImportError:
    from models import IncidentAction, IncidentObservation, IncidentState

try:
    from .rewards import calculate_reward
except ImportError:
    from rewards import calculate_reward


class IncidentEnvironment(Environment):
    def __init__(self, max_steps: int = 15):
        self.max_steps = max_steps
        self.step_count = 0
        self._state = None
        self.current_scenario = None

    def reset(self, scenario_id: Optional[str] = None) -> IncidentObservation:
        self.step_count = 0
        
        if not scenario_id:
            scenario_id = random.choice(["task1_simple", "task2_cascade", "task3_noisy"])
            
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scenario_path = os.path.join(base_dir, "scenarios", f"{scenario_id}.json")
        
        if not os.path.exists(scenario_path):
            scenario_path = os.path.join("scenarios", f"{scenario_id}.json")
            
        with open(scenario_path, "r") as f:
            self.current_scenario = json.load(f)
            
        self._state = IncidentState(
            ground_truth=self.current_scenario.get("ground_truth", {}),
            actions_taken=[],
            diagnosed=False,
            remediated=False,
            service_statuses=self.current_scenario.get("topology", {})
        )
        
        return IncidentObservation(
            alerts=self.current_scenario.get("alerts", []),
            logs=self.current_scenario.get("logs", {}),
            metrics=self.current_scenario.get("metrics", {}),
            topology=self.current_scenario.get("topology", {})
        )

    def step(self, action: IncidentAction) -> IncidentObservation:
        self.step_count += 1
        
        action_summary = {
            "action_type": action.action_type,
            "target": getattr(action, "target", None),
            "summary": getattr(action, "summary", "")
        }
        
        obs_logs = {}
        obs_metrics = {}
        
        target = getattr(action, "target", None)
        action_type = action.action_type
        
        if action_type == "investigate" and target:
            obs_logs = {target: self.current_scenario.get("deeper_logs", {}).get(target, [])}
            obs_metrics = {target: self.current_scenario.get("deeper_metrics", {}).get(target, {})}
            
        elif action_type == "diagnose":
            action_summary["diagnosis_attempt"] = getattr(action, "payload", {})
            if target == self._state.ground_truth.get("root_cause_service"):
                self._state.diagnosed = True
                
        elif action_type == "remediate":
            action_summary["remediation_attempt"] = getattr(action, "payload", {})
            root_cause = self._state.ground_truth.get("root_cause_service")
            if target == root_cause and self._state.diagnosed:
                self._state.remediated = True
                if target in self._state.service_statuses:
                    self._state.service_statuses[target]["status"] = "recovering"
                    
        elif action_type == "escalate":
            action_summary["severity"] = getattr(action, "payload", {}).get("severity")
            
        elif action_type == "communicate":
            action_summary["communication_summary"] = action_summary["summary"]

        self._state.actions_taken.append(action_summary)
        
        reward = calculate_reward(self._state, action)
        
        done = False
        if self.step_count >= self.max_steps:
            done = True
        elif self._state.diagnosed and self._state.remediated:
            done = True
            
        return IncidentObservation(
            alerts=[],
            logs=obs_logs,
            metrics=obs_metrics,
            topology=self._state.service_statuses,
            reward=reward,
            done=done,
            step=self.step_count
        )

    @property
    def state(self) -> IncidentState:
        return self._state
