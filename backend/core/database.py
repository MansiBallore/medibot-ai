"""
MediBot AI — Database Layer (MongoDB via Motor async driver)
Falls back to in-memory dict store if MongoDB is unavailable.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

logger = logging.getLogger("medibot.db")

# Try MongoDB; fall back to in-memory
try:
    import motor.motor_asyncio
    from core.config import settings
    _client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=3000)
    _db = _client[settings.MONGODB_DB]
    MONGO_AVAILABLE = True
except Exception:
    MONGO_AVAILABLE = False
    _db = None

# ─── In-memory fallback store ─────────────────────────────────────────────────
_mem: Dict[str, List] = {
    "users": [],
    "sessions": [],
    "messages": [],
    "diagnoses": [],
}


async def init_db():
    global MONGO_AVAILABLE
    if MONGO_AVAILABLE:
        try:
            await _client.admin.command("ping")
            logger.info("✅ MongoDB connected")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB unavailable: {e} — using in-memory store")
            MONGO_AVAILABLE = False
    else:
        logger.info("ℹ️  Using in-memory store (no MongoDB)")


# ─── Generic CRUD helpers ─────────────────────────────────────────────────────

async def db_insert(collection: str, doc: Dict) -> str:
    doc["_id"] = doc.get("_id", str(uuid.uuid4()))
    doc["created_at"] = datetime.utcnow().isoformat()
    if MONGO_AVAILABLE:
        result = await _db[collection].insert_one(doc)
        return str(result.inserted_id)
    else:
        _mem.setdefault(collection, []).append(doc)
        return doc["_id"]


async def db_find_one(collection: str, query: Dict) -> Optional[Dict]:
    if MONGO_AVAILABLE:
        return await _db[collection].find_one(query)
    else:
        for doc in _mem.get(collection, []):
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None


async def db_find_many(collection: str, query: Dict, limit: int = 100) -> List[Dict]:
    if MONGO_AVAILABLE:
        cursor = _db[collection].find(query).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
    else:
        results = []
        for doc in _mem.get(collection, []):
            if all(doc.get(k) == v for k, v in query.items()):
                results.append(doc)
        return results[-limit:]


async def db_update_one(collection: str, query: Dict, update: Dict) -> bool:
    if MONGO_AVAILABLE:
        result = await _db[collection].update_one(query, {"$set": update})
        return result.modified_count > 0
    else:
        for doc in _mem.get(collection, []):
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update)
                return True
        return False


async def db_delete_one(collection: str, query: Dict) -> bool:
    if MONGO_AVAILABLE:
        result = await _db[collection].delete_one(query)
        return result.deleted_count > 0
    else:
        store = _mem.get(collection, [])
        for i, doc in enumerate(store):
            if all(doc.get(k) == v for k, v in query.items()):
                store.pop(i)
                return True
        return False


async def db_count(collection: str, query: Dict = {}) -> int:
    if MONGO_AVAILABLE:
        return await _db[collection].count_documents(query)
    else:
        return sum(
            1 for doc in _mem.get(collection, [])
            if all(doc.get(k) == v for k, v in query.items())
        )
