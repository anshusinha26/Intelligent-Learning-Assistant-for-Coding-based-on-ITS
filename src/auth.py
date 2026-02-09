"""
Authentication Module
Handles user registration, login, and JWT token management
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from src.database import Database

SECRET_KEY = "your-secret-key-change-in-production"  # Change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

class AuthService:
    def __init__(self, db: Database):
        self.db = db
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(self, user_id: int, email: str, name: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "exp": expire
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def register_user(self, name: str, email: str, password: str, target_level: str = "medium") -> dict:
        """Register a new user"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            raise ValueError("Email already registered")
        
        # Hash password and insert user
        password_hash = self.hash_password(password)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, target_level)
            VALUES (?, ?, ?, ?)
        """, (name, email, password_hash, target_level))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Create access token
        token = self.create_access_token(user_id, email, name)
        
        return {
            "user_id": user_id,
            "name": name,
            "email": email,
            "access_token": token,
            "token_type": "bearer"
        }
    
    def login_user(self, email: str, password: str) -> dict:
        """Login user and return token"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get user
        cursor.execute("""
            SELECT user_id, name, email, password_hash
            FROM users WHERE email = ?
        """, (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            raise ValueError("Invalid email or password")
        
        # Create token
        token = self.create_access_token(user['user_id'], user['email'], user['name'])
        
        return {
            "user_id": user['user_id'],
            "name": user['name'],
            "email": user['email'],
            "access_token": token,
            "token_type": "bearer"
        }
    
    def get_current_user(self, token: str) -> Optional[dict]:
        """Get current user from token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, name, email, role, target_level
            FROM users WHERE user_id = ?
        """, (payload['user_id'],))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None