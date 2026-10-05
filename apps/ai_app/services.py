from .llm import cached_completion


def get_cached_llm_completion(prompt: str,*, user_id=None, timeout: int = 86400) -> str:
    """Matnli maslahat uchun LLM chaqiruvi (kesh + kvota llm.py da)."""
    if not prompt:
        return ""
    return cached_completion(
        'text', prompt,
        [{"role": "user", "content": prompt}],
        user_id=user_id, ttl=timeout,
    )
