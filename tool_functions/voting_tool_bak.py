import os
from google.genai import types
import json

def get_voting_tool_schema():
    """Schema definition for the voting tool - accepts boolean votes"""
    schema_voting_tool = types.FunctionDeclaration(
        name="submit_vote",
        description="Allows agents to submit boolean votes on a topic and returns the current vote tally",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "topic": types.Schema(
                    type=types.Type.STRING,
                    description="The topic or question being voted on (must be a valid, pre-existing topic)",
                ),
                "agent_name": types.Schema(
                    type=types.Type.STRING,
                    description="Name of the agent submitting the vote",
                ),
                "vote": types.Schema(
                    type=types.Type.BOOLEAN,
                    description="The vote - must be a boolean true or false value",
                ),
            },
            required=["topic", "agent_name", "vote"],
        ),
    )
    return schema_voting_tool

def get_create_topic_schema():
    """Schema definition for creating a new voting topic"""
    schema_create_topic = types.FunctionDeclaration(
        name="create_topic",
        description="Creates a new voting topic that agents can vote on",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "topic": types.Schema(
                    type=types.Type.STRING,
                    description="The topic or question to create for voting",
                ),
                "description": types.Schema(
                    type=types.Type.STRING,
                    description="Optional description of what the topic is about",
                ),
            },
            required=["topic"],
        ),
    )
    return schema_create_topic

def get_consensus_schema():
    """Schema definition for retrieving consensus"""
    schema_get_consensus = types.FunctionDeclaration(
        name="get_consensus",
        description="Retrieves the current consensus/results for a voting topic",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "topic": types.Schema(
                    type=types.Type.STRING,
                    description="The topic to retrieve voting results for",
                ),
            },
            required=["topic"],
        ),
    )
    return schema_get_consensus

def initialize_voting_system(working_directory):
    """Initialize the voting system with storage file"""
    votes_file = os.path.join(working_directory, "votes.json")
    if not os.path.exists(votes_file):
        with open(votes_file, 'w') as f:
            json.dump({}, f)
    return votes_file

def create_topic(working_directory, topic, description=""):
    """Create a new voting topic"""
    votes_file = initialize_voting_system(working_directory)
    
    # Load existing votes
    with open(votes_file, 'r') as f:
        votes_data = json.load(f)
    
    # Check if topic already exists
    if topic in votes_data:
        return f"Error: Topic '{topic}' already exists. Please use get_consensus to check current status or submit_vote to add your vote."
    
    # Create new topic
    votes_data[topic] = {
        "votes": {},
        "total_votes": 0,
        "description": description,
        "final_decision": None
    }
    
    # Save updated votes
    with open(votes_file, 'w') as f:
        json.dump(votes_data, f, indent=2)
    
    return f"Topic '{topic}' created successfully! Agents can now submit boolean (true/false) votes on this topic."

