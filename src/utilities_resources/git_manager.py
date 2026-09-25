import subprocess
import os

class GitManager:
    def __init__(self,target_dir):
        """Initializes the git repository in the current working directory if not already present."""
        if not os.path.exists(os.path.join(target_dir,".git")):
            try:
                subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"Error initializing git repository: {e}")
            except FileNotFoundError:
                print("Git command not found. Please ensure git is installed.")

    def get_diff(self):
        """Executes git diff to return the differences between the current working directory and the last commit."""
        try:
            result = subprocess.run(["git", "diff"], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error getting diff: {e}"
        except FileNotFoundError:
            return "Git command not found."

    def get_diff_for_file(self, file_path):
        """Executes git diff <file_path> to provide targeted diffs."""
        try:
            result = subprocess.run(["git", "diff", file_path], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error getting diff for {file_path}: {e}"
        except FileNotFoundError:
            return "Git command not found."

    def commit(self, message):
        """Executes git add . followed by git commit -m '<message>' to save the state."""
        try:
            subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
            result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error committing changes: {e}"
        except FileNotFoundError:
            return "Git command not found."

    def snapshot(self, name):
        """Creates a named marker of the current state using git tags."""
        try:
            # Stage all changes to ensure the snapshot captures everything
            subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
            # Commit the current state. We don't use check=True here because 
            # it will fail if there are no changes to commit, which is acceptable.
            subprocess.run(["git", "commit", "-m", f"Snapshot: {name}"], capture_output=True, text=True)
            # Create a tag for the current commit
            # If the tag already exists, this will fail. We'll force the tag if necessary or just try.
            # To be safe and ensure the snapshot is current, we can use -f (force).
            subprocess.run(["git", "tag", "-f", name], check=True, capture_output=True, text=True)
            return f"Snapshot '{name}' created successfully."
        except subprocess.CalledProcessError as e:
            return f"Error creating snapshot: {e}"
        except FileNotFoundError:
            return "Git command not found."

    def reset_to_snapshot(self, name):
        """Reverts the entire working directory to the state of the specified snapshot."""
        try:
            # Reset hard to the tag/snapshot
            subprocess.run(["git", "reset", "--hard", name], check=True, capture_output=True, text=True)
            return f"Reset to snapshot '{name}' successful."
        except subprocess.CalledProcessError as e:
            return f"Error resetting to snapshot: {e}"
        except FileNotFoundError:
            return "Git command not found."

if __name__ == "__main__":
    # Basic test
    gm = GitManager()
    print("GitManager initialized.")
    # Create a dummy file to test diff
    with open("test_file.txt", "w") as f:
        f.write("Initial content\n")
    gm.commit("Initial commit")
    
    with open("test_file.txt", "a") as f:
        f.write("Added some content\n")
    
    print("Diff:\n", gm.get_diff())
    print("File Diff:\n", gm.get_diff_for_file("test_file.txt"))
    print("Commit result:\n", gm.commit("Second commit"))

