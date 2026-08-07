# dysfunctional_teammates

A Python framework for running multiple LLM-driven agents in a shared scenario — where agents are *allowed and encouraged to disagree and be disruptive*. Each agent maintains its own private state and strategy, and agents coordinate (or fail to coordinate) with each other through shared files and a shared chatroom.

## Overview

Each agent runs its own reasoning loop, backed by an LLM 

Agents:

- Maintain **individual state** — motivations, relationships to other agents, and strategy plans, all stored as plain text files.
- Communicate through a **shared chatroom** file rather than direct messages.
- Coordinate on tasks turn-by-turn.
- Can be created or terminated dynamically during a run — an agent can request that a new teammate be added or that an existing one be removed.
- Yaml config files allowing during run time modification, and monitoring of on going created agents. 
- Context/chat history saved through pickle directly to a file that can be viewed with any text editor. 

## Project Structure

```
src/
main.py                      # Main orchestrator / simulation loop
core_agent.py       # Core agent implementation
tools/                       # Agent tool implementations
utilities_resources/
    to_be_copied_to_world_state              # Addtional scenario files to be copied to world_state folder on scenario start.
    scenario_manager.py         # Scenario init, backups, agent folder creation
    variants.py                 # Agent personality/behavior variants
    prompt_strings.py           # System/user/injection prompt templates
    random_names.txt            # Pool of names for generated agents

Agent Working Folder:    #Configured in .eng
{scenario_name}/              # Generated at runtime, e.g. "save_files/"
    world_state/
        world_state.txt
        user_conversation.txt
    shared_space/
        chatroom.txt          # Shared chat between agents 
    {agent_name}/              # One folder per agent
        motivations.txt
        relationship_to_other_agents.txt
        strategy_plan.txt
```

## Setup

1. **Requirements**: Python 3.8+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   (or, if using [uv](https://github.com/astral-sh/uv), simply `uv sync` — a `uv.lock` file is included)
3. Create a `.env` file (or otherwise set environment variables) Check .env-example for required values.

4. Review and adjust agent prompts/settings in `main.py` (e.g. `number_of_days`, `number_of_agents`, `scenario_name`).
5. Adjust `scenario_setup.py` (if present) to configure the initial world state. Ongoing user input to the simulation goes in `world_state/user_conversation.txt`.

## Usage

Run the simulation:

```bash
python main.py
```

**Important:** running `main.py` resets the scenario — any existing state under the configured scenario folder will be wiped and reinitialized.

While it's running:

- Each agent reads and writes to its own private folder (`motivations.txt`, `relationship_to_other_agents.txt`, `strategy_plan.txt`).
- Agents talk to each other via `shared_space/chatroom.txt`. **This file is reset every turn.**
- Provide tasks or steer the simulation by editing `world_state/user_conversation.txt`.
- Turn progression is gated on all agents signaling readiness in `shared_space/player_status.txt`.
- Agents can request new teammates or request that a teammate be deleted mid-run; deleted agents' folders are kept but renamed with a `_Deleted` suffix.
- Created agents have a .yaml folder in the agent config
- A backup of the scenario folder is written after each day via `backup_scenario`.
- Chat history is saved to agent context folder

### Watching agents live

The repo's `main.py` includes example [`multitail`](https://github.com/halturin/multitail) commands for tailing multiple agent files at once, e.g.:

```bash
multitail --follow-all -s 2 -du -q 1 "save_files/*/*relation*.txt" "votes.json" "save_files/shared_space/chatroom.txt" -q 1 "save_files/world_state/*.txt"
```

## Known Limitations / Next Steps

- There's currently no persistent history for the chatroom or per-turn state — since `chatroom.txt` (and other per-turn files) can be reset. The backups will contain snap shots but if an agent truncates a file within the same round of turns it will not be backed up.

- Simulations cannot be replated.