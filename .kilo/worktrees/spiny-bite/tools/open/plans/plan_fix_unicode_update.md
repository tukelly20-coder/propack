# Plan to Fix Unicode Issue in Update Script

## Problem
The update script fails during the backup phase with robocopy exit code 16 when dealing with Unicode paths (Vietnamese characters) and spaces.

## Root Cause
The robocopy command in the PowerShell script may not handle Unicode paths correctly despite the UTF-8 encoding setting, or there may be issues with the long paths or special characters.

## Solution
Use Windows short paths (8.3 format) for all file operations in the update script to avoid Unicode and space-related issues.

## Steps
- [ ] Modify the `apply_onedir_update` function in `updater.py` to compute short paths for:
      - onedir_path
      - backup_path
      - parent_dir
      - extracted_path (if used in PowerShell)
- [ ] Pass these short paths as parameters to the PowerShell script instead of the original paths.
- [ ] Ensure the PowerShell script uses the short paths for all operations (robocopy, process finding, Explorer refresh, etc.).
- [ ] Test the updated script with a Unicode path to verify the backup and update process works.