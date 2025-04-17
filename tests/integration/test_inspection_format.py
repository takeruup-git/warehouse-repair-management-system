import pytest
from flask import url_for
import os

def test_inspection_format_button(client, auth):
    """Test that the inspection format button is present on the forklift list page."""
    auth.login()
    response = client.get('/forklift')
    assert response.status_code == 200
    assert b'\xe5\xae\x9a\xe6\x9c\x9f\xe8\x87\xaa\xe4\xb8\xbb\xe6\xa4\x9c\xe6\x9f\xbb\xe8\xa8\x98\xe9\x8c\xb2\xe8\xa1\xa8\xe5\x87\xba\xe5\x8a\x9b' in response.data  # '定期自主検査記録表出力' in UTF-8

def test_inspection_format_generation(client, auth, app):
    """Test the generation of inspection format Excel file."""
    auth.login()
    
    # Ensure we have some forklifts in the database
    with app.app_context():
        from app.models.forklift import Forklift
        from app import db
        
        # Check if we have active forklifts, if not create one
        active_forklifts = Forklift.query.filter_by(status='active').count()
        if active_forklifts == 0:
            forklift = Forklift(
                asset_id='FORMAT-TEST',
                model_number='FORMAT-MODEL',
                serial_number='FORMAT-SN',
                forklift_type='reach',
                power_source='battery',
                max_load=1000,
                max_height=3000,
                manufacture_year=2022,
                status='active'
            )
            db.session.add(forklift)
            db.session.commit()
    
    # Generate the inspection format
    response = client.get('/forklift/inspection-format')
    
    # Check response
    assert response.status_code == 200
    assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert 'Content-Disposition' in response.headers
    assert 'attachment' in response.headers['Content-Disposition']
    assert 'inspection_format' in response.headers['Content-Disposition']