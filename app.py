from typing import Optional, Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import settings
from .perplexity import PerplexityClient


app = FastAPI(title="Perplexity Proxy Server", version="1.0.0")


class AskRequest(BaseModel):
    title: Optional[str] = Field(None, description="Book title to ask about")
    query: Optional[str] = Field(
        None, description="Optional full query to send to Perplexity"
    )
    model: Optional[str] = Field(
        None, description="Optional Perplexity model override"
    )


class AskResponse(BaseModel):
    answer: str
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    raw: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "model": settings.perplexity_model}


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    if not req.query and not req.title:
        raise HTTPException(status_code=400, detail="Provide 'title' or 'query'")

    # Prefer explicit query if given; otherwise, craft a prompt from title
    if req.query:
        query = req.query.strip()
    else:
        query = (
            f"Provide a concise, accurate overview of the book titled '" \
            f"{req.title}'. Include author, publication context, main plot, " \
            f"key themes, and notable insights."
        )

    client = PerplexityClient()
    try:
        data = await client.ask(query=query, model=req.model)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Extract primary answer content
    answer = ""
    model_used = data.get("model")
    usage = data.get("usage")

    try:
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message", {})
            answer = message.get("content", "")
    except Exception:
        # Fall back silently; return raw for debugging
        answer = ""

    if not answer:
        # If answer parsing fails, surface the raw payload
        answer = "No answer content found in response."

    return AskResponse(answer=answer, model=model_used, usage=usage, raw=data)


class TextAskRequest(BaseModel):
    key: str = Field(
        ..., description="Идентификационный ключ пользователя (не Perplexity API key)"
    )
    text: str = Field(..., description="Prompt text to send to Perplexity")
    model: Optional[str] = Field(
        None, description="Optional Perplexity model override"
    )


def _compose_book_info_prompt(subject: str) -> str:
    subject = subject.strip()
    return (
        "Найди информацию об этой книге: '" + subject + "'.\n"
        "Ответь на русском языке, кратко и по делу.\n"
        "Сохрани структуру ровно из 10 строк с метками (свободный текст, не JSON), без маркеров, цифр и лишних комментариев, без пустых строк. Одна строка — одна метка:\n"
        "Автор: <имя автора>\n"
        "Страна: <страна написания>\n"
        "Язык: <язык оригинала>\n"
        "Первая публикация: <год публикации>\n"
        "Годы: <годы написания или публикации, если отличаются>\n"
        "Жанр: <основной жанр>\n"
        "Герои: <2–5 главных героев>\n"
        "Сюжет: <очень краткое описание, 1–2 предложения>\n"
        "Город: <город или города событий>\n"
        "Контекст: <краткий историко-культурный контекст, 1 фраза>\n"
        "Если данных нет, пиши 'неизвестно' для соответствующего пункта. Не выдумывай факты."
    )


@app.post("/ask_text", response_model=AskResponse)
async def ask_text(req: TextAskRequest) -> AskResponse:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="'text' must be non-empty")
    # Validate identification key from request vs env
    expected_key = settings.client_ident_key
    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="Server identification key is not configured (CLIENT_IDENT_KEY)",
        )
    if req.key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid key")

    # Wrap provided text (обычно название книги) специальным промптом на русском
    prompt = _compose_book_info_prompt(text)

    # Используем API ключ Perplexity из .env (settings), а не из запроса
    client = PerplexityClient()
    try:
        data = await client.ask(query=prompt, model=req.model)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    answer = ""
    model_used = data.get("model")
    usage = data.get("usage")
    try:
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message", {})
            answer = message.get("content", "")
    except Exception:
        answer = ""
    if not answer:
        answer = "No answer content found in response."

    return AskResponse(answer=answer, model=model_used, usage=usage, raw=data)


class SearchTextRequest(BaseModel):
    key: str = Field(
        ..., description="Идентификационный ключ пользователя (не Perplexity API key)"
    )
    text: str = Field(..., description="Search query text for Perplexity Search API")
    count: int = Field(5, ge=1, le=20, description="Number of results to return (1-20)")
    include_snippets: bool = Field(
        True, description="Whether to include snippets in results"
    )


@app.post("/search_text")
async def search_text(req: SearchTextRequest) -> Dict[str, Any]:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="'text' must be non-empty")

    expected_key = settings.client_ident_key
    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="Server identification key is not configured (CLIENT_IDENT_KEY)",
        )
    if req.key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid key")

    client = PerplexityClient()
    try:
        data = await client.search(
            query=text, count=req.count, include_snippets=req.include_snippets
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {"results": data}


# Convenience: run with `python -m server_pplx.app`
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server_pplx.app:app", host="0.0.0.0", port=8080, reload=True)
