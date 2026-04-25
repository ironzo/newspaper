"""
Standalone Ukrainian crossword generator using crossword-generator (MCTS) on PyPI.
Patches the library for Cyrillic: Latin-only word sanitization and [A-Z] gap patterns.

Run: python -m agent.tools.crossword_generator
   or: python agent/tools/crossword_generator.py
"""

from __future__ import annotations

import csv
import io
import os
import re
import sys
import tempfile
import webbrowser
from contextlib import nullcontext, redirect_stdout
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

# Patch pattern for filling `_` slots before any module reads Constants at import time
from crossword_generator import config as _cg_config

_cg_config.Constants.EMPTY_SYMBOL_FOR_PATTERN_MATCHING = r"[А-ЯҐЄІЇ]"

from crossword_generator.layout_handler import NewLayoutHandler  # noqa: E402
from crossword_generator.optimizer import fill_current_layout  # noqa: E402
from crossword_generator.word_handler import FileWordHandler, WordHandler  # noqa: E402

# Ukrainian letters only (uppercase after normalization)
_UKR_CLEAN_RE = re.compile(r"[^А-ЯҐЄІЇ]")


class UkrainianFileWordHandler(FileWordHandler):
    """FileWordHandler that keeps Cyrillic letters; base class strips non A-Z."""

    def preprocess_words(self) -> list[str]:
        def ok(x: Any) -> bool:
            return isinstance(x, str) and len(x) in self.word_lengths

        def normalize(x: str) -> str:
            return _UKR_CLEAN_RE.sub("", x.upper())

        words = sorted({normalize(x) for x in filter(ok, self.raw_words) if normalize(x)})
        k = int(min(len(words), self.max_num_words))
        words = list(np.random.choice(words, size=k, replace=False))
        return words


@dataclass(frozen=True)
class WordEntry:
    answer: str
    clue: str


# Deterministic bank: dictionary lemmas in uppercase; clues in Ukrainian.
UKR_WORD_BANK: tuple[WordEntry, ...] = (
    WordEntry("МОВА", "Засіб спілкування та вираження думки"),
    WordEntry("КНИГА", "Друкований або рукописний твір"),
    WordEntry("МІСТО", "Велике населене місце"),
    WordEntry("КРАЇНА", "Держава або територія з власним устроєм"),
    WordEntry("НЕБО", "Простір над землею"),
    WordEntry("СЛОВО", "Одиниця мови; те, що кажуть"),
    WordEntry("НАРОД", "Сукупність людей, пов'язаних спільною культурою"),
    WordEntry("ЗЕМЛЯ", "Поверхня суходолу; планета"),
    WordEntry("СОНЦЕ", "Зоря центру Сонячної системи"),
    WordEntry("ДУША", "Внутрішня людина; те, що відчуває"),
    WordEntry("ВОЛЯ", "Бажання; здатність діяти за власним розумінням"),
    WordEntry("СИЛА", "Могутність, потужність"),
    WordEntry("МИР", "Відсутність війни; злагода"),
    WordEntry("СТІХ", "Поетичний твір; уривок вірша"),
    WordEntry("ДОБРО", "Позитивна дія або якість"),
    WordEntry("ШКОЛА", "Заклад середньої чи початкової освіти"),
    WordEntry("ПРАВДА", "Відповідність дійсності"),
    WordEntry("ПРАЦЯ", "Діяльність для досягнення мети"),
    WordEntry("РОБОТА", "Трудова діяльність"),
    WordEntry("ЛЮБОВ", "Глибока прихильність"),
    WordEntry("НАУКА", "Система знань про світ"),
    WordEntry("ПІСНЯ", "Музичний твір зі словами"),
    WordEntry("ДУМКА", "Думка, ідея"),
    WordEntry("ОСЕНЬ", "Пора року після літа"),
    WordEntry("КАЗКА", "Народна оповідь, часто вигадана"),
    WordEntry("ГОЛОС", "Звук, яким говорять або співають"),
    WordEntry("АВТОР", "Той, хто створив твір"),
    WordEntry("ЧАС", "Тривалість або момент події"),
    WordEntry("ВОДА", "Рідина необхідна для життя"),
    WordEntry("ДІМ", "Житло; будинок"),
    WordEntry("ЛІС", "Зарості дерев"),
    WordEntry("ПОЛЕ", "Відкрита ділянка землі"),
    WordEntry("ДЕНЬ", "Частина доби зі світлом"),
    WordEntry("НІЧ", "Темна частина доби"),
    WordEntry("СНІГ", "Опади у вигляді кристалів льоду"),
    WordEntry("ЛІТО", "Найтепліша пора року"),
    WordEntry("ЗИМА", "Найхолодніша пора року"),
    WordEntry("ВЕСНА", "Пора оновлення природи"),
    WordEntry("ВІТЕР", "Рух повітря"),
    WordEntry("МОРЕ", "Велика водна простір"),
    WordEntry("РІКА", "Водотік на суходолі"),
    WordEntry("ГОРА", "Підвищення земної поверхні"),
    WordEntry("СВІТ", "Всесвіт; навколишнє"),
    WordEntry("СВОБОДА", "Незалежність від примусу"),
    WordEntry("ДРУЖБА", "Дружні стосунки між людьми"),
    WordEntry("ЖИТТЯ", "Існування організмів"),
    WordEntry("УЧИТИ", "Навчати когось"),
    WordEntry("МРІЯ", "Бажання чогось особливого"),
    WordEntry("УСМІШКА", "Легке підняття кутків губ"),
    WordEntry("ДІТИ", "Молодь до підліткового віку"),
    WordEntry("РОДИНА", "Сім'я, рідні"),
    WordEntry("ЧЕСТЬ", "Моральна гідність"),
    WordEntry("СЛУЖБА", "Робота за призначенням"),
    WordEntry("ПОЛІТ", "Державні справи; галузь влади"),
    WordEntry("ЦІНА", "Вартість товару чи послуги"),
    WordEntry("МУЗИКА", "Мистецтво звуків у часі"),
    WordEntry("ТАНЕЦЬ", "Рухи під музику"),
    WordEntry("КІНЕЦЬ", "Завершення чогось"),
    WordEntry("ПОЧАТОК", "Перший етап події"),
    WordEntry("ІСТОРІЯ", "Минулі події людства"),
    WordEntry("КУЛЬТУРА", "Сукупність духовних цінностей"),
    WordEntry("ПРАВО", "Система норм і законів"),
    WordEntry("ЩАСТЯ", "Стан радості й задоволення"),
    WordEntry("НАДІЯ", "Віра у краще майбутнє"),
)

