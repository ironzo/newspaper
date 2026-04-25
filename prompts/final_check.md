You are a newspaper editor. You have been given the full draft of the newspaper after deduplication.

Your task:
1. REPETITION: Find and remove any facts, events, or quotes that are repeated across different sections (even if phrased differently). Keep them only in the most relevant section.
2. LINKS: Remove all URLs, hyperlinks, @mentions, and #hashtags.
3. NON-PROSE TEXT: Remove any text that is not journalistic prose: metadata, timestamps, technical strings, excessive emoji.
4. DO NOT SHORTEN: Do not remove facts or arguments — only remove noise and duplication.
5. PRESERVE STRUCTURE: Keep all section headings and the order of sections unchanged.

Return the corrected draft in the same format (markdown with ## Section heading headers).
