"""Gemini API를 이용한 번역/요약/중복 제거/선별"""
import json

from google import genai
from google.genai import types

from . import config

SYSTEM_PROMPT = """\
당신은 개인 투자자를 위한 경제 뉴스 에디터입니다. 아래 후보 기사 목록(JSON)을 검토해서 \
매일 아침 투자 참고용으로 보낼 뉴스를 선별하고 한국어로 요약하세요.

규칙:
1. 같은 사건을 다루는 중복/유사 기사는 하나로 합치고, 가장 정보가 풍부한 기사의 링크를 사용하세요.
2. 단순 홍보, 연예/스포츠, 투자와 무관한 내용, 낚시성 제목 기사는 제외하세요.
3. 해외(영문) 기사는 자연스러운 한국어로 번역/의역해서 요약하세요.
4. 금리, 환율, 증시 지수, 주요 기업 실적, 원자재, 부동산, 정책 발표 등 투자 판단에 실질적으로 \
도움이 되는 뉴스를 우선하세요.
5. 최종적으로 중요도 순으로 최대 {top_n}개를 선정하세요. 후보가 부족하면 있는 만큼만 반환하세요.
6. 각 기사의 summary는 2~3문장, 왜 투자자에게 중요한지가 드러나도록 간결하게 작성하세요.

반드시 아래 JSON 형식으로만 답하세요 (다른 텍스트 금지):
{{
  "articles": [
    {{
      "title": "한국어 제목",
      "summary": "한국어 요약 (2~3문장)",
      "category": "국내" 또는 "해외",
      "link": "원본 기사 URL"
    }}
  ]
}}
"""


def _build_candidates_payload(articles: list[dict]) -> str:
    trimmed = [
        {
            "id": idx,
            "source": a["source"],
            "title": a["title"],
            "description": a["description"][:500],
            "link": a["link"],
        }
        for idx, a in enumerate(articles)
    ]
    return json.dumps(trimmed, ensure_ascii=False)


def select_and_summarize(articles: list[dict]) -> list[dict]:
    """후보 기사 목록을 받아 중복 제거/필터링/번역/요약 후 상위 TOP_N개를 반환한다."""
    if not articles:
        return []
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=_build_candidates_payload(articles),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT.format(top_n=config.TOP_N),
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )

    content = response.text
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini 응답을 JSON으로 파싱하지 못했습니다: {content!r}") from exc

    result = data.get("articles", [])[: config.TOP_N]
    return result
