"""Calcula embeddings para los listings que todavia no tienen uno.

Modelo local (sentence-transformers), sin llamadas a APIs externas.
Solo genera y guarda los vectores, no decide todavia si dos listings
son el mismo producto (eso viene despues).
"""

from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from tenacity import retry, stop_after_attempt, wait_exponential

from src.db import get_connection

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE = 256


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=5, max=60), reraise=True)
def load_model() -> SentenceTransformer:
    # Hugging Face rate-limita (429) seguido a las IPs compartidas de los
    # runners de CI; unos reintentos con backoff suelen bastar si ya hay
    # cache (ver el step "Cache del modelo" en el workflow).
    return SentenceTransformer(MODEL_NAME)


def fetch_listings_without_embedding(conn):
    with conn.cursor() as cur:
        cur.execute("select id, raw_title from product_listings where title_embedding is null")
        return cur.fetchall()


def update_embeddings(conn, listing_ids, embeddings):
    with conn.cursor() as cur:
        for listing_id, embedding in zip(listing_ids, embeddings):
            cur.execute(
                "update product_listings set title_embedding = %s where id = %s",
                (embedding, listing_id),
            )


def main():
    conn = get_connection()
    register_vector(conn)

    try:
        rows = fetch_listings_without_embedding(conn)
        print(f"Listings sin embedding: {len(rows)}")

        if not rows:
            return

        print(f"Cargando modelo '{MODEL_NAME}' (puede tardar la primera vez)...")
        model = load_model()

        listing_ids = [row[0] for row in rows]
        titles = [row[1] for row in rows]

        for start in range(0, len(titles), BATCH_SIZE):
            batch_ids = listing_ids[start:start + BATCH_SIZE]
            batch_titles = titles[start:start + BATCH_SIZE]

            embeddings = model.encode(batch_titles, show_progress_bar=False)
            update_embeddings(conn, batch_ids, embeddings)
            conn.commit()

            print(f"Procesados {min(start + BATCH_SIZE, len(titles))}/{len(titles)}")

        print("Listo.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
