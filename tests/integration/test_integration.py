import pytest
from flask import url_for

def test_complete_workflow(client, auth, app):
    """Test a complete workflow that integrates all features."""
    # 1. Login
    auth.login()
    
    # 2. Select operator
    client.post(
        '/operator/select',
        data={'operator_name': 'Integration Test Operator'},
        follow_redirects=True
    )
    
    # 3. Check dashboard
    response = client.get('/')
    assert response.status_code == 200
    assert b'\xe3\x83\x80\xe3\x83\x83\xe3\x82\xb7\xe3\x83\xa5\xe3\x83\x9c\xe3\x83\xbc\xe3\x83\x89' in response.data  # 'ダッシュボード' in UTF-8
    
    # 4. Create a new forklift
    response = client.post(
        '/forklift/create',
        data={
            'asset_id': 'INT-TEST-FL',
            'model_number': 'INT-MODEL',
            'serial_number': 'INT-SN',
            'forklift_type': 'reach',
            'power_source': 'battery',
            'max_load': '1000',
            'max_height': '3000',
            'manufacture_year': '2022',
            'status': 'active',
            'warehouse': 'Test Warehouse'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'\xe3\x83\x95\xe3\x82\xa9\xe3\x83\xbc\xe3\x82\xaf\xe3\x83\xaa\xe3\x83\x95\xe3\x83\x88\xe3\x82\x92\xe8\xbf\xbd\xe5\x8a\xa0\xe3\x81\x97\xe3\x81\xbe\xe3\x81\x97\xe3\x81\x9f' in response.data  # 'フォークリフトを追加しました' in UTF-8
    
    # Get the forklift ID
    with app.app_context():
        from app.models.forklift import Forklift
        forklift = Forklift.query.filter_by(asset_id='INT-TEST-FL').first()
        assert forklift is not None
        forklift_id = forklift.id
    
    # 5. Add a repair record
    response = client.post(
        f'/forklift/{forklift_id}/repair/add',
        data={
            'repair_date': '2025-03-15',
            'repair_reason': 'failure',
            'repair_target': 'battery',
            'repair_action': 'X',
            'cost': '50000',
            'description': 'Integration test repair'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'\xe4\xbf\xae\xe7\xb9\x95\xe8\xa8\x98\xe9\x8c\xb2\xe3\x82\x92\xe8\xbf\xbd\xe5\x8a\xa0\xe3\x81\x97\xe3\x81\xbe\xe3\x81\x97\xe3\x81\x9f' in response.data  # '修繕記録を追加しました' in UTF-8
    
    # 6. Check forklift details
    response = client.get(f'/forklift/{forklift_id}')
    assert response.status_code == 200
    assert b'INT-TEST-FL' in response.data
    assert b'Integration test repair' in response.data
    
    # 7. Generate inspection format
    response = client.get('/forklift/inspection-format')
    assert response.status_code == 200
    assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    # 8. Check reports
    response = client.get('/report')
    assert response.status_code == 200
    assert b'\xe3\x83\xac\xe3\x83\x9d\xe3\x83\xbc\xe3\x83\x88' in response.data  # 'レポート' in UTF-8
    
    # 9. Logout
    auth.logout()
    response = client.get('/', follow_redirects=True)
    assert b'\xe3\x83\xad\xe3\x82\xb0\xe3\x82\xa4\xe3\x83\xb3' in response.data  # 'ログイン' in UTF-8