"""Admin API integration tests."""
import pytest
from models import User, Invoice, db


@pytest.mark.integration
@pytest.mark.admin
class TestAdminUsersAPI:
    """Admin user management API tests."""
    
    def test_get_users_list(self, client, admin_headers, user_factory):
        """Test get user list."""
        # Create several users
        user_factory()
        user_factory()
        
        response = client.get('/api/admin/users', headers=admin_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'Users retrieved successfully'
        assert 'items' in json_data['data']
        assert 'pagination' in json_data['data']
    
    def test_get_users_pagination(self, client, admin_headers, user_factory):
        """Test user list pagination."""
        # Create 15 users
        for _ in range(15):
            user_factory()
        
        response = client.get('/api/admin/users?page=1&per_page=10', headers=admin_headers)
        json_data = response.get_json()
        
        assert len(json_data['data']['items']) == 10
        assert json_data['data']['pagination']['has_next'] is True
    
    def test_get_users_filter_active(self, client, admin_headers, user_factory):
        """Test filter users by active status."""
        user_factory(is_active=True)
        user_factory(is_active=False)
        
        response = client.get('/api/admin/users?is_active=true', headers=admin_headers)
        json_data = response.get_json()
        
        assert all(item['is_active'] is True for item in json_data['data']['items'])
    
    def test_get_users_filter_role(self, client, admin_headers, user_factory):
        """Test filter users by role."""
        user_factory(role='user')
        user_factory(role='admin')
        
        response = client.get('/api/admin/users?role=admin', headers=admin_headers)
        json_data = response.get_json()
        
        assert all(item['role'] == 'admin' for item in json_data['data']['items'])
    
    def test_get_users_unauthorized(self, client, auth_headers):
        """Test regular user access admin endpoint."""
        response = client.get('/api/admin/users', headers=auth_headers)
        
        assert response.status_code == 403
        json_data = response.get_json()
        assert json_data['error'] == 'insufficient_permissions'
    
    def test_toggle_user_status_disable(self, client, admin_headers, user_factory, db_session):
        """Test disable user."""
        user = user_factory(is_active=True)
        
        response = client.put(f'/api/admin/users/{user.id}/toggle', headers=admin_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'disabled' in json_data['message'].lower()
        
        # Verify database was updated
        db_session.refresh(user)
        assert user.is_active is False
    
    def test_toggle_user_status_enable(self, client, admin_headers, user_factory, db_session):
        """Test enable user."""
        user = user_factory(is_active=False)
        
        response = client.put(f'/api/admin/users/{user.id}/toggle', headers=admin_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'enabled' in json_data['message'].lower()
        
        # Verify database was updated
        db_session.refresh(user)
        assert user.is_active is True
    
    def test_toggle_user_status_not_found(self, client, admin_headers):
        """Test disable non-existent user."""
        response = client.put('/api/admin/users/99999/toggle', headers=admin_headers)
        
        assert response.status_code == 404
        json_data = response.get_json()
        assert json_data['error'] == 'user_not_found'
    
    def test_toggle_user_status_self(self, client, admin_headers, admin_user):
        """Test disable self (should fail)."""
        response = client.put(f'/api/admin/users/{admin_user.id}/toggle', headers=admin_headers)
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data['error'] == 'invalid_operation'


@pytest.mark.integration
@pytest.mark.admin
class TestAdminStatsAPI:
    """Admin statistics API tests."""
    
    def test_get_stats_success(self, client, admin_headers, user_factory, invoice_factory):
        """Test get system statistics."""
        # Create some test data
        user1 = user_factory(role='user')
        user2 = user_factory(role='admin')
        invoice_factory(user_id=user1.id, status='ocr_completed')
        invoice_factory(user_id=user1.id, status='xml_generated')
        invoice_factory(user_id=user1.id, status='validated')
        
        response = client.get('/api/admin/stats', headers=admin_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'Statistics retrieved successfully'
        assert 'users' in json_data['data']
        assert 'invoices' in json_data['data']
        
        stats = json_data['data']
        assert 'total' in stats['users']
        assert 'active' in stats['users']
        assert 'admin' in stats['users']
        assert 'total' in stats['invoices']
        assert 'by_status' in stats['invoices']
        assert 'recent_7_days' in stats['invoices']
    
    def test_get_stats_unauthorized(self, client, auth_headers):
        """Test regular user access statistics endpoint."""
        response = client.get('/api/admin/stats', headers=auth_headers)
        
        assert response.status_code == 403
        json_data = response.get_json()
        assert json_data['error'] == 'insufficient_permissions'

