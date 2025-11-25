"""OCR and XML API integration tests."""
import pytest
import json
import responses
from models import Invoice


@pytest.mark.integration
@pytest.mark.slow
class TestOCRAPI:
    """OCR API tests."""
    
    @responses.activate
    def test_ocr_success(self, client, auth_headers, test_user, app):
        """Test successful OCR processing."""
        # Mock Veryfi API response
        mock_ocr_response = {
            'document_type': 'invoice',
            'invoice_number': 'INV-001',
            'date': '2024-01-15',
            'total': 100.50,
            'vendor': {'name': 'Test Vendor'},
            'bill_to': {'name': 'Test Customer'},
            'line_items': [
                {'description': 'Item 1', 'quantity': 1, 'price': 100.50, 'total': 100.50}
            ],
            'subtotal': 100.50,
            'tax': 0,
            'total': 100.50
        }
        
        responses.add(
            responses.POST,
            'https://api.veryfi.com/api/v8/partner/documents/',
            json=mock_ocr_response,
            status=200
        )
        
        # Create test file
        from io import BytesIO
        file_data = BytesIO(b'fake pdf content')
        file_data.name = 'test_invoice.pdf'
        
        response = client.post(
            '/api/ocr',
            data={'file': (file_data, 'test_invoice.pdf')},
            headers=auth_headers,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'Document processed successfully'
        assert 'invoice_id' in json_data['data']
        assert 'raw_data' in json_data['data']
        assert 'extracted' in json_data['data']
        
        # Verify invoice record was created
        invoice_id = json_data['data']['invoice_id']
        from models import db
        with app.app_context():
            invoice = db.session.get(Invoice, invoice_id)
            assert invoice is not None
            assert invoice.user_id == test_user.id
            assert invoice.status == 'ocr_completed'
    
    def test_ocr_unauthorized(self, client):
        """Test unauthorized OCR request."""
        from io import BytesIO
        file_data = BytesIO(b'fake pdf content')
        file_data.name = 'test.pdf'
        
        response = client.post(
            '/api/ocr',
            data={'file': (file_data, 'test.pdf')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 401
    
    def test_ocr_invalid_file_type(self, client, auth_headers):
        """Test invalid file type."""
        from io import BytesIO
        file_data = BytesIO(b'fake content')
        file_data.name = 'test.txt'
        
        response = client.post(
            '/api/ocr',
            data={'file': (file_data, 'test.txt')},
            headers=auth_headers,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert json_data['error'] == 'validation_error'


@pytest.mark.integration
class TestXMLAPI:
    """XML API tests."""
    
    def test_generate_xml_success(self, client, auth_headers, test_user, invoice_factory):
        """Test successful XML generation."""
        invoice = invoice_factory(user_id=test_user.id)
        
        data = {
            'invoice_id': invoice.id,
            'invoice_info': {
                'invoice_number': 'INV-001',
                'issue_date': '2024-01-15',
                'currency_code': 'AUD'
            },
            'supplier': {'name': 'Test Supplier'},
            'customer': {'name': 'Test Customer'},
            'line_items': [
                {'name': 'Item 1', 'quantity': 1, 'unit_price': 100, 'line_total': 100}
            ],
            'summary': {'subtotal': 100, 'tax_amount': 10, 'total': 110}
        }
        
        response = client.post('/api/generate-xml', json=data, headers=auth_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'XML generated successfully'
        assert 'xml_content' in json_data['data']
        assert 'filename' in json_data['data']
        
        # Verify invoice record was updated
        from models import db
        db.session.refresh(invoice)
        assert invoice.xml_content is not None
        assert invoice.status == 'xml_generated'
    
    def test_generate_xml_without_invoice_id(self, client, auth_headers):
        """Test XML generation without invoice_id."""
        data = {
            'invoice_info': {'invoice_number': 'INV-001'},
            'supplier': {'name': 'Test Supplier'},
            'customer': {'name': 'Test Customer'},
            'line_items': [],
            'summary': {'subtotal': 0, 'tax_amount': 0, 'total': 0}
        }
        
        response = client.post('/api/generate-xml', json=data, headers=auth_headers)
        
        assert response.status_code == 200
        # Should still successfully generate XML, but not update invoice record
    

    '''Commented due to token needed'''
    # @responses.activate
    # def test_validate_xml_success(self, client, auth_headers, test_user, invoice_factory, db_session):
    #     """Test successful XML validation."""
    #     invoice = invoice_factory(user_id=test_user.id)
    #     invoice.xml_content = '<?xml version="1.0"?><invoice>test</invoice>'
    #     db_session.commit()
        
    #     # Mock ESS Validator API response
    #     mock_validation_response = {
    #         'success': True,
    #         'valid': True,
    #         'results': {}
    #     }
        
    #     responses.add(
    #         responses.POST,
    #         'https://validator.ess.digital/api/validate',
    #         json=mock_validation_response,
    #         status=200
    #     )
        
    #     data = {
    #         'xml_content': invoice.xml_content,
    #         'invoice_id': invoice.id
    #     }
        
    #     response = client.post('/api/validate-xml', json=data, headers=auth_headers)
        
    #     assert response.status_code == 200
    #     json_data = response.get_json()
    #     assert json_data['success'] is True
        
    #     # Verify invoice record was updated
    #     db_session.refresh(invoice)
    #     assert invoice.validation_result is not None
    #     assert invoice.status == 'validated'
    
    def test_validate_xml_unauthorized(self, client):
        """Test unauthorized XML validation."""
        data = {'xml_content': '<?xml version="1.0"?><invoice>test</invoice>'}
        
        response = client.post('/api/validate-xml', json=data)
        
        assert response.status_code == 401
    
    def test_upload_xml_success(self, client, auth_headers):
        """Test XML file upload."""
        from io import BytesIO
        xml_content = '<?xml version="1.0"?><invoice>test</invoice>'
        file_data = BytesIO(xml_content.encode('utf-8'))
        file_data.name = 'test.xml'
        
        response = client.post(
            '/api/upload-xml',
            data={'file': (file_data, 'test.xml')},
            headers=auth_headers,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['message'] == 'XML file uploaded successfully'
        assert 'xml_content' in json_data['data']
    
    def test_download_json_success(self, client, auth_headers, app, test_user):
        """Test download JSON file."""
        import os
        import json
        
        # Create test JSON file
        test_data = {'test': 'data'}
        test_filename = 'test_result.json'
        test_path = os.path.join(app.config['UPLOAD_FOLDER'], test_filename)
        
        with open(test_path, 'w') as f:
            json.dump(test_data, f)
        
        try:
            response = client.get(f'/api/download-json/{test_filename}', headers=auth_headers)
            
            assert response.status_code == 200
            assert response.content_type == 'application/json'
        finally:
            if response:
                try:
                    response.close()    # Close connection to release file handle
                except Exception:
                    pass
            if os.path.exists(test_path):
                # Windows needs to wait for handle release
                for _ in range(3):
                    try:
                        os.remove(test_path)
                        break
                    except:
                        raise PermissionError
    
    def test_download_json_not_found(self, client, auth_headers):
        """Test download non-existent JSON file."""
        response = client.get('/api/download-json/nonexistent.json', headers=auth_headers)
        
        assert response.status_code == 404
        json_data = response.get_json()
        assert json_data['error'] == 'file_not_found'

