import pytest
from flask import url_for

def test_dashboard_access(client, auth):
    """Test that the dashboard is accessible after login."""
    auth.login()
    response = client.get('/')
    assert response.status_code == 200
    assert b'\xe3\x83\x80\xe3\x83\x83\xe3\x82\xb7\xe3\x83\xa5\xe3\x83\x9c\xe3\x83\xbc\xe3\x83\x89' in response.data  # 'ダッシュボード' in UTF-8

def test_dashboard_summary_data(client, auth, app):
    """Test that the dashboard displays summary data."""
    auth.login()
    response = client.get('/')
    assert response.status_code == 200
    
    # Check for summary sections
    assert b'\xe3\x83\x95\xe3\x82\xa9\xe3\x83\xbc\xe3\x82\xaf\xe3\x83\xaa\xe3\x83\x95\xe3\x83\x88\xe7\xb7\x8f\xe6\x95\xb0' in response.data  # 'フォークリフト総数' in UTF-8
    assert b'\xe4\xbf\xae\xe7\xb9\x95\xe4\xbb\xb6\xe6\x95\xb0' in response.data  # '修繕件数' in UTF-8
    
def test_dashboard_charts(client, auth):
    """Test that the dashboard displays charts."""
    auth.login()
    response = client.get('/')
    assert response.status_code == 200
    
    # Check for chart elements
    assert b'chart' in response.data.lower()
    assert b'canvas' in response.data.lower()
    
def test_dashboard_recent_repairs(client, auth, app):
    """Test that the dashboard displays recent repairs."""
    auth.login()
    response = client.get('/')
    assert response.status_code == 200
    
    # Check for recent repairs section
    assert b'\xe6\x9c\x80\xe8\xbf\x91\xe3\x81\xae\xe4\xbf\xae\xe7\xb9\x95' in response.data  # '最近の修繕' in UTF-8