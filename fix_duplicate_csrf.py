#!/usr/bin/env python3
import os
import re

def fix_duplicate_csrf_tokens(directory):
    """
    Recursively search for HTML files in the given directory and remove duplicate CSRF tokens.
    """
    # Pattern to match both the include statement and the direct CSRF token input
    include_pattern = re.compile(r'{% include [\'"]includes/csrf_token.html[\'"] %}')
    direct_pattern = re.compile(r'<input type="hidden" name="csrf_token" value="{{ csrf_token\(\) }}">')
    
    # Count of files modified
    modified_count = 0
    
    # Walk through all files in the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if both patterns exist in the file
                include_match = include_pattern.search(content)
                direct_match = direct_pattern.search(content)
                
                if include_match and direct_match:
                    # Remove the direct CSRF token input
                    new_content = direct_pattern.sub('', content)
                    
                    # Write the modified content back to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    modified_count += 1
                    print(f"Removed duplicate CSRF token from {file_path}")
    
    return modified_count

if __name__ == "__main__":
    templates_dir = "app/templates"
    modified = fix_duplicate_csrf_tokens(templates_dir)
    print(f"Fixed duplicate CSRF tokens in {modified} files.")