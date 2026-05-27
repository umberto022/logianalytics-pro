import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

class Database:
    def __init__(self, db_path: str = "logi_analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos con las tablas necesarias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                company_name TEXT,
                phone TEXT,
                subscription_plan TEXT DEFAULT 'basic'
            )
        ''')
        
        # Tabla de sesiones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabla de envíos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_number TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                weight REAL NOT NULL,
                volume REAL NOT NULL,
                priority TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                cost REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                estimated_delivery TIMESTAMP,
                actual_delivery TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabla de rutas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                distance REAL NOT NULL,
                estimated_time REAL NOT NULL,
                cost_per_km REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabla de inventario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                sku TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                current_stock INTEGER NOT NULL,
                min_stock INTEGER NOT NULL,
                max_stock INTEGER NOT NULL,
                unit_cost REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Crear usuario administrador por defecto
        self.create_default_admin()
    
    def create_default_admin(self):
        """Crea un usuario administrador por defecto"""
        admin_exists = self.get_user_by_username("admin")
        if not admin_exists:
            self.create_user(
                username="admin",
                email="admin@logianalytics.com",
                full_name="Administrador",
                password="admin123",
                role="admin",
                company_name="LogiAnalytics Pro"
            )
    
    def hash_password(self, password: str) -> str:
        """Hashea una contraseña usando SHA-256 con salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica una contraseña contra su hash"""
        try:
            salt, hash_part = password_hash.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == hash_part
        except:
            return False
    
    def create_user(self, username: str, email: str, full_name: str, password: str, 
                   role: str = "user", company_name: str = None, phone: str = None) -> bool:
        """Crea un nuevo usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, email, full_name, password_hash, role, company_name, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, full_name, password_hash, role, company_name, phone))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False  # Usuario o email ya existe
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Obtiene un usuario por nombre de usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, full_name, password_hash, role, is_active, 
                   created_at, last_login, company_name, phone, subscription_plan
            FROM users WHERE username = ?
        ''', (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3],
                'password_hash': row[4],
                'role': row[5],
                'is_active': bool(row[6]),
                'created_at': row[7],
                'last_login': row[8],
                'company_name': row[9],
                'phone': row[10],
                'subscription_plan': row[11]
            }
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtiene un usuario por email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, full_name, password_hash, role, is_active, 
                   created_at, last_login, company_name, phone, subscription_plan
            FROM users WHERE email = ?
        ''', (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3],
                'password_hash': row[4],
                'role': row[5],
                'is_active': bool(row[6]),
                'created_at': row[7],
                'last_login': row[8],
                'company_name': row[9],
                'phone': row[10],
                'subscription_plan': row[11]
            }
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autentica un usuario"""
        user = self.get_user_by_username(username)
        if user and user['is_active'] and self.verify_password(password, user['password_hash']):
            # Actualizar último login
            self.update_last_login(user['id'])
            return user
        return None
    
    def update_last_login(self, user_id: int):
        """Actualiza el último login del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def create_session(self, user_id: int) -> str:
        """Crea una nueva sesión para el usuario"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)  # Sesión válida por 7 días
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, session_token, expires_at))
        
        conn.commit()
        conn.close()
        
        return session_token
    
    def get_user_by_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Obtiene un usuario por token de sesión"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.full_name, u.role, u.is_active, 
                   u.created_at, u.last_login, u.company_name, u.phone, u.subscription_plan
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.is_active = 1 AND s.expires_at > CURRENT_TIMESTAMP
        ''', (session_token,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3],
                'role': row[4],
                'is_active': bool(row[5]),
                'created_at': row[6],
                'last_login': row[7],
                'company_name': row[8],
                'phone': row[9],
                'subscription_plan': row[10]
            }
        return None
    
    def logout_session(self, session_token: str):
        """Cierra una sesión"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions SET is_active = 0 WHERE session_token = ?
        ''', (session_token,))
        
        conn.commit()
        conn.close()
    
    def get_all_users(self) -> list:
        """Obtiene todos los usuarios (solo para administradores)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, full_name, role, is_active, 
                   created_at, last_login, company_name, phone, subscription_plan
            FROM users ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3],
                'role': row[4],
                'is_active': bool(row[5]),
                'created_at': row[6],
                'last_login': row[7],
                'company_name': row[8],
                'phone': row[9],
                'subscription_plan': row[10]
            })
        
        return users
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Actualiza un usuario"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construir query dinámicamente
            fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['username', 'email', 'full_name', 'role', 'company_name', 'phone', 'subscription_plan']:
                    fields.append(f"{key} = ?")
                    values.append(value)
                elif key == 'password':
                    fields.append("password_hash = ?")
                    values.append(self.hash_password(value))
                elif key == 'is_active':
                    fields.append("is_active = ?")
                    values.append(value)
            
            if fields:
                values.append(user_id)
                query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
                cursor.execute(query, values)
                
                conn.commit()
                conn.close()
                return True
            
            conn.close()
            return False
        except:
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """Elimina un usuario (soft delete)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET is_active = 0 WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
