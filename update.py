# Script to update the working_with_cogstack repo from github branch main
import subprocess

# Command to stash local changes
stash_command = ["git", "stash", "save", "Stashing local changes"]

# Command to list changes in the stash
list_changes_command = ["git", "stash", "show", "-p", "--name-only"]

# Command to perform a git pull
pull_command = ["git", "pull"]

# Replace this with the actual path of the file you want to restore
files_to_restore = ["credentials.py"]

try:
    # Run the command to stash local changes
    subprocess.run(stash_command, check=True)
    
    print("Local changes stashed.")

    # Check if there are stash entries
    stash_entries = subprocess.check_output(list_changes_command, text=True)
    
    # Run the command to list changes in the stash
    changes_output = subprocess.check_output(list_changes_command, text=True)

    print("Changes in the stash:")
    print(changes_output)
    if input(f"Only {', '.join(files_to_restore)} will be preserved.\nAre you should you want to continue? (y/n)") == 'y':
        # Run the command to perform a git pull
        subprocess.run(pull_command, check=True)
        
        print("Pull complete.")

        # Run the command to restore the specific file
        for file_to_restore in files_to_restore:
            # Command to restore a specific file from the stash
            subprocess.run(["git", "checkout", "stash@{0}", "--", file_to_restore], check=True)
        
        print(f"File {file_to_restore} restored from stash.")
    else:
        print("Operation cancelled.")
        
except subprocess.CalledProcessError as e:
    if e.returncode == 1:
        print("No stash entries found. Continuing with git pull.")
        # Run the command to perform a git pull
        subprocess.run(pull_command, check=True)
    else:
        print("An error occurred:")
        print(e)

