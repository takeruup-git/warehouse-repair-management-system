import pytest
from flask import url_for, session

def test_operator_selection_modal(client, auth, app):
    """Test that the operator selection modal appears and works correctly."""
    auth.login()
    
    # Access a page that should trigger the operator selection modal
    response = client.get('/forklift')
    assert response.status_code == 200
    
    # Check if the operator selection modal is present
    assert b'\xe6\x93\x8d\xe4\xbd\x9c\xe8\x80\x85\xe9\x81\xb8\xe6\x8a\x9e' in response.data  # '操作者選択' in UTF-8
    
def test_operator_selection_functionality(client, auth, app):
    """Test the operator selection functionality."""
    auth.login()
    
    # Select an operator
    response = client.post(
        '/operator/select',
        data={'operator_name': 'Test Operator'},
        follow_redirects=True
    )
    
    # Check response
    assert response.status_code == 200
    
    # Verify operator is set in session
    with client.session_transaction() as sess:
        assert 'operator_name' in sess
        assert sess['operator_name'] == 'Test Operator'
    
def test_operator_persistence(client, auth, app):
    """Test that the operator name persists across requests."""
    auth.login()
    
    # Select an operator
    client.post(
        '/operator/select',
        data={'operator_name': 'Persistent Operator'},
        follow_redirects=True
    )
    
    # Make another request
    response = client.get('/forklift')
    assert response.status_code == 200
    
    # Verify operator is still set in session
    with client.session_transaction() as sess:
        assert 'operator_name' in sess
        assert sess['operator_name'] == 'Persistent Operator'
    
def test_operator_used_in_records(client, auth, app):
    """Test that the operator name is recorded in database records."""
    auth.login()
    
    # Select an operator
    client.post(
        '/operator/select',
        data={'operator_name': 'Record Operator'},
        follow_redirects=True
    )
    
    # Create a record that should include the operator name
    with app.app_context():
        from app.models.forklift import Forklift
        from app import db
        
        # Get a forklift to use for the test
        forklift = Forklift.query.first()
        if forklift:
            # Add a repair record
            response = client.post(
                f'/forklift/{forklift.id}/repair/add',
                data={
                    'repair_date': '2025-03-15',
                    'repair_reason': 'failure',
                    'repair_target': 'battery',
                    'repair_action': 'X',
                    'cost': '50000',
                    'description': 'Test repair with operator'
                },
                follow_redirects=True
            )
            
            # Check response
            assert response.status_code == 200
            
            # Verify operator was recorded
            from app.models.forklift import ForkliftRepair
            
            repair = ForkliftRepair.query.filter_by(forklift_id=forklift.id).order_by(ForkliftRepair.id.desc()).first()
            assert repair is not None
            assert repair.updated_by == 'Record Operator'