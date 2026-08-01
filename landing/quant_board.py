"""
=============================================================================
AXIOM QUANT — QUANTREDDIT / QUANTCHAN DISCUSSION BOARD ROUTER
=============================================================================
Anonymous, PII-scrubbed, high-signal quantitative research board.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from quant_scrubber import generate_anon_tripcode, scrub_pii_and_profanity

router = APIRouter(prefix="/api/v1/board", tags=["QuantReddit Board"])


class ReplyModel(BaseModel):
    reply_id: str
    tripcode: str
    timestamp: str
    content: str


class ThreadModel(BaseModel):
    thread_id: str
    title: str
    category: str
    tripcode: str
    timestamp: str
    content: str
    upvotes: int = 0
    replies: List[ReplyModel] = Field(default_factory=list)


class CreateThreadRequest(BaseModel):
    title: str
    category: str = "Quantitative Research"
    content: str
    author_seed: Optional[str] = "anon_user"


class CreateReplyRequest(BaseModel):
    thread_id: str
    content: str
    author_seed: Optional[str] = "anon_user"


# In-memory board storage pre-populated with high-signal quantitative threads
MEMORY_THREADS: List[ThreadModel] = [
    ThreadModel(
        thread_id="th-001",
        title="BitNet b1.58 Ternary Weights vs LWE Lattice Error Noise Equivalence",
        category="Quantum & Lattice Cryptography",
        tripcode="Anon#Δ8a3c9e",
        timestamp="2026-07-31T14:20:00Z",
        content=r"Is the ternary weight quantization $w_q \in \{-1, 0, +1\}$ mathematically isomorphic to discrete Gaussian LWE lattice noise errors $\mathbf{e} \sim \mathcal{D}_{\mathbb{Z}, \sigma}$? See Theorem H.1 in Axiom Quant Appendices.",
        upvotes=42,
        replies=[
            ReplyModel(
                reply_id="rep-001",
                tripcode="Anon#Δ4b1f9a",
                timestamp="2026-07-31T14:45:00Z",
                content=r"Yes, because the error vector $\mathbf{e}$ under matrix product $W_q \mathbf{b} = W_q \mathbf{A}\mathbf{s} + W_q \mathbf{e} \pmod q$ remains bounded within the same LWE error distribution.",
            )
        ],
    ),
    ThreadModel(
        thread_id="th-002",
        title="Python 3.13 JIT + NoGIL Performance on Cloud Run for Stochastic Options",
        category="High Performance Computing",
        tripcode="Anon#Δ1c7e4b",
        timestamp="2026-08-01T02:10:00Z",
        content="Testing free-threaded Python 3.13 on Google Cloud Run. We achieved 4.2x speedup on Monte Carlo Black-Scholes Greeks calculation across 16 vCPUs without GIL locking.",
        upvotes=38,
        replies=[],
    ),
]


@router.get("/threads", response_model=List[ThreadModel])
async def list_threads():
    """List all active PII-scrubbed threads."""
    return MEMORY_THREADS


@router.post("/thread", response_model=ThreadModel)
async def create_thread(req: CreateThreadRequest, request: Request):
    """Create a new anonymous PII-scrubbed thread."""
    client_ip = request.client.host if request.client else req.author_seed
    tripcode = generate_anon_tripcode(client_ip or "anon")

    clean_title = scrub_pii_and_profanity(req.title)
    clean_content = scrub_pii_and_profanity(req.content)

    thread = ThreadModel(
        thread_id=f"th-{uuid.uuid4().hex[:6]}",
        title=clean_title,
        category=req.category,
        tripcode=tripcode,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        content=clean_content,
        upvotes=1,
        replies=[],
    )
    MEMORY_THREADS.insert(0, thread)
    return thread


@router.post("/reply", response_model=ReplyModel)
async def create_reply(req: CreateReplyRequest, request: Request):
    """Post a reply to an existing thread."""
    target_thread = next(
        (t for t in MEMORY_THREADS if t.thread_id == req.thread_id), None
    )
    if not target_thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    client_ip = request.client.host if request.client else req.author_seed
    tripcode = generate_anon_tripcode(client_ip or "anon")
    clean_content = scrub_pii_and_profanity(req.content)

    reply = ReplyModel(
        reply_id=f"rep-{uuid.uuid4().hex[:6]}",
        tripcode=tripcode,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        content=clean_content,
    )
    target_thread.replies.append(reply)
    return reply


@router.post("/upvote/{thread_id}")
async def upvote_thread(thread_id: str):
    """Upvote a thread score."""
    target_thread = next((t for t in MEMORY_THREADS if t.thread_id == thread_id), None)
    if not target_thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    target_thread.upvotes += 1
    return {
        "status": "SUCCESS",
        "thread_id": thread_id,
        "upvotes": target_thread.upvotes,
    }
