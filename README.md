# dysfunctional_teammates

A Python framework for running multiple LLM-driven agents in a shared scenario — where agents are *allowed and encouraged to disagree and be disruptive*. Each agent maintains its own private state and strategy, and agents coordinate (or fail to coordinate) with each other through shared files and a shared chatroom.

## Overview

Each agent runs its own reasoning loop, backed by an LLM 

Agents:

- Maintain **individual state** — motivations, relationships to other agents, and strategy plans, all stored as plain text files.
- Communicate through a **shared chatroom** file rather than direct messages.
- Coordinate on tasks turn-by-turn.
- Can be created or terminated dynamically during a run — an agent can request that a new teammate be added or that an existing one be removed.

The framework runs in discrete "days" (turns). Within each day, every active agent gets a number of iterations to read shared context, act, and update its own files before the next day begins.

## Project Structure

```
main.py                      # Main orchestrator / simulation loop
simple_agent_object.py       # Core agent implementation
tools/                       # Agent tool implementations
utilities/
    world_state              # Addtional scenario files to be copied to world_state folder on scenario start.
    scenario_manager.py      # Scenario init, backups, agent folder creation
    turn_manager.py          # Turn/day progression logic
    variants.py              # Agent personality/behavior variants
    prompt_strings.py        # System/user/injection prompt templates
    random_names.txt         # Pool of names for generated agents

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
3. Create a `.env` file (or otherwise set environment variables) with:
   ```
   GEMINI_API_KEY=your_key_here
   BASE_URL_ENV=your_base_url
   MODEL=your_model_name
   WORKING_DIRECTORY=agent_working_folder
   ```
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
- A backup of the scenario folder is written after each day via `backup_scenario`.

### Watching agents live

The repo's `main.py` includes example [`multitail`](https://github.com/halturin/multitail) commands for tailing multiple agent files at once, e.g.:

```bash
multitail --follow-all -s 2 -du -q 1 "save_files/*/*relation*.txt" "votes.json" "save_files/shared_space/chatroom.txt" -q 1 "save_files/world_state/*.txt"
```

## Known Limitations / Next Steps

- There's currently no persistent history for the chatroom or per-turn state — since `chatroom.txt` (and other per-turn files) reset every day, that data is lost and can't be replayed later. Adding turn-by-turn history/replay support is a planned improvement.

