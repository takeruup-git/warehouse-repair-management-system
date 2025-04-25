#!/usr/bin/env python3
import os
import re

def remove_csrf_tokens(directory):
    """
    Recursively search for HTML files in the given directory and remove CSRF token inputs.
    """
    # Pattern to match CSRF token input
    csrf_pattern = re.compile(r'<input[^>]*name=["\']csrf_token["\'][^>]*>')
    
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
                
                # Find all CSRF token inputs
                matches = csrf_pattern.findall(content)
                
                # If we found CSRF token inputs
                if matches:
                    # Remove CSRF token inputs
                    new_content = csrf_pattern.sub('', content)
                    
                    # Write the modified content back to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    modified_count += 1
                    print(f"Removed CSRF token from {file_path}")
    
    return modified_count

if __name__ == "__main__":
    templates_dir = "app/templates"
    modified = remove_csrf_tokens(templates_dir)
    print(f"Removed CSRF tokens from {modified} files.")