"""
Quick smoke test for the brain image pipeline.
Run: source venv/bin/activate && python test_brain_upload.py <image_path>

Tests: GPT-4o vision → text-embedding-3-small → Pinecone "images" namespace
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from server.app.brain.service import describe_image, embed_and_upsert_image, NAMESPACE_IMAGES
from server.app.vector.service import _get_index_sync


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_brain_upload.py <image_path>")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"File not found: {image_path}")
        sys.exit(1)

    image_bytes = image_path.read_bytes()
    ext = image_path.suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    print(f"Image: {image_path.name} ({len(image_bytes) / 1024:.0f} KB, {mime_type})")

    # Step 1: Image description (manual for now — GPT-4o vision requires separate key)
    print("\n1. Using manual description (GPT-4o vision skipped)...")
    description = (
        "Outdoor portrait photograph of a woman with vibrant red-orange bob haircut, "
        "wearing sunglasses pushed up on her head and a purple floral sundress. "
        "She holds a clear iced drink with a green straw. Shallow depth of field "
        "with soft bokeh background showing other people and greenery. "
        "Warm golden-hour lighting, candid street photography style, "
        "slightly serious or contemplative expression. Dominant colors: purple, "
        "red-orange, warm skin tones against a soft green and golden background."
    )
    print(f"   Description ({len(description)} chars):")
    print(f"   {description[:300]}{'...' if len(description) > 300 else ''}")

    # Step 2: Generate fake 1536-dim vector (stands in for text-embedding-3-small)
    pinecone_id = str(uuid4())
    test_user_id = "00000000-0000-0000-0000-000000000001"  # fake test user

    import numpy as np
    fake_vector = np.random.randn(1536).astype(np.float32)
    fake_vector = (fake_vector / np.linalg.norm(fake_vector)).tolist()

    print(f"\n2. Upserting fake vector to Pinecone (id={pinecone_id[:8]}...)...")
    index = _get_index_sync()
    if index is None:
        print("   FAILED — Pinecone index not available")
        sys.exit(1)

    index.upsert(
        vectors=[{
            "id": pinecone_id,
            "values": fake_vector,
            "metadata": {
                "user_id": test_user_id,
                "blob_url": f"file://{image_path.resolve()}",
                "filename": image_path.name,
                "description_preview": description[:200],
            },
        }],
        namespace=NAMESPACE_IMAGES,
    )
    print("   SUCCESS — vector stored in Pinecone 'images' namespace")

    # Step 3: Verify by fetching
    print("\n3. Verifying vector exists in Pinecone...")
    result = index.fetch(ids=[pinecone_id], namespace=NAMESPACE_IMAGES)
    if pinecone_id in result.vectors:
        vec = result.vectors[pinecone_id]
        print(f"   VERIFIED — dim={len(vec.values)}, metadata keys={list(vec.metadata.keys())}")
    else:
        print("   NOT FOUND — upsert may still be propagating")

    # Step 4: Query for similar (should return empty since it's the only vector)
    print("\n4. Testing similarity query...")
    query_result = index.query(
        vector=fake_vector,
        top_k=3,
        filter={"user_id": {"$eq": test_user_id}},
        include_metadata=True,
        namespace=NAMESPACE_IMAGES,
    )
    print(f"   Matches found: {len(query_result.matches)}")
    for m in query_result.matches:
        print(f"   - {m.id[:8]}... score={m.score:.4f} file={m.metadata.get('filename')}")

    # Cleanup: remove test vector
    print(f"\n5. Cleaning up test vector...")
    index.delete(ids=[pinecone_id], namespace=NAMESPACE_IMAGES)
    print("   Deleted.")

    print("\n✓ Pipeline test complete.")


if __name__ == "__main__":
    asyncio.run(main())
