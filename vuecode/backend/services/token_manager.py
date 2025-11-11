"""ESS Validator Token管理服务"""
import requests
import os
from datetime import datetime, timedelta


class TokenManager:
    """管理ESS Validator的access token"""
    
    def __init__(self):
        self.token = None
        self.token_expires_at = None
        self.client_id = "7d30bi87iptegbrf2bp37p42gg"
        self.client_secret = "880tema3rvh3h63j4nquvgoh0lgts11n09bq8597fgrkvvd62su"
        self.token_url = "https://dev-eat.auth.eu-central-1.amazoncognito.com/oauth2/token"
    
    def get_token(self):
        """获取有效的token（如果过期则自动刷新）"""
        # 如果token不存在或即将过期，刷新
        if not self.token or not self.token_expires_at or datetime.now() >= self.token_expires_at:
            self.refresh_token()
        
        return self.token
    
    def refresh_token(self):
        """刷新access token"""
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
            expires_in = result.get('expires_in', 3600)  # 默认1小时
            
            # 设置过期时间（提前5分钟刷新）
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            print(f"[TokenManager] Token refreshed successfully (expires in {expires_in}s)")
            
            # 更新.env文件中的token
            self._update_env_file()
            
            return self.token
            
        except Exception as e:
            print(f"[TokenManager] Error refreshing token: {str(e)}")
            raise
    
    def _update_env_file(self):
        """更新.env文件中的token"""
        try:
            env_path = '.env'
            if not os.path.exists(env_path):
                return
            
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 更新或添加ESS_VALIDATOR_TOKEN
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


# 全局token manager实例
_token_manager = None


def get_token_manager():
    """获取token manager实例"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager

