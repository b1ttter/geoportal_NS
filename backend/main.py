from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from db import get_connection, init_db


app = FastAPI(title="Geoportal API")


@app.get("/health")
def health():
    return {"status": "ok"}

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/users")
def get_users():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(
                json_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(geom)::json,
                    'properties', json_build_object(
                        'id', id,
                        'name', name,
                        'created_at', created_at
                    )
                )
            ), '[]'::json)
        )
        FROM map_users;
    """)

    result = cur.fetchone()[0]

    cur.close()
    conn.close()

    return result


@app.post("/users")
def add_user(user: UserCreate):
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO map_users (name, geom)
        VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        RETURNING id;
    """, (user.name, user.lon, user.lat))

    user_id = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "id": user_id,
        "name": user.name,
        "lat": user.lat,
        "lon": user.lon
    }


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("DELETE FROM map_users WHERE id = %s RETURNING id;", (user_id,))
    deleted = cur.fetchone()

    cur.close()
    conn.close()

    if deleted is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {"deleted": True, "id": user_id}


@app.get("/miasta")
def miasta():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', json_agg(
                json_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(geom)::json,
                    'properties', json_build_object(
                        'id', id,
                        'nazwa', nazwa
                    )
                )
            )
        )
        FROM miasta;
    """)

    result = cur.fetchone()[0]

    cur.close()
    conn.close()

    return result