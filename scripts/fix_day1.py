import os

path = "D:/Obsidian/Syndicate Intelligence/Syndicate Intelligence/10_База_знаний/📖 День 1 — Словарь терминов и механик рынка.md"
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Nav header
text = text.replace('[[Syndicate Intelligence — Главный пульт|Главный пульт]]', '[[🧭 Syndicate Intelligence — Главный пульт|Главный пульт]]')

# 2. Term 14
t14_old = 'беcфиатная конструкция, где 1 обеспечивается'
t14_new = 'бесфиатная конструкция, где $1.00 обеспечивается'
assert t14_old in text, 'Term 14 not found'
text = text.replace(t14_old, t14_new)

# 3. Term 25
t25_old = 'до 2030 года на рынок выльется разлоков на $155 млрд против максимум 75 млрд и программирует 95% альткоинов на медленное обнуление.'
t25_new = 'до 2030 года на рынок выльется разлоков на $155 млрд против максимум $75 млрд органического притока капитала, что создает структурный дефицит спроса и программирует 95% альткоинов на медленное обнуление.'
assert t25_old in text, 'Term 25 not found'
text = text.replace(t25_old, t25_new)

# 4. Term 36
t36_old = '(Pbreakeven\u200b)'
t36_new = '($P_{\\text{breakeven}}$)'
assert t36_old in text, 'Term 36 not found'
text = text.replace(t36_old, t36_new)

# 5. Term 46
t46_old = 'сжигая у пользователя 60 чистых денег за газ впустую.'
t46_new = 'сжигая у пользователя $40–$60 чистых денег за газ впустую.'
assert t46_old in text, 'Term 46 not found'
text = text.replace(t46_old, t46_new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Day 1 successfully fixed and verified!')

