-- Migration 015: converte notes.text de plain-text para HTML
UPDATE notes
SET text = regexp_replace(
             regexp_replace(
               regexp_replace(
                 regexp_replace(text,
                   '@([a-zA-Z0-9_-]+)',
                   '<span data-type="mention" data-id="\1" class="mention">@\1</span>',
                   'g'),
                 E'\\*\\*([^*]+)\\*\\*', '<strong>\1</strong>', 'g'),
               E'\\*([^*]+)\\*', '<em>\1</em>', 'g'),
             E'_([^_]+)_', '<u>\1</u>', 'g')
WHERE text NOT LIKE '<%';
