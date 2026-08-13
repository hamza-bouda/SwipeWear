from __future__ import annotations
from contracts.interfaces import StyleVector

async def embed_image(image_bytes: bytes) -> StyleVector:
    # FashionSigLIP fashionsiglip-v1, 512-dim L2-norm. Latency < 350 ms/image CPU.
    raise NotImplementedError

async def embed_text(text: str) -> StyleVector:
    # Same model space as embed_image.
    raise NotImplementedError
