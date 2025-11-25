"""ESS Validator token management service."""
import requests
import os
from datetime import datetime, timedelta


class TokenManager:
    """Manages ESS Validator access tokens."""
    
    def __init__(self) -> None:
        self.token = None
        self.token_expires_at = None
        self.client_id = os.getenv("ESS_VALIDATOR_CLIENT_ID")
        self.client_secret = os.getenv("ESS_VALIDATOR_CLIENT_SECRET")
        self.token_url = os.getenv("ESS_VALIDATOR_TOKEN_URL")
    
    def get_token(self) -> str:
        """
        Get valid token (automatically refreshes if expired).
        
        Returns:
            Valid access token string
        """
        # Refresh if token doesn't exist or is about to expire
        if not self.token or not self.token_expires_at or datetime.now() >= self.token_expires_at:
            self.refresh_token()
        
        return self.token
    
    def refresh_token(self) -> str:
        """
        Refresh access token.
        
        Returns:
            New access token string
        
        Raises:
            Exception: If token refresh fails
        """
        try:
            print("[TokenManager] Refreshing ESS Validator token...")
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "eat/read"
            }
            
            response = requests.post(
                self.token_url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            if not response.ok:
                raise Exception(f"Token refresh failed: {response.status_code} - {response.text}")
            
            result = response.json()
            self.token = result.get('access_token')
            expires_in = result.get('expires_in', 3600)  # Default 1 hour
            
            # Set expiration time (refresh 5 minutes early)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            print(f"[TokenManager] Token refreshed successfully (expires in {expires_in}s)")
            
            # Update token in .env file
            self._update_env_file()
            
            return self.token
            
        except Exception as e:
            print(f"[TokenManager] Error refreshing token: {str(e)}")
            raise
    
    def _update_env_file(self) -> None:
        """
        Update token in .env file.
        
        Updates or adds ESS_VALIDATOR_TOKEN in the .env file.
        """
        try:
            env_path = '.env'
            if not os.path.exists(env_path):
                return
            
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Update or add ESS_VALIDATOR_TOKEN
            token_found = False
            for i, line in enumerate(lines):
                if line.startswith('ESS_VALIDATOR_TOKEN='):
                    lines[i] = f'ESS_VALIDATOR_TOKEN={self.token}\n'
                    token_found = True
                    break
            
            if not token_found:
                lines.append(f'\nESS_VALIDATOR_TOKEN={self.token}\n')
            
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print("[TokenManager] Updated .env file with new token")
            
        except Exception as e:
            print(f"[TokenManager] Failed to update .env file: {str(e)}")


# Global token manager instance
_token_manager = None


def get_token_manager() -> TokenManager:
    """
    Get token manager instance (singleton pattern).
    
    Returns:
        TokenManager instance
    """
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager

