import httpx

# Cliente global do httpx
_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    """Retorna o cliente HTTP global."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=10)
    return _client


async def close_http_client() -> None:
    """Fecha o cliente HTTP global."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def set_http_client(client: httpx.AsyncClient | None) -> None:
    """Define um cliente HTTP customizado (útil para testes)."""
    global _client
    _client = client
