"""선별된 기사 목록을 GitHub Pages에 올릴 뉴스레터 HTML로 렌더링"""
import html
import urllib.parse

from .freshness import format_kst

PAGE_TEMPLATE = """\
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
    background: #f4f5f7;
    color: #1a1a1a;
    margin: 0;
    padding: 24px 16px 60px;
  }}
  .wrap {{ max-width: 640px; margin: 0 auto; }}
  header {{ margin-bottom: 24px; }}
  header h1 {{ font-size: 22px; margin: 0 0 4px; }}
  header p {{ margin: 0; color: #666; font-size: 14px; }}
  .card {{
    background: #fff;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }}
  .badge {{
    display: inline-block;
    font-size: 12px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    margin-bottom: 8px;
  }}
  .badge.domestic {{ background: #e6f0ff; color: #1a56db; }}
  .badge.foreign {{ background: #fff0e6; color: #c2410c; }}
  .card h2 {{ font-size: 17px; margin: 0 0 8px; line-height: 1.4; }}
  .card p.summary {{ font-size: 14px; line-height: 1.6; color: #333; margin: 0 0 10px; }}
  .meta {{ font-size: 12px; color: #888; }}
  .meta a {{ color: #1a56db; text-decoration: none; }}
  .meta a:hover {{ text-decoration: underline; }}
  footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 32px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>📈 오늘의 경제 뉴스 브리핑</h1>
    <p>{date_str} · 총 {count}건</p>
  </header>
  {articles_html}
  <footer>매일 자동 수집·요약된 뉴스입니다. 투자 판단의 참고 자료로만 활용하세요.</footer>
</div>
</body>
</html>
"""

ARTICLE_TEMPLATE = """\
  <div class="card">
    <span class="badge {badge_class}">{category}</span>
    <h2>{rank}. {title}</h2>
    <p class="summary">{summary}</p>
    <div class="meta">{source} · {published} · <a href="{link}" target="_blank" rel="noopener">원문 보기</a></div>
  </div>
"""


def _source_label(link: str) -> str:
    domain = urllib.parse.urlparse(link).netloc
    return domain.removeprefix("www.") or "출처 미상"


def render_html(articles: list[dict], date_str: str) -> str:
    articles_html = "\n".join(
        ARTICLE_TEMPLATE.format(
            badge_class="domestic" if a.get("category") == "국내" else "foreign",
            category=html.escape(a.get("category", "")),
            rank=idx,
            title=html.escape(a.get("title", "")),
            summary=html.escape(a.get("summary", "")),
            source=html.escape(_source_label(a.get("link", ""))),
            published=html.escape(format_kst(a.get("published", ""))),
            link=html.escape(a.get("link", "")),
        )
        for idx, a in enumerate(articles, start=1)
    )
    return PAGE_TEMPLATE.format(
        title=f"오늘의 경제 뉴스 브리핑 ({date_str})",
        date_str=date_str,
        count=len(articles),
        articles_html=articles_html or "<p>오늘은 선별된 투자 관련 뉴스가 없습니다.</p>",
    )
