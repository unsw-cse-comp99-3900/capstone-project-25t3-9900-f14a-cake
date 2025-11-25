"""Flask test client helper utilities."""
from flask import Flask
from flask.testing import FlaskClient


class AuthClient:
    """Test client wrapper with authentication functionality."""
    
    def __init__(self, client: FlaskClient, token: str):
        self.client = client
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def get(self, url, **kwargs):
        """GET request."""
        headers = kwargs.pop('headers', {})
        headers.update(self.headers)
        return self.client.get(url, headers=headers, **kwargs)
    
    def post(self, url, **kwargs):
        """POST request."""
        headers = kwargs.pop('headers', {})
        headers.update(self.headers)
        return self.client.post(url, headers=headers, **kwargs)
    
    def put(self, url, **kwargs):
        """PUT request."""
        headers = kwargs.pop('headers', {})
        headers.update(self.headers)
        return self.client.put(url, headers=headers, **kwargs)
    
    def delete(self, url, **kwargs):
        """DELETE request."""
        headers = kwargs.pop('headers', {})
        headers.update(self.headers)
        return self.client.delete(url, headers=headers, **kwargs)
    
    def patch(self, url, **kwargs):
        """PATCH request."""
        headers = kwargs.pop('headers', {})
        headers.update(self.headers)
        return self.client.patch(url, headers=headers, **kwargs)

