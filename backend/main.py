from fastapi import FastAPI
from db import get_connection

app = FastAPI(title="Geoportal API")

@app.get("/health")
def health():
    return {"status": "ok"}

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