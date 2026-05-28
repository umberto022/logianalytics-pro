import sqlite3
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = "logi_analytics.db"


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        conn = self._conn()
        c = conn.cursor()

        # Migrate old schema if needed
        c.execute("PRAGMA table_info(users)")
        existing_cols = [row[1] for row in c.fetchall()]
        if existing_cols and "email" not in existing_cols:
            for tbl in ["sessions", "user_sessions", "inventory_movements",
                        "sales", "inventory", "users"]:
                c.execute(f"DROP TABLE IF EXISTS {tbl}")
            conn.commit()

        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT DEFAULT '',
            password_hash TEXT NOT NULL,
            phone TEXT DEFAULT '',
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            subscription_plan TEXT DEFAULT 'free',
            company_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            last_login TEXT
        );

        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rif TEXT DEFAULT '',
            address TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            industry TEXT DEFAULT '',
            country TEXT DEFAULT '',
            owner_id INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_id INTEGER,
            sku TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            color TEXT DEFAULT '',
            supplier TEXT DEFAULT '',
            current_stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 0,
            max_stock INTEGER DEFAULT 200,
            unit_cost REAL DEFAULT 0.0,
            sale_price REAL DEFAULT 0.0,
            daily_demand REAL,
            lead_time_days INTEGER DEFAULT 7,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, sku)
        );

        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_id INTEGER,
            inventory_id INTEGER,
            sku TEXT DEFAULT '',
            product_name TEXT DEFAULT '',
            category TEXT DEFAULT '',
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            unit_cost REAL DEFAULT 0.0,
            route TEXT DEFAULT '',
            zone TEXT DEFAULT '',
            client TEXT DEFAULT '',
            sale_date TEXT DEFAULT (datetime('now')),
            total_revenue REAL DEFAULT 0.0,
            total_cost REAL DEFAULT 0.0,
            profit REAL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS inventory_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            reference TEXT DEFAULT '',
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)

        # Migrate: add color column if missing
        try:
            conn.execute("ALTER TABLE inventory ADD COLUMN color TEXT DEFAULT ''")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # Trigger: auto-decrease stock and log movement on every sale
        c.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_sale_auto_inventory
        AFTER INSERT ON sales
        WHEN NEW.inventory_id IS NOT NULL
        BEGIN
            UPDATE inventory
            SET current_stock = MAX(0, current_stock - NEW.quantity),
                updated_at = datetime('now')
            WHERE id = NEW.inventory_id AND user_id = NEW.user_id;

            INSERT INTO inventory_movements
                (inventory_id, user_id, movement_type, quantity, reference, note)
            VALUES
                (NEW.inventory_id, NEW.user_id, 'sale', -NEW.quantity,
                 'Venta #' || NEW.id,
                 NEW.product_name || ' x' || NEW.quantity || ' @ $' || NEW.unit_price);
        END;
        """)

        conn.commit()
        conn.close()
        self._create_default_admin()

    def _create_default_admin(self):
        if not self.get_user_by_username("admin"):
            self.register_user("admin", "admin@logianalytics.com",
                               "Administrador", "Admin123!", phone="")

    # ─────────────────────────────── PASSWORDS ────────────────────────────────

    @staticmethod
    def _hash(pw: str) -> str:
        return hashlib.sha256(pw.encode()).hexdigest()

    def verify_password(self, pw: str, hashed: str) -> bool:
        return self._hash(pw) == hashed

    # ─────────────────────────────── USERS ────────────────────────────────────

    def register_user(self, username: str, email: str, full_name: str,
                      password: str, phone: str = "") -> tuple:
        try:
            conn = self._conn()
            conn.execute(
                "INSERT INTO users (username,email,full_name,password_hash,phone) VALUES (?,?,?,?,?)",
                (username.strip(), email.strip().lower(), full_name.strip(),
                 self._hash(password), phone),
            )
            conn.commit()
            conn.close()
            return True, "Cuenta creada exitosamente"
        except sqlite3.IntegrityError:
            return False, "El usuario o email ya está registrado"

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        conn = self._conn()
        c = conn.cursor()
        c.execute(
            "SELECT * FROM users WHERE (username=? OR email=?) AND is_active=1",
            (username, username.lower()),
        )
        row = c.fetchone()
        if not row or row[4] != self._hash(password):
            conn.close()
            return None
        conn.execute("UPDATE users SET last_login=datetime('now') WHERE id=?", (row[0],))
        conn.commit()
        conn.close()
        return self._user_with_company(self._user_dict(row))

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        return self._user_with_company(self._user_dict(row)) if row else None

    def get_user_by_username(self, username: str) -> Optional[dict]:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        d = self._user_dict(row)
        d["password_hash"] = row[4]
        return d

    def update_user(self, user_id: int, email=None, full_name=None,
                    phone=None, password=None, company_id=None,
                    company_name=None) -> bool:
        sets, vals = [], []
        if email is not None:
            sets.append("email=?"); vals.append(email)
        if full_name is not None:
            sets.append("full_name=?"); vals.append(full_name)
        if phone is not None:
            sets.append("phone=?"); vals.append(phone)
        if company_id is not None:
            sets.append("company_id=?"); vals.append(company_id)
        if password:
            sets.append("password_hash=?"); vals.append(self._hash(password))
        if sets:
            vals.append(user_id)
            conn = self._conn()
            conn.execute(f"UPDATE users SET {','.join(sets)} WHERE id=?", vals)
            conn.commit()
            conn.close()
        if company_name:
            user = self.get_user_by_id(user_id)
            if user and user.get("company_id"):
                self.update_company(user["company_id"], name=company_name)
        return True

    def get_all_users(self) -> list:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        return [self._user_dict(r) for r in rows]

    def _user_with_company(self, d: dict) -> dict:
        if d.get("company_id"):
            company = self.get_company(d["company_id"])
            d["company_name"] = company["name"] if company else ""
        else:
            d["company_name"] = ""
        return d

    @staticmethod
    def _user_dict(row) -> dict:
        cols = ["id", "username", "email", "full_name", "password_hash", "phone",
                "role", "is_active", "subscription_plan", "company_id",
                "created_at", "last_login"]
        d = dict(zip(cols, row))
        d.pop("password_hash", None)
        return d

    # ─────────────────────────────── SESSIONS ─────────────────────────────────

    def create_session(self, user_id: int) -> str:
        token = secrets.token_hex(32)
        expires = (datetime.now() + timedelta(hours=12)).isoformat()
        conn = self._conn()
        conn.execute(
            "INSERT INTO sessions (user_id,token,expires_at) VALUES (?,?,?)",
            (user_id, token, expires),
        )
        conn.commit()
        conn.close()
        return token

    def delete_session(self, token: str) -> None:
        conn = self._conn()
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
        conn.close()

    # ─────────────────────────────── COMPANIES ────────────────────────────────

    def register_company(self, owner_id: int, name: str, rif: str = "",
                         address: str = "", phone: str = "", email: str = "",
                         industry: str = "", country: str = "") -> tuple:
        try:
            conn = self._conn()
            c = conn.cursor()
            c.execute(
                "INSERT INTO companies (name,owner_id,rif,address,phone,email,industry,country) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (name.strip(), owner_id, rif, address, phone, email, industry, country),
            )
            cid = c.lastrowid
            conn.execute("UPDATE users SET company_id=? WHERE id=?", (cid, owner_id))
            conn.commit()
            conn.close()
            return True, cid
        except Exception:
            return False, 0

    def get_company(self, company_id: int) -> Optional[dict]:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT * FROM companies WHERE id=?", (company_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        cols = ["id", "name", "rif", "address", "phone", "email",
                "industry", "country", "owner_id", "created_at"]
        return dict(zip(cols, row))

    def update_company(self, company_id: int, **kw) -> bool:
        allowed = {"name", "rif", "address", "phone", "email", "industry", "country"}
        sets = [(k, v) for k, v in kw.items() if k in allowed]
        if not sets:
            return True
        conn = self._conn()
        conn.execute(
            f"UPDATE companies SET {','.join(f'{k}=?' for k,_ in sets)} WHERE id=?",
            [v for _, v in sets] + [company_id],
        )
        conn.commit()
        conn.close()
        return True

    # ─────────────────────────────── INVENTORY ────────────────────────────────

    def list_inventory(self, user_id: int) -> list:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT * FROM inventory WHERE user_id=? ORDER BY category, name", (user_id,))
        rows = c.fetchall()
        conn.close()
        cols = ["id", "user_id", "company_id", "sku", "name", "category", "color",
                "supplier", "current_stock", "min_stock", "max_stock", "unit_cost",
                "sale_price", "daily_demand", "lead_time_days", "updated_at"]
        return [dict(zip(cols, r)) for r in rows]

    def add_inventory_item(self, user_id: int, sku: str, name: str, category: str,
                           current_stock: int, min_stock: int, max_stock: int,
                           unit_cost: float, daily_demand=None, lead_time_days: int = 7,
                           supplier: str = "", sale_price: float = 0.0,
                           company_id=None, color: str = "") -> tuple:
        try:
            conn = self._conn()
            c = conn.cursor()
            c.execute(
                "INSERT INTO inventory (user_id,company_id,sku,name,category,color,supplier,"
                "current_stock,min_stock,max_stock,unit_cost,sale_price,daily_demand,lead_time_days) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (user_id, company_id, sku, name, category, color, supplier, current_stock,
                 min_stock, max_stock, unit_cost, sale_price, daily_demand, lead_time_days),
            )
            inv_id = c.lastrowid
            if current_stock > 0:
                conn.execute(
                    "INSERT INTO inventory_movements (inventory_id,user_id,movement_type,quantity,note) "
                    "VALUES (?,?,'purchase',?,'Stock inicial')",
                    (inv_id, user_id, current_stock),
                )
            conn.commit()
            conn.close()
            return True, f"'{name}' agregado"
        except sqlite3.IntegrityError:
            return False, f"SKU '{sku}' ya existe"

    def update_inventory_item(self, item_id: int, user_id: int, sku: str, name: str,
                               category: str, current_stock: int, min_stock: int,
                               max_stock: int, unit_cost: float, daily_demand=None,
                               lead_time_days: int = 7, supplier: str = "",
                               sale_price: float = 0.0, color: str = "") -> tuple:
        conn = self._conn()
        c = conn.cursor()
        c.execute("SELECT current_stock FROM inventory WHERE id=? AND user_id=?",
                  (item_id, user_id))
        row = c.fetchone()
        if row:
            diff = current_stock - row[0]
            if diff != 0:
                mov_type = "purchase" if diff > 0 else "adjustment"
                conn.execute(
                    "INSERT INTO inventory_movements "
                    "(inventory_id,user_id,movement_type,quantity,note) "
                    "VALUES (?,?,?,?,'Ajuste manual')",
                    (item_id, user_id, mov_type, diff),
                )
        c.execute(
            "UPDATE inventory SET sku=?,name=?,category=?,color=?,supplier=?,current_stock=?,"
            "min_stock=?,max_stock=?,unit_cost=?,sale_price=?,daily_demand=?,"
            "lead_time_days=?,updated_at=datetime('now') "
            "WHERE id=? AND user_id=?",
            (sku, name, category, color, supplier, current_stock, min_stock, max_stock,
             unit_cost, sale_price, daily_demand, lead_time_days, item_id, user_id),
        )
        ok = c.rowcount > 0
        conn.commit()
        conn.close()
        return (ok, "Actualizado" if ok else "No encontrado")

    def delete_inventory_item(self, item_id: int, user_id: int) -> tuple:
        conn = self._conn()
        conn.execute("DELETE FROM inventory WHERE id=? AND user_id=?", (item_id, user_id))
        conn.commit()
        conn.close()
        return True, "Eliminado"

    def get_inventory_movements(self, user_id: int, days: int = 30) -> list:
        conn = self._conn()
        c = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute(
            "SELECT m.id, m.inventory_id, m.movement_type, m.quantity, m.reference, "
            "m.note, m.created_at, i.sku, i.name "
            "FROM inventory_movements m "
            "JOIN inventory i ON m.inventory_id = i.id "
            "WHERE m.user_id=? AND m.created_at >= ? "
            "ORDER BY m.created_at DESC",
            (user_id, since),
        )
        rows = c.fetchall()
        conn.close()
        cols = ["id", "inventory_id", "movement_type", "quantity", "reference",
                "note", "created_at", "sku", "name"]
        return [dict(zip(cols, r)) for r in rows]

    # ─────────────────────────────── SALES ────────────────────────────────────

    def register_sale(self, user_id: int, inventory_id: int, quantity: int,
                      unit_price: float, route: str = "", zone: str = "",
                      client: str = "", sale_date: str = "",
                      company_id=None) -> tuple:
        conn = self._conn()
        c = conn.cursor()
        c.execute(
            "SELECT sku, name, category, unit_cost, current_stock "
            "FROM inventory WHERE id=? AND user_id=?",
            (inventory_id, user_id),
        )
        item = c.fetchone()
        if not item:
            conn.close()
            return False, "Producto no encontrado en inventario"
        sku, product_name, category, unit_cost, current_stock = item

        if current_stock < quantity:
            conn.close()
            return False, f"Stock insuficiente: disponible {current_stock}, solicitado {quantity}"

        total_revenue = quantity * unit_price
        total_cost = quantity * unit_cost
        profit = total_revenue - total_cost
        sd = sale_date or datetime.now().isoformat()

        c.execute(
            "INSERT INTO sales (user_id,company_id,inventory_id,sku,product_name,category,"
            "quantity,unit_price,unit_cost,route,zone,client,"
            "sale_date,total_revenue,total_cost,profit) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (user_id, company_id, inventory_id, sku, product_name, category,
             quantity, unit_price, unit_cost, route, zone, client,
             sd, total_revenue, total_cost, profit),
        )
        conn.commit()
        conn.close()
        return True, "Venta registrada. Inventario actualizado automáticamente."

    def get_sales(self, user_id: int, days: int = 30) -> list:
        conn = self._conn()
        c = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute(
            "SELECT * FROM sales WHERE user_id=? AND sale_date >= ? ORDER BY sale_date DESC",
            (user_id, since),
        )
        rows = c.fetchall()
        conn.close()
        cols = ["id", "user_id", "company_id", "inventory_id", "sku", "product_name",
                "category", "quantity", "unit_price", "unit_cost", "route", "zone",
                "client", "sale_date", "total_revenue", "total_cost", "profit"]
        return [dict(zip(cols, r)) for r in rows]

    def get_sales_summary(self, user_id: int, days: int = 30) -> dict:
        conn = self._conn()
        c = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute(
            "SELECT COUNT(*), SUM(quantity), SUM(total_revenue), SUM(total_cost), SUM(profit) "
            "FROM sales WHERE user_id=? AND sale_date >= ?",
            (user_id, since),
        )
        row = c.fetchone()
        conn.close()
        return {
            "num_sales": row[0] or 0,
            "total_units": row[1] or 0,
            "revenue": row[2] or 0.0,
            "cost": row[3] or 0.0,
            "profit": row[4] or 0.0,
        }

    def get_profitability_by_route(self, user_id: int, days: int = 30) -> list:
        conn = self._conn()
        c = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute(
            "SELECT COALESCE(NULLIF(TRIM(route),''), 'Sin ruta') AS route, "
            "COUNT(*) AS num_sales, SUM(quantity) AS total_units, "
            "SUM(total_revenue) AS revenue, SUM(total_cost) AS cost, "
            "SUM(profit) AS profit, "
            "CASE WHEN SUM(total_revenue) > 0 "
            "THEN ROUND(SUM(profit)*100.0/SUM(total_revenue),1) ELSE 0 END AS margin_pct "
            "FROM sales WHERE user_id=? AND sale_date >= ? "
            "GROUP BY route ORDER BY profit DESC",
            (user_id, since),
        )
        rows = c.fetchall()
        conn.close()
        cols = ["route", "num_sales", "total_units", "revenue", "cost", "profit", "margin_pct"]
        return [dict(zip(cols, r)) for r in rows]

    def get_profitability_by_product(self, user_id: int, days: int = 30) -> list:
        conn = self._conn()
        c = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        c.execute(
            "SELECT sku, product_name, category, COUNT(*) AS num_sales, "
            "SUM(quantity) AS total_units, SUM(total_revenue) AS revenue, "
            "SUM(total_cost) AS cost, SUM(profit) AS profit, "
            "CASE WHEN SUM(total_revenue) > 0 "
            "THEN ROUND(SUM(profit)*100.0/SUM(total_revenue),1) ELSE 0 END AS margin_pct "
            "FROM sales WHERE user_id=? AND sale_date >= ? "
            "GROUP BY sku ORDER BY profit DESC",
            (user_id, since),
        )
        rows = c.fetchall()
        conn.close()
        cols = ["sku", "product_name", "category", "num_sales", "total_units",
                "revenue", "cost", "profit", "margin_pct"]
        return [dict(zip(cols, r)) for r in rows]
