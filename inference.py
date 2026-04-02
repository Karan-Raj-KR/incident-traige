import os
import json
from openai import OpenAI

try:
    from .client import IncidentEnvClient
except ImportError:
    from client import IncidentEnvClient

def main():
    api_base_url = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
    model_name = os.environ.get("MODEL_NAME", "gpt-4-turbo")
    hf_token = os.environ.get("HF_TOKEN")
    
    # Initialize the OpenAI client
    # Assuming HF_TOKEN is used as the API key for an OpenAI-compatible HF endpoint if provided
    api_key = hf_token or os.environ.get("OPENAI_API_KEY", "dummy_key")
    
    client = OpenAI(
        api_key=api_key,
        base_url=api_base_url
    )

    env = IncidentEnvClient()
    scenarios = ["task1_simple", "task2_cascade", "task3_noisy"]
    
    total_score = 0.0
    
    system_prompt = (
        "You are an SRE engineer on call. Diagnose and fix the incident. "
        "Respond ONLY with JSON: {\"action_type\": \"string\", \"target\": \"string\", \"value\": \"string\"}"
    )

    for scenario in scenarios:
        print(f"\n--- Starting episode: {scenario} ---")
        try:
            obs = env.reset(scenario_id=scenario)
            # Depending on the env's reset, it might return obs or (obs, info)
            if isinstance(obs, tuple) and len(obs) == 2:
                obs, _ = obs
        except Exception as e:
            print(f"Failed to reset environment for {scenario}: {e}")
            continue
            
        done = False
        step_count = 0
        episode_reward = 0.0
        
        while not done:
            step_count += 1
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Observation:\n{json.dumps(obs, default=str)}\n\nWhat is your next action?"}
            ]
            
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.1,  # Low temperature for more deterministic JSON outputs
                    response_format={"type": "json_object"}
                )
                
                action_text = response.choices[0].message.content
                action = json.loads(action_text)
                
            except Exception as e:
                print(f"Error during LLM inference: {e}")
                action = {"action_type": "investigate", "target": "system", "value": "retry"}
                
            print(f"Step {step_count} Action: {action}")
            
            try:
                step_result = env.step(action)
                # Handle varying unpacking depending on Gym version (obs, reward, done, info) vs (obs, reward, terminated, truncated, info)
                if len(step_result) == 4:
                    obs, reward, done, info = step_result
                elif len(step_result) == 5:
                    obs, reward, terminated, truncated, info = step_result
                    done = terminated or truncated
                else:
                     raise ValueError(f"Unexpected step() return signature length: {len(step_result)}")
                
                episode_reward = reward
                
            except Exception as e:
                print(f"Error during env.step(): {e}")
                done = True
                episode_reward = 0.0
            
        print(f"Episode {scenario} completed in {step_count} steps. Reward: {episode_reward}")
        total_score += episode_reward
        
    avg_score = total_score / len(scenarios) if scenarios else 0.0
    print(f"\n=== Final Average Score: {avg_score:.2f} ===")

if __name__ == "__main__":
    main()
