from cryptography.fernet import Fernet
from src.core.config import settings
import base64

class CryptoManager:
    def __init__(self):
        # 키 생성 또는 설정에서 가져오기
        key = settings.ENCRYPTION_KEY.encode() if hasattr(settings, 'ENCRYPTION_KEY') else Fernet.generate_key()
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """데이터 암호화"""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """데이터 복호화"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()

crypto_manager = CryptoManager() 