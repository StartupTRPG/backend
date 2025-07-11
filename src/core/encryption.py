import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
from typing import Optional
from src.core.config import settings

class EncryptionService:
    """양방향 암호화 서비스"""
    
    def __init__(self):
        self._fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """암호화 키 초기화"""
        try:
            # 환경변수에서 암호화 키 가져오기
            encryption_key = getattr(settings, 'ENCRYPTION_KEY', None)
            
            if not encryption_key:
                raise ValueError("ENCRYPTION_KEY 환경변수가 설정되지 않았습니다.")
            
            # PBKDF2를 사용해 키 파생
            password = encryption_key.encode()
            salt = b'madcamp_salt_2024'  # 실제 운영환경에서는 랜덤 salt 사용
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self._fernet = Fernet(key)
            
        except Exception as e:
            print(f"암호화 초기화 오류: {e}")
            # 기본 키 생성
            key = Fernet.generate_key()
            self._fernet = Fernet(key)
    
    def encrypt_message(self, message: str) -> str:
        """메시지 암호화"""
        try:
            if not message:
                return ""
            
            # 문자열을 바이트로 변환 후 암호화
            encrypted_bytes = self._fernet.encrypt(message.encode('utf-8'))
            
            # base64로 인코딩하여 문자열로 변환
            encrypted_string = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
            
            return encrypted_string
            
        except Exception as e:
            print(f"메시지 암호화 오류: {e}")
            return message  # 암호화 실패 시 원본 반환
    
    def decrypt_message(self, encrypted_message: str) -> str:
        """메시지 복호화"""
        try:
            if not encrypted_message:
                return ""
            
            # base64 디코딩
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_message.encode('utf-8'))
            
            # 복호화 후 문자열로 변환
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            decrypted_string = decrypted_bytes.decode('utf-8')
            
            return decrypted_string
            
        except Exception as e:
            print(f"메시지 복호화 오류: {e}")
            return encrypted_message  # 복호화 실패 시 원본 반환
    
    def hash_message(self, message: str) -> str:
        """메시지 해시 생성 (검증용)"""
        try:
            return hashlib.sha256(message.encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"메시지 해시 생성 오류: {e}")
            return ""
    
    def verify_message_integrity(self, message: str, message_hash: str) -> bool:
        """메시지 무결성 검증"""
        try:
            return self.hash_message(message) == message_hash
        except Exception as e:
            print(f"메시지 무결성 검증 오류: {e}")
            return False

# 싱글톤 인스턴스
encryption_service = EncryptionService() 