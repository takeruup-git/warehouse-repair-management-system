import os
import pytest
import tempfile
import pandas as pd
from io import StringIO
from flask import url_for

def test_csv_upload_page_access(client, auth):
    """Test that the CSV upload page is accessible after login."""
    auth.login()
    response = client.get('/forklift/import')
    assert response.status_code == 200
    assert b'CSV\xe3\x82\xa2\xe3\x83\x83\xe3\x83\x97\xe3\x83\xad\xe3\x83\xbc\xe3\x83\x89' in response.data  # 'CSVアップロード' in UTF-8

def create_test_csv():
    """Create a test CSV file for forklift data."""
    data = {
        '管理番号': ['FL001', 'FL002'],
        '機種': ['リーチ式', 'カウンター式'],
        '型式': ['TEST-R1', 'TEST-C1'],
        '製造番号': ['SN001', 'SN002'],
        '製造年': [2020, 2021],
        '動力': ['バッテリー', 'ディーゼル'],
        '最大荷重': [1000, 2000],
        '最大揚高': [3000, 4000],
        '倉庫': ['倉庫A', '倉庫B'],
        '状態': ['稼働中', '稼働中']
    }
    
    df = pd.DataFrame(data)
    csv_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
    df.to_csv(csv_file.name, index=False, encoding='utf-8')
    csv_file.close()
    
    return csv_file.name

def test_csv_upload_functionality(client, auth, app):
    """Test the CSV upload functionality."""
    auth.login()
    
    # Create a test CSV file
    csv_path = create_test_csv()
    
    try:
        with open(csv_path, 'rb') as csv_file:
            response = client.post(
                '/forklift/import',
                data={
                    'file': (csv_file, 'test_forklifts.csv'),
                },
                follow_redirects=True
            )
        
        # Check response
        assert response.status_code == 200
        assert b'\xe6\x88\x90\xe5\x8a\x9f\xe3\x81\x97\xe3\x81\xbe\xe3\x81\x97\xe3\x81\x9f' in response.data  # '成功しました' in UTF-8
        
        # Verify data was imported
        with app.app_context():
            from app.models.forklift import Forklift
            from app import db
            
            forklifts = Forklift.query.all()
            assert len(forklifts) >= 2
            
            # Check if our test data exists
            fl001 = Forklift.query.filter_by(asset_id='FL001').first()
            assert fl001 is not None
            assert fl001.model_number == 'TEST-R1'
            
            fl002 = Forklift.query.filter_by(asset_id='FL002').first()
            assert fl002 is not None
            assert fl002.model_number == 'TEST-C1'
    
    finally:
        # Clean up the test file
        os.unlink(csv_path)