import pytest
from flask import url_for, session

def test_operator_info_modal(client, auth, app):
    """Test that the operator info modal appears correctly."""
    auth.login()
    
    # Access a page that should have the operator info modal
    response = client.get('/forklift/')
    assert response.status_code == 200
    
    # Check if the operator info modal is present
    assert b'\xe6\x93\x8d\xe4\xbd\x9c\xe8\x80\x85\xe6\x83\x85\xe5\xa0\xb1' in response.data  # '操作者情報' in UTF-8