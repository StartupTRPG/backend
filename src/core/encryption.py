import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from src.core.config import settings

class EncryptionService:
    """Bidirectional encryption service"""
    
    def __init__(self):
        self._fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption key"""
        try:
            # Get encryption key from environment variable
            encryption_key = getattr(settings, 'ENCRYPTION_KEY', None)
            
            if not encryption_key:
                raise ValueError("ENCRYPTION_KEY environment variable is not set.")
            
            # Use PBKDF2 for key derivation
            password = encryption_key.encode()
            salt = b'madcamp_salt_2024'  # Use random salt in production
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self._fernet = Fernet(key)
            
        except Exception as e:
            print(f"Encryption initialization error: {e}")
            # Generate default key
            key = Fernet.generate_key()
            self._fernet = Fernet(key)
    
    def encrypt_message(self, message: str) -> str:
        """Encrypt message"""
        try:
            if not message:
                return ""
            
            # Convert string to bytes then encrypt
            encrypted_bytes = self._fernet.encrypt(message.encode('utf-8'))
            
            # Encode with base64 to convert to string
            encrypted_string = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
            
            return encrypted_string
            
        except Exception as e:
            print(f"Encryption error: {e}")
            return message  # Return original if encryption fails
    
    def decrypt_message(self, encrypted_message: str) -> str:
        """Decrypt message"""
        try:
            if not encrypted_message:
                return ""
            
            # Base64 decode
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_message.encode('utf-8'))
            
            # Decrypt then convert to string
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            decrypted_string = decrypted_bytes.decode('utf-8')
            
            return decrypted_string
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_message  # Return original if decryption fails
    
    def hash_message(self, message: str) -> str:
        """Generate message hash (for verification)"""
        try:
            return hashlib.sha256(message.encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"Hash generation error: {e}")
            return ""
    
    def verify_message_integrity(self, message: str, message_hash: str) -> bool:
        """메시지 무결성 검증"""
        try:
            return self.hash_message(message) == message_hash
        except Exception as e:
            print(f"Message integrity verification error: {e}")
            return False

# 싱글톤 인스턴스
encryption_service = EncryptionService() 