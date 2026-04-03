-- Migration 016: converte tips.answer de plain-text para HTML
UPDATE tips
SET answer = regexp_replace(
               regexp_replace(
                 regexp_replace(
                   regexp_replace(answer,
                     '@([a-zA-Z0-9_-]+)',
                     '<span data-type="mention" data-id="\1" class="mention">@\1</span>',
                     'g'),
                   E'\\*\\*([^*]+)\\*\\*', '<strong>\1</strong>', 'g'),
                 E'\\*([^*]+)\\*', '<em>\1</em>', 'g'),
               E'_([^_]+)_', '<u>\1</u>', 'g')
WHERE answer NOT LIKE '<%';