CLUE_BY_WORD: dict[str, str] = {e.answer: e.clue for e in UKR_WORD_BANK}


def _write_words_csv(path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["answer"])
        for e in UKR_WORD_BANK:
            w.writerow([e.answer])


def _entry_word(grid: pd.DataFrame, coords: list[tuple[int, int]]) -> str:
    parts: list[str] = []
    for r, c in coords:
        v = grid.iloc[r, c]
        s = "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)
        parts.append(s)
    return "".join(parts)


def _is_across(coords: list[tuple[int, int]]) -> bool:
    if len(coords) < 2:
        return True
    return coords[0][0] == coords[1][0]


def _number_entries(
    coords_by_index: list[list[tuple[int, int]]],
    grid: pd.DataFrame,
) -> tuple[dict[tuple[int, int], int], list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns cell_number map and clue rows for across / down (same number may appear in both)."""
    entries: list[tuple[tuple[int, int], int, list[tuple[int, int]]]] = []
    for i, coords in enumerate(coords_by_index):
        start = coords[0]
        raw = _entry_word(grid, coords)
        if "_" in raw:
            continue
        word = raw.replace("_", "")
        if not word:
            continue
        entries.append((start, i, coords))

    entries.sort(key=lambda x: (x[0][0], x[0][1]))
    cell_to_num: dict[tuple[int, int], int] = {}
    across: list[dict[str, Any]] = []
    down: list[dict[str, Any]] = []
    n = 0
    for start, _idx, coords in entries:
        if start not in cell_to_num:
            n += 1
            cell_to_num[start] = n
        num = cell_to_num[start]
        w = _entry_word(grid, coords)
        clue = CLUE_BY_WORD.get(w, f"({len(w)} літер)")
        block = {"num": num, "word": w, "clue": clue, "len": len(w)}
        if _is_across(coords):
            across.append(block)
        else:
            down.append(block)
    across.sort(key=lambda b: (b["num"], b["word"]))
    down.sort(key=lambda b: (b["num"], b["word"]))
    return cell_to_num, across, down


def _build_crossword_css() -> str:
    return """
.crossword-section { padding: 20px 40px 32px; border-top: 3px double #000; break-inside: avoid; }
.crossword-title {
  font-family: Georgia, "Times New Roman", serif; font-size: 1em; font-weight: 900;
  text-transform: uppercase; letter-spacing: 2px; border-bottom: 1px solid #666;
  padding: 8px 0 6px; margin: 0 0 14px; color: #000;
}
.crossword-sub { font-size: 0.82em; color: #333; margin: -8px 0 16px; font-style: italic; }
.crossword-wrap { display: flex; flex-wrap: wrap; gap: 28px; align-items: flex-start; justify-content: center; }
.crossword-grid-wrap { flex: 0 0 auto; }
.crossword-grid {
  display: grid; gap: 0;
  border: 2px solid #000;
  font-family: "Times New Roman", Times, serif;
}
.crossword-cell {
  position: relative; width: 32px; height: 32px;
  border: 1px solid #222; display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 1rem; text-transform: uppercase; background: #fff;
  box-sizing: border-box;
}
.crossword-cell.block { background: #111; border-color: #111; }
.crossword-cell .cw-num {
  position: absolute; left: 2px; top: 1px; font-size: 9px; font-weight: 700; line-height: 1; color: #000;
}
.crossword-clues {
  flex: 1 1 280px; max-width: 420px; font-family: "Times New Roman", Times, serif; font-size: 0.88em;
}
.crossword-clues h3 {
  margin: 0 0 8px; font-size: 0.95em; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #999; padding-bottom: 4px;
}
.crossword-clues ol { margin: 0 0 16px 1.1em; padding: 0; }
.crossword-clues li { margin-bottom: 6px; line-height: 1.45; }
.crossword-clues .cw-ans { font-weight: 700; letter-spacing: 0.3px; }
@media print {
  .crossword-section { border-top: 2px solid #000; padding: 12px 0 24px; }
  .crossword-cell { width: 28px; height: 28px; font-size: 0.9rem; }
}
"""


def build_crossword_html(grid: pd.DataFrame, coords_by_index: list[list[tuple[int, int]]]) -> str:
    cell_to_num, across, down = _number_entries(coords_by_index, grid)
    rows, cols = grid.shape[0], grid.shape[1]

    cells_html = []
    for r in range(rows):
        for c in range(cols):
            raw = grid.iloc[r, c]
            s = "" if raw is None or (isinstance(raw, float) and pd.isna(raw)) else str(raw)
            if s == "" or s.strip() == "":
                cells_html.append('<div class="crossword-cell block" aria-hidden="true"></div>')
                continue
            letter = s if s != "_" else ""
            num = cell_to_num.get((r, c))
            num_html = f'<span class="cw-num">{num}</span>' if num else ""
            letter_html = letter if letter else "&nbsp;"
            cells_html.append(f'<div class="crossword-cell">{num_html}{letter_html}</div>')

    def clue_items(rows: list[dict[str, Any]]) -> str:
        parts = []
        for b in rows:
            parts.append(
                f'<li value="{b["num"]}"><span class="cw-ans">{b["word"]}</span> — {b["clue"]}</li>'
            )
        return "\n".join(parts)

    style = _build_crossword_css()
    gcols = f"repeat({cols}, 32px)"
    grows = f"repeat({rows}, 32px)"

    return f"""<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Кросворд</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; background: #f5f5f5; }}
    .paper {{ max-width: 1120px; margin: 24px auto; padding: 0 0 40px; background: #fff; border: 1px solid #999; }}
    {style}
  </style>
</head>
<body>
  <div class="paper">
    <section class="crossword-section">
      <h2 class="crossword-title">Кросворд українською</h2>
      <p class="crossword-sub">Генерація: MCTS (crossword-generator). Слова й пояснення задані детерміновано в коді.</p>
      <div class="crossword-wrap">
        <div class="crossword-grid-wrap">
          <div class="crossword-grid" style="grid-template-columns: {gcols}; grid-template-rows: {grows};">
            {"".join(cells_html)}
          </div>
        </div>
        <div class="crossword-clues">
          <h3>По горизонталі</h3>
          <ol>{clue_items(across)}</ol>
          <h3>По вертикалі</h3>
          <ol>{clue_items(down)}</ol>
        </div>
      </div>
    </section>
  </div>
</body>
</html>
"""


def generate_ukrainian_crossword(
    num_rows: int = 5,
    num_cols: int = 5,
    max_mcts_iterations: int = 2_000,
    random_seed: int = 42,
    quiet: bool = False,
) -> tuple[bool, pd.DataFrame, NewLayoutHandler]:
    np.random.seed(random_seed)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        words_path = tmp.name
    try:
        _write_words_csv(words_path)
        layout_handler = NewLayoutHandler(num_rows=num_rows, num_cols=num_cols)
        word_handler = UkrainianFileWordHandler(
            path_to_words=words_path,
            word_lengths=layout_handler.word_lengths,
            max_num_words=int(_cg_config.DefaultArguments.MAX_NUM_WORDS),
        )
        out_buf = io.StringIO()
        ctx = redirect_stdout(out_buf) if quiet else nullcontext()
        with ctx:
            solved, final_grid, _stats = fill_current_layout(
                layout_handler=layout_handler,
                word_handler=word_handler,
                iteration_limit=max_mcts_iterations,
            )
        if quiet and not solved:
            sys.stderr.write(out_buf.getvalue())
        return solved, final_grid, layout_handler
    finally:
        try:
            os.unlink(words_path)
        except OSError:
            pass


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = os.path.join(root, "temp_storage")
    os.makedirs(out_dir, exist_ok=True)
    out_html = os.path.join(out_dir, "crossword.html")

    solved, grid, layout_handler = generate_ukrainian_crossword(
        num_rows=5,
        num_cols=5,
        max_mcts_iterations=2_500,
        random_seed=42,
        quiet=True,
    )

    if not solved:
        sys.stderr.write("Не вдалося заповнити сітку. Спробуйте збільшити max_mcts_iterations або словник.\n")
        sys.exit(1)

    html = build_crossword_html(grid, layout_handler.coordinates)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Збережено: {out_html}")
    try:
        webbrowser.open(f"file://{out_html}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
