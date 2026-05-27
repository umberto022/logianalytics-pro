from fastapi import FastAPI
from database import init_db, get_conn

app = FastAPI()

init_db()

@app.post("/login")
def login(data: dict):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (data["username"], data["password"])
    )

    user = cursor.fetchone()

    return {"success": bool(user)}

@app.get("/shipments")
def get_shipments():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM shipments")
    rows = cursor.fetchall()

    return [
        {"id": r[0], "date": r[1], "cost": r[2]}
        for r in rows
    ]