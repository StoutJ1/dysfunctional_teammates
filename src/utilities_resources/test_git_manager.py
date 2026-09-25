import os
import subprocess
from git_manager import GitManager

def test_git_manager():
    print("Starting rigorous testing of GitManager...")
    gm = GitManager()
    
    # Setup: Clean start (if possible) or just use a unique file
    test_file = "qa_test_file.txt"
    if os.path.exists(test_file):
        os.remove(test_file)
        
    # Test 1: Initial Commit
    print("\nTest 1: Initial Commit")
    with open(test_file, "w") as f:
        f.write("QA Test Line 1\n")
    
    commit_res = gm.commit("QA: Initial commit")
    print(f"Commit result: {commit_res}")
    
    # Verify file is in git
    res = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    if test_file in res.stdout:
        print("PASSED: File tracked by git.")
    else:
        print("FAILED: File not tracked by git.")

    # Test 2: Global Diff
    print("\nTest 2: Global Diff")
    with open(test_file, "a") as f:
        f.write("QA Test Line 2\n")
    
    diff = gm.get_diff()
    if "QA Test Line 2" in diff:
        print("PASSED: Global diff detected change.")
    else:
        print(f"FAILED: Global diff failed. Output: {diff}")

    # Test 3: File-specific Diff
    print("\nTest 3: File-specific Diff")
    file_diff = gm.get_diff_for_file(test_file)
    if "QA Test Line 2" in file_diff:
        print("PASSED: File-specific diff detected change.")
    else:
        print(f"FAILED: File-specific diff failed. Output: {file_diff}")

    # Test 4: Commit clearing diff
    print("\nTest 4: Commit clearing diff")
    gm.commit("QA: Second commit")
    diff_after = gm.get_diff()
    if not diff_after or "nothing to commit" in diff_after or diff_after == "":
        # Note: git diff returns empty string if there are no changes
        print("PASSED: Diff is empty after commit.")
    else:
        # If there are other changes in the repo, this might fail. 
        # But for our specific file, it should be gone.
        file_diff_after = gm.get_diff_for_file(test_file)
        if not file_diff_after:
            print("PASSED: File-specific diff is empty after commit.")
        else:
            print(f"FAILED: Diff still exists after commit: {file_diff_after}")

    # Test 5: Edge Case - Non-existent file diff
    print("\nTest 5: Non-existent file diff")
    non_existent = "does_not_exist_12345.txt"
    res_non = gm.get_diff_for_file(non_existent)
    # Git usually returns an error or empty for non-existent files in diff
    if "Error getting diff" in res_non or res_non == "":
        print("PASSED: Handled non-existent file.")
    else:
        print(f"FAILED: Unexpected result for non-existent file: {res_non}")

    # Test 6: Edge Case - Empty Commit (No changes)
    print("\nTest 6: Empty Commit")
    res_empty = gm.commit("Empty commit")
    if "Error committing changes" in res_empty:
        print("PASSED: Correctly identified that there was nothing to commit.")
    else:
        print(f"FAILED: Git should not have committed nothing. Result: {res_empty}")

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    test_git_manager()

