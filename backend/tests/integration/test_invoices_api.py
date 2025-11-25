"""Invoice API integration tests."""
import pytest
from models import Invoice, db


@pytest.mark.integration
class TestInvoicesAPI:
    """Invoice API tests."""
    
    def test_get_my_invoices_success(self, client, auth_headers, test_user, invoice_factory):
        """Test get current user invoice list."""
        # Create several invoices
        invoice1 = invoice_factory(user_id=test_user.id)
        invoice2 = invoice_factory(user_id=test_user.id)
        
        response = client.get('/api/invoices', headers=auth_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'Invoices retrieved successfully'
        assert 'items' in json_data['data']
        assert 'pagination' in json_data['data']
        assert len(json_data['data']['items']) == 2
    
    def test_get_my_invoices_pagination(self, client, auth_headers, test_user, invoice_factory):
        """Test invoice list pagination."""
        # Create 15 invoices
        for _ in range(15):
            invoice_factory(user_id=test_user.id)
        
        # First page
        response = client.get('/api/invoices?page=1&per_page=10', headers=auth_headers)
        json_data = response.get_json()
        assert len(json_data['data']['items']) == 10
        assert json_data['data']['pagination']['has_next'] is True
        
        # Second page
        response = client.get('/api/invoices?page=2&per_page=10', headers=auth_headers)
        json_data = response.get_json()
        assert len(json_data['data']['items']) == 5
        assert json_data['data']['pagination']['has_next'] is False
    
    def test_get_my_invoices_status_filter(self, client, auth_headers, test_user, invoice_factory):
        """Test invoice status filter."""
        invoice_factory(user_id=test_user.id, status='ocr_completed')
        invoice_factory(user_id=test_user.id, status='xml_generated')
        invoice_factory(user_id=test_user.id, status='validated')
        
        response = client.get('/api/invoices?status=ocr_completed', headers=auth_headers)
        json_data = response.get_json()
        
        assert len(json_data['data']['items']) == 1
        assert json_data['data']['items'][0]['status'] == 'ocr_completed'
    
    def test_get_my_invoices_unauthorized(self, client):
        """Test unauthorized invoice list access."""
        response = client.get('/api/invoices')
        
        assert response.status_code == 401
    
    def test_get_invoice_detail_success(self, client, auth_headers, test_user, invoice_factory):
        """Test get invoice details."""
        invoice = invoice_factory(user_id=test_user.id)
        
        response = client.get(f'/api/invoices/{invoice.id}', headers=auth_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'Invoice retrieved successfully'
        assert json_data['data']['invoice']['id'] == invoice.id
    
    def test_get_invoice_detail_not_found(self, client, auth_headers):
        """Test get non-existent invoice."""
        response = client.get('/api/invoices/99999', headers=auth_headers)
        
        assert response.status_code == 404
        json_data = response.get_json()
        assert json_data['error'] == 'invoice_not_found'
    
    def test_get_invoice_detail_other_user(self, client, auth_headers, test_user, user_factory, invoice_factory):
        """Test get other user's invoice (should fail)."""
        other_user = user_factory()
        invoice = invoice_factory(user_id=other_user.id)
        
        response = client.get(f'/api/invoices/{invoice.id}', headers=auth_headers)
        
        assert response.status_code == 404
        json_data = response.get_json()
        assert json_data['error'] == 'invoice_not_found'


@pytest.mark.integration
@pytest.mark.admin
class TestAdminInvoicesAPI:
    """Admin invoice API tests."""
    
    def test_get_all_invoices_admin(self, client, admin_headers, test_user, user_factory, invoice_factory):
        """Test admin get all invoices."""
        other_user = user_factory()
        
        # Create invoices for two users
        invoice_factory(user_id=test_user.id)
        invoice_factory(user_id=other_user.id)
        
        response = client.get('/api/admin/invoices', headers=admin_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data['data']['items']) == 2
    
    def test_get_all_invoices_user_filter(self, client, admin_headers, test_user, user_factory, invoice_factory):
        """Test admin filter invoices by user."""
        other_user = user_factory()
        
        invoice_factory(user_id=test_user.id)
        invoice_factory(user_id=other_user.id)
        
        response = client.get(f'/api/admin/invoices?user_id={test_user.id}', headers=admin_headers)
        json_data = response.get_json()
        
        assert len(json_data['data']['items']) == 1
        assert json_data['data']['items'][0]['user_id'] == test_user.id
    
    def test_get_all_invoices_unauthorized(self, client, auth_headers):
        """Test regular user access admin endpoint."""
        response = client.get('/api/admin/invoices', headers=auth_headers)
        
        assert response.status_code == 403
        json_data = response.get_json()
        assert json_data['error'] == 'insufficient_permissions'

