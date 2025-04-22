import os
import pytest
import tempfile
from flask import url_for
from io import BytesIO
from reportlab.pdfgen import canvas

def create_test_pdf():
    """Create a test PDF file for annual inspection."""
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer)
    c.drawString(100, 750, "Annual Inspection Report")
    c.save()
    
    pdf_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    pdf_file.write(pdf_buffer.getvalue())
    pdf_file.close()
    
    return pdf_file.name

def test_annual_inspection_upload(client, auth, app):
    """Test uploading an annual inspection report."""
    auth.login()
    
    # First, ensure we have a forklift to work with
    with app.app_context():
        from app.models.forklift import Forklift
        from app import db
        
        # Check if test forklift exists, if not create it
        forklift = Forklift.query.filter_by(asset_id='ANNUAL-TEST').first()
        if not forklift:
            forklift = Forklift(
                asset_id='ANNUAL-TEST',
                model_number='ANNUAL-MODEL',
                serial_number='ANNUAL-SN',
                forklift_type='reach',
                power_source='battery',
                max_load=1000,
                max_height=3000,
                manufacture_year=2022,
                status='active'
            )
            db.session.add(forklift)
            db.session.commit()
    
    # Create a test PDF file
    pdf_path = create_test_pdf()
    
    try:
        with open(pdf_path, 'rb') as pdf_file:
            # Upload annual inspection report
            response = client.post(
                f'/forklift/{forklift.id}/annual-inspection',
                data={
                    'inspection_date': '2025-03-15',
                    'report_file': (pdf_file, 'annual_inspection.pdf'),
                    'notes': 'Annual inspection test'
                },
                follow_redirects=True
            )
        
        # Check response
        assert response.status_code == 200
        assert b'\xe5\xb9\xb4\xe6\xac\xa1\xe7\x82\xb9\xe6\xa4\x9c\xe3\x83\xac\xe3\x83\x9d\xe3\x83\xbc\xe3\x83\x88\xe3\x82\x92\xe8\xbf\xbd\xe5\x8a\xa0\xe3\x81\x97\xe3\x81\xbe\xe3\x81\x97\xe3\x81\x9f' in response.data  # '年次点検レポートを追加しました' in UTF-8
        
        # Verify annual inspection record was created
        with app.app_context():
            from app.models.inspection import AnnualInspection
            
            inspection = AnnualInspection.query.filter_by(forklift_id=forklift.id).order_by(AnnualInspection.id.desc()).first()
            assert inspection is not None
            assert inspection.notes == 'Annual inspection test'
            assert inspection.report_file is not None
            assert inspection.report_file.endswith('.pdf')
    
    finally:
        # Clean up the test file
        os.unlink(pdf_path)

def test_annual_inspection_view(client, auth, app):
    """Test viewing annual inspection history."""
    auth.login()
    
    # Get a forklift with annual inspection records
    with app.app_context():
        from app.models.forklift import Forklift
        from app.models.inspection import AnnualInspection
        
        # Find a forklift with annual inspection records
        forklift_id = None
        inspection = AnnualInspection.query.first()
        if inspection:
            forklift_id = inspection.forklift_id
        
        if forklift_id:
            # Test viewing the annual inspection history
            response = client.get(f'/forklift/{forklift_id}/annual-inspections')
            assert response.status_code == 200
            assert b'\xe5\xb9\xb4\xe6\xac\xa1\xe7\x82\xb9\xe6\xa4\x9c\xe5\xb1\xa5\xe6\xad\xb4' in response.data  # '年次点検履歴' in UTF-8