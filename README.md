# Agent Collaboration Framework

## Overview
A Python-based framework for running multiple AI agents in a collaborative scenario. Agents are allowed and encouraged to disagree and be disruptive. Agents communicate via shared files, maintain individual state, and coordinate tasks through a shared chatroom.

## Project Structure
```
# Core scripts and global state
 main.py           # Main orchestrator
 scenario_setup.py # Scenario initialization
simple_agent_object.py     # Agent implementation 

- {scenario_name}/
    - world_state/
        - world_state.txt
        - user_conversation
    - shared_space/
        - share_space.txt
        - player_status.txt
    - {agent_name}/ (for each agent in the agents list)
        - motivations.txt
        - relationship_to_other_agents.txt
        - strategy_plan.txt
        
```

## Setup
1. Ensure Python 3.8+ is installed.
2. Install required dependencies (check `requirements.txt` if present).
3. Configure environment variables (e.g., `GEMINI_API_KEY`, `BASE_URL_ENV`,`MODEL`,`WORKING_DIRECTORY`).
4. Main.py contains agent prompts and variants.
5. Scenario_setup.py can be modified to setup initial state. For ongoing interactions check the user_conversation.txt
6. Execute `python main.py` to start the agent collaboration loop.

## Usage
- Agents read/write to their private directories for strategy and relationships.
- Shared collaboration happens via `shared_space/chatroom.txt`.
- User provides tasks via `world_state/user_conversation.txt`.
- Turn-based execution: agents signal readiness via `player_status.txt`, each turn will reset the chatroom.txt
- Running main.py will reset the scenario.
## Next Steps
- Need to setup a history save for the chatroom and other files so the data isn't lost when turn resets/can be replayed.