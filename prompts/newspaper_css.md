@page { size: A4; margin: 12mm 14mm; }

*, *::before, *::after { box-sizing: border-box; }

html, body {
  margin: 0; padding: 0;
  background: #fff;
  font-family: "Times New Roman", Times, serif;
  color: #000;
  -webkit-font-smoothing: antialiased;
}

.paper {
  max-width: 1120px;
  margin: 32px auto;
  padding: 0 0 40px;
  background: #fff;
  border: 1px solid #999;
}

/* ── Masthead ── */
.masthead {
  text-align: center;
  padding: 20px 40px 14px;
  border-bottom: 4px double #000;
}

.masthead-rules {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}
.masthead-rules span { flex: 1; height: 1px; background: #000; }
.masthead-rules em {
  font-style: italic;
  font-size: 0.72em;
  color: #333;
  letter-spacing: 2px;
  text-transform: uppercase;
  white-space: nowrap;
}

.masthead h1 {
  font-family: "Georgia", "Times New Roman", serif;
  font-size: 5em;
  font-weight: 900;
  letter-spacing: 8px;
  text-transform: uppercase;
  margin: 0 0 6px;
  line-height: 1;
  color: #000;
}

.masthead .edition-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 2px solid #000;
  border-bottom: 2px solid #000;
  padding: 4px 0;
  margin-top: 8px;
  font-size: 0.78em;
  font-weight: bold;
  letter-spacing: 0.5px;
  color: #000;
}

/* ── Price bar ── */
.price-bar {
  font-size: 0.65em;
  font-style: italic;
  text-align: center;
  letter-spacing: 1px;
  color: #555;
  padding: 4px 0 0;
}

/* ── Two-column layout via CSS columns (handles print page breaks natively) ── */
.content {
  padding: 20px 40px 0;
  column-count: 2;
  column-gap: 32px;
  column-rule: 1.5px solid #555;
}

/* ── Articles ── */
article {
  margin-bottom: 20px;
}

article h2 {
  font-family: "Georgia", "Times New Roman", serif;
  font-size: 1.15em;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #000;
  border-top: 3px solid #000;
  border-bottom: 1px solid #666;
  padding: 5px 0 4px;
  margin: 0 0 8px;
  break-after: avoid;
}

article p {
  font-size: 0.91em;
  line-height: 1.58;
  margin: 0;
  text-align: justify;
  hyphens: auto;
}
article p + p { text-indent: 1.4em; }

article a { color: #000; word-break: break-all; text-decoration: underline; }

/* ── Footer ── */
.footer {
  text-align: center;
  font-size: 0.72em;
  font-weight: bold;
  color: #000;
  border-top: 3px double #000;
  margin: 20px 40px 0;
  padding: 8px 0 0;
  letter-spacing: 0.5px;
}

@media (max-width: 860px) {
  .paper { margin: 0; border: none; }
  .content { padding: 16px 20px 0; column-count: 1; column-rule: none; }
  .masthead { padding: 16px 20px 12px; }
  .masthead h1 { font-size: 3em; }
}

@media print {
  html, body { background: #fff; }
  .paper { margin: 0; padding: 0; border: none; box-shadow: none; max-width: 100%; }
  .content { padding: 14px 0 0; column-count: 2; column-gap: 28px; column-rule: 1.5px solid #555; }
  .masthead { padding: 0 0 12px; }
  .footer { margin: 16px 0 0; }
  a[href]::after { content: none !important; }
}