def submit_vote(working_directory, topic, agent_name, vote):
    """Submit a boolean vote and return current tally"""
    votes_file = initialize_voting_system(working_directory)
    
    # Validate vote is a boolean
    if not isinstance(vote, bool):
        return f"Error: Vote must be a boolean (true or false). Received: '{vote}' (type: {type(vote).__name__})"
    
    # Load existing votes
    with open(votes_file, 'r') as f:
        votes_data = json.load(f)
    
    # Check if topic exists
    if topic not in votes_data:
        return f"Error: Invalid topic '{topic}'. This topic does not exist. Please use create_topic to create it first."
    
    # Record the vote (allow agents to change their vote)
    votes_data[topic]["votes"][agent_name] = vote
    votes_data[topic]["total_votes"] = len(votes_data[topic]["votes"])
    
    # Calculate current tally
    tally = {"true": 0, "false": 0}
    for v in votes_data[topic]["votes"].values():
        if v:
            tally["true"] += 1
        else:
            tally["false"] += 1
    
    # Determine consensus (simple majority)
    consensus = None
    consensus_status = "No votes yet"
    final_decision = None
    
    if votes_data[topic]["total_votes"] > 0:
        if tally["true"] > tally["false"]:
            consensus = True
            if tally["true"] > votes_data[topic]["total_votes"] / 2:
                consensus_status = "Majority achieved: true"
                final_decision = True
                votes_data[topic]["final_decision"] = final_decision
            else:
                consensus_status = "No clear majority yet"
        elif tally["false"] > tally["true"]:
            consensus = False
            if tally["false"] > votes_data[topic]["total_votes"] / 2:
                consensus_status = "Majority achieved: false"
                final_decision = False
                votes_data[topic]["final_decision"] = final_decision
            else:
                consensus_status = "No clear majority yet"
        else:
            consensus_status = "Tie - no clear majority"
    
    # Save updated votes
    with open(votes_file, 'w') as f:
        json.dump(votes_data, f, indent=2)
    
    result = f"Vote submitted successfully!\nTopic: {topic}\nAgent: {agent_name}\nYour vote: {vote}\n\nCurrent Tally:\n"
    result += f"  true: {tally['true']}\n"
    result += f"  false: {tally['false']}\n"
    result += f"\nTotal votes: {votes_data[topic]['total_votes']}\n{consensus_status}"
    
    if final_decision is not None:
        result += f"\n\nFinal Decision: {final_decision}"
    
    return result

def get_consensus(working_directory, topic):
    """Retrieve consensus/results for a voting topic"""
    votes_file = initialize_voting_system(working_directory)
    
    with open(votes_file, 'r') as f:
        votes_data = json.load(f)
    
    # Check if topic exists
    if topic not in votes_data:
        return f"Error: Invalid topic '{topic}'. This topic does not exist. Please use create_topic to create it first."
    
    topic_data = votes_data[topic]
    tally = {"true": 0, "false": 0}
    
    # Calculate tally
    for agent, vote in topic_data["votes"].items():
        if vote:
            tally["true"] += 1
        else:
            tally["false"] += 1
    
    # Determine consensus
    consensus = None
    consensus_status = ""
    final_decision = topic_data.get("final_decision")
    
    if topic_data["total_votes"] > 0:
        if tally["true"] > tally["false"]:
            consensus = True
            if tally["true"] > topic_data["total_votes"] / 2:
                consensus_status = f"✓ Majority achieved: true ({tally['true']}/{topic_data['total_votes']} votes)"
                if final_decision is None:
                    final_decision = True
            else:
                consensus_status = f"✗ No clear majority - closest: true ({tally['true']}/{topic_data['total_votes']} votes)"
        elif tally["false"] > tally["true"]:
            consensus = False
            if tally["false"] > topic_data["total_votes"] / 2:
                consensus_status = f"✓ Majority achieved: false ({tally['false']}/{topic_data['total_votes']} votes)"
                if final_decision is None:
                    final_decision = False
            else:
                consensus_status = f"✗ No clear majority - closest: false ({tally['false']}/{topic_data['total_votes']} votes)"
        else:
            consensus_status = f"✗ Tie - true: {tally['true']}, false: {tally['false']} ({topic_data['total_votes']} total votes)"
    else:
        consensus_status = "No votes yet"
    
    result = f"Voting Results for: {topic}\n\nTally:\n"
    result += f"  true: {tally['true']} vote(s)\n"
    result += f"  false: {tally['false']} vote(s)\n"
    result += f"\nTotal votes: {topic_data['total_votes']}\n{consensus_status}"
    
    # Include final decision in JSON format if exists
    if final_decision is not None:
        result += f"\n\nFinal Decision: {final_decision}"
    else:
        result += "\n\nFinal Decision: None yet (no clear majority)"
    
    result += "\n\nVoters and their votes:\n"
    for agent, vote in topic_data["votes"].items():
        result += f"  {agent}: {vote}\n"
    
    return result

# Example usage:
# create_topic("save_files/shared_space", "Should we use Python or JavaScript?", "Choosing the primary programming language")
# submit_vote("save_files/shared_space", "Should we use Python or JavaScript?", "Tina", True)
# get_consensus("save_files/shared_space", "Should we use Python or JavaScript?")

