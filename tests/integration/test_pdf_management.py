import os
import pytest
import tempfile
from flask import url_for
from io import BytesIO
from reportlab.pdfgen import canvas

def create_test_pdf():
    """Create a test PDF file."""
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer)
    c.drawString(100, 750, "Test PDF Document")
    c.save()
    
    pdf_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    pdf_file.write(pdf_buffer.getvalue())
    pdf_file.close()
    
    return pdf_file.name

def test_pdf_upload_functionality(client, auth, app):
    """Test the PDF upload functionality for repair records."""
    auth.login()
    
    # First, create a forklift to attach the PDF to
    with app.app_context():
        from app.models.forklift import Forklift
        from app import db
        
        # Check if test forklift exists, if not create it
        forklift = Forklift.query.filter_by(asset_id='TEST-FL').first()
        if not forklift:
            forklift = Forklift(
                asset_id='TEST-FL',
                model_number='TEST-MODEL',
                serial_number='TEST-SN',
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
            # Add a repair record with PDF attachment
            response = client.post(
                f'/forklift/{forklift.id}/repair/add',
                data={
                    'repair_date': '2025-03-15',
                    'repair_reason': 'failure',
                    'repair_target': 'battery',
                    'repair_action': 'X',
                    'cost': '50000',
                    'description': 'Test repair with PDF attachment',
                    'report_file': (pdf_file, 'test_report.pdf')
                },
                follow_redirects=True
            )
        
        # Check response
        assert response.status_code == 200
        assert b'\xe4\xbf\xae\xe7\xb9\x95\xe8\xa8\x98\xe9\x8c\xb2\xe3\x82\x92\xe8\xbf\xbd\xe5\x8a\xa0\xe3\x81\x97\xe3\x81\xbe\xe3\x81\x97\xe3\x81\x9f' in response.data  # '修繕記録を追加しました' in UTF-8
        
        # Verify repair record was created with PDF
        with app.app_context():
            from app.models.forklift import ForkliftRepair
            
            repair = ForkliftRepair.query.filter_by(forklift_id=forklift.id).order_by(ForkliftRepair.id.desc()).first()
            assert repair is not None
            assert repair.description == 'Test repair with PDF attachment'
            assert repair.report_file is not None
            assert repair.report_file.endswith('.pdf')
    
    finally:
        # Clean up the test file
        os.unlink(pdf_path)

def test_pdf_view_functionality(client, auth, app):
    """Test the PDF viewing functionality."""
    auth.login()
    
    # Get the latest repair record with a PDF
    with app.app_context():
        from app.models.forklift import ForkliftRepair
        
        repair = ForkliftRepair.query.filter(ForkliftRepair.report_file.isnot(None)).order_by(ForkliftRepair.id.desc()).first()
        
        if repair:
            # Test viewing the PDF
            response = client.get(f'/repair/forklift/{repair.id}/report')
            assert response.status_code == 200
            assert response.mimetype == 'application/pdf'