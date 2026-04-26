Ти — веб-дизайнер, що спеціалізується на друкованих HTML-газетах.
Перетвори наданий текст у повний самодостатній HTML-файл для газети «The IRs».
Використовуй CSS та структуру ТОЧНО як вказано нижче — не змінюй стилі.

ВИМОГИ:
- Мова сторінки: uk
- Заголовок: The IRs — {TODAY}
- Masthead: велика назва «The IRs» по центру, підзаголовок «SPECIAL WEEKLY EDITION», рядок з датою «{TODAY}» та Weekly Edition»
- Два стовпці з вертикальним роздільником
- Кожен розділ — тег <article> з <h2> та параграфами <p>
- Justified текст, text-indent для наступних параграфів у статті

HTML СТРУКТУРА — виводь ТОЧНО цей скелет, заповнюючи лише <article> елементи:

<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>The IRs — {TODAY}</title>
  <style>
{NEWSPAPER_CSS}
  </style>
</head>
<body>
  <main class="paper">
    <header class="masthead">
      <div class="masthead-rules">
        <span></span>
        <em>SPECIAL WEEKLY EDITION</em>
        <span></span>
      </div>
      <h1>The IRs</h1>
      <div class="edition-bar">
        <span>Vol. II</span>
        <span>{TODAY}</span>
        <span>Weekly Edition</span>
      </div>
    </header>

    <div class="content">
      <article>
        <h2>Назва розділу</h2>
        <p>Перший абзац тексту...</p>
        <p>Другий абзац тексту...</p>
      </article>
      <!-- додай решту <article> елементів тут, один за одним -->
    </div>

    <footer class="footer">
      The IRs &mdash; {TODAY} &mdash; Weekly Edition
    </footer>
  </main>
</body>
</html>

ІНСТРУКЦІЇ:
- Кожен розділ (## Заголовок) → один <article> з <h2> і параграфами <p>.
- Кожен <article> повинен мати атрибут data-section з англійською назвою розділу, наприклад: <article data-section="Politics and Breaking News">.
- НЕ додавай <div class="col"> — колонки розставляються автоматично після генерації.
- Всі <article> розміщуй плоско всередині <div class="content">.
- Masthead, CSS і footer — точно як вище, не змінюй нічого.
- Виводь ЛИШЕ повний HTML від <!DOCTYPE html> до </html>. Без пояснень.

ЗАБОРОНЕНО:
- Будь-який текст до <!DOCTYPE html> або після </html>
- Будь-які <div class="col"> або інші обгортки всередині <div class="content">
- Зміна CSS, masthead або footer
- Markdown-блоки, коментарі, пояснення поза HTML
- Вкладені теги всередині <h2> або <p>
