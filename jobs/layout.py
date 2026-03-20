"""
Post-processes AI-generated HTML: injects the latest CSS from
prompts/newspaper_css.md and adds the production cost as a price tag
in the masthead (like old-style newspaper pricing).
"""
import os
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(ROOT_DIR, "prompts")


def _load_css() -> str:
    with open(os.path.join(PROMPTS_DIR, "newspaper_css.md"), "r", encoding="utf-8") as f:
        return f.read().strip()


def apply_layout(html: str, today: str, cost_usd: float = 0.0) -> str:
    """
    1. Injects fresh CSS from newspaper_css.md.
    2. Inserts a price-bar element into the masthead.
    """
    # ── 1. Inject CSS ──────────────────────────────────────────────
    css = _load_css()
    html = re.sub(
        r'(<style[^>]*>).*?(</style>)',
        lambda m: f'{m.group(1)}\n{css}\n  {m.group(2)}',
        html,
        flags=re.DOTALL,
    )

    # ── 2. Inject price bar into masthead ──────────────────────────
    price_str = f"${cost_usd:.4f}"
    price_html = f'<div class="price-bar">Price: {price_str}</div>\n    '
    html = re.sub(
        r'(</header>)',
        price_html + r'\1',
        html,
        count=1,
    )

    return html
