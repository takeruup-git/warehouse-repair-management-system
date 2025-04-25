#!/usr/bin/env python3
import os
import re

def add_csrf_token_to_forms(directory):
    """
    Recursively search for HTML files in the given directory and add CSRF token to forms
    that don't already have it.
    """
    form_pattern = re.compile(r'<form[^>]*method=["\'](?:post|POST)["\'][^>]*>')
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
                
                # Find all form tags with method="post"
                form_matches = form_pattern.finditer(content)
                
                # Track positions where we need to insert CSRF tokens
                positions = []
                
                for form_match in form_matches:
                    # Get the form tag and its end position
                    form_tag = form_match.group(0)
                    form_end_pos = form_match.end()
                    
                    # Check if there's already a CSRF token in this form
                    # We'll search from the form start to the next form or end of file
                    next_form_match = form_pattern.search(content, form_end_pos)
                    search_end = next_form_match.start() if next_form_match else len(content)
                    form_content = content[form_match.start():search_end]
                    
                    if not csrf_pattern.search(form_content):
                        # This form needs a CSRF token
                        positions.append(form_end_pos)
                
                # If we found forms that need CSRF tokens
                if positions:
                    # Insert CSRF tokens at the identified positions
                    # We need to adjust positions as we insert
                    offset = 0
                    new_content = content
                    for pos in positions:
                        csrf_token = '\n    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
                        adjusted_pos = pos + offset
                        new_content = new_content[:adjusted_pos] + csrf_token + new_content[adjusted_pos:]
                        offset += len(csrf_token)
                    
                    # Write the modified content back to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    modified_count += 1
                    print(f"Added CSRF token to {file_path}")
    
    return modified_count

if __name__ == "__main__":
    templates_dir = "app/templates"
    modified = add_csrf_token_to_forms(templates_dir)
    print(f"Added CSRF tokens to {modified} files.")