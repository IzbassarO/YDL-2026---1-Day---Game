# -*- coding: utf-8 -*-
"""Генерирует PDF-речь на защиту team_task.ipynb. Фокус — Шаг 5 (Классификация)."""
import os, matplotlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle

FT = os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data', 'fonts', 'ttf')
pdfmetrics.registerFont(TTFont('DJ', os.path.join(FT, 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DJB', os.path.join(FT, 'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFont(TTFont('DJI', os.path.join(FT, 'DejaVuSans-Oblique.ttf')))

BLUE = HexColor('#1f4e79'); GREEN = HexColor('#2e7d32'); GREY = HexColor('#555555')
LIGHT = HexColor('#eef3f8'); ACC = HexColor('#c0392b')

def ss(**k):
    k.setdefault('fontName', 'DJ'); k.setdefault('leading', 14)
    return ParagraphStyle(**k)
H1   = ss(name='H1', fontName='DJB', fontSize=17, textColor=BLUE, spaceAfter=4, leading=20)
SUB  = ss(name='SUB', fontName='DJI', fontSize=10, textColor=GREY, spaceAfter=10)
H2   = ss(name='H2', fontName='DJB', fontSize=13, textColor=BLUE, spaceBefore=12, spaceAfter=5, leading=16)
H2G  = ss(name='H2G', fontName='DJB', fontSize=13.5, textColor=GREEN, spaceBefore=12, spaceAfter=5, leading=17)
ROLE = ss(name='ROLE', fontName='DJB', fontSize=9.5, textColor=ACC, spaceAfter=2)
BODY = ss(name='BODY', fontSize=10.3, leading=15, spaceAfter=7, alignment=TA_LEFT)
SAY  = ss(name='SAY', fontSize=10.5, leading=15.5, spaceAfter=7, leftIndent=8,
          textColor=HexColor('#1a1a1a'))
NOTE = ss(name='NOTE', fontName='DJI', fontSize=9, leading=12.5, textColor=GREY, spaceAfter=6)
CELL = ss(name='CELL', fontSize=8.8, leading=11)
CELLB= ss(name='CELLB', fontName='DJB', fontSize=8.8, leading=11)

doc = SimpleDocTemplate('YDL2026_w2_day3_team1_speech.pdf', pagesize=A4,
                        leftMargin=18*mm, rightMargin=18*mm,
                        topMargin=15*mm, bottomMargin=15*mm)
E = []
def hr(): E.append(HRFlowable(width='100%', thickness=0.7, color=HexColor('#cccccc'),
                              spaceBefore=6, spaceAfter=8))
def say(t): E.append(Paragraph('🗣 ' + t, SAY))
def body(t): E.append(Paragraph(t, BODY))

# ───────── TITLE ─────────
E.append(Paragraph('Речь на защиту проекта', H1))
E.append(Paragraph('Команда 1 · Country Data · «Кому помогать» · YDL 2026, Неделя 2, День 3 · '
                   'регламент 10 минут · фокус — Шаг 5 (Классификация)', SUB))
hr()
E.append(Paragraph('Как читать этот документ', H2))
body('Значком 🗣 отмечены фразы, которые можно <b>говорить вслух почти дословно</b>. '
     'Курсивом — заметки докладчику (что показать на экране, чего не говорить). '
     'Один ноутбук на команду, выступаем по очереди — у каждого свой блок. '
     'Главный акцент защиты — <b>Шаг 5</b>: именно классификатор доказывает, что наши группы реальны, '
     'а не «разноцветные точки».')

# ───────── 0. INTRO (30 сек) ─────────
E.append(Paragraph('0. Вступление — кто говорит первым (~30 сек)', H2))
E.append(Paragraph('Спикер 1 — постановка задачи', ROLE))
say('«Нам выдали 167 стран и 9 показателей — доход, ВВП на душу, детская смертность, '
    'продолжительность жизни и другие. <b>Готовой метки нет</b>: никто не сказал, какие страны '
    '“бедные”, а какие “развитые”. Мы — аналитики гуманитарного фонда, и наша задача: '
    'найти эти группы сами, превратить их в метку и <b>честно проверить</b>, можно ли её предсказывать. '
    'Главный вопрос защиты — в самом конце, на Шаге 5: <b>а метка вообще не случайна?</b>»')
E.append(Paragraph('Это и есть три опорные мысли задания: (1) данные и находка EDA, '
                   '(2) сколько кластеров и как назвали, (3) насколько хорошо классификатор '
                   'предсказывает метку и наш честный вердикт.', NOTE))

# ───────── 1. EDA (1 мин) ─────────
E.append(Paragraph('Опорная мысль 1 — Данные и находка EDA (~1 мин)', H2))
E.append(Paragraph('Спикер 1 (или 2)', ROLE))
say('«167 стран, 9 числовых признаков, пропусков нет. Но масштабы <b>несопоставимы</b>: '
    'доход — десятки тысяч, рождаемость и инфляция — единицы. Поэтому перед KMeans и PCA мы '
    'обязательно привели всё к одному масштабу через <b>StandardScaler</b> — иначе доход и ВВП '
    'перекричали бы остальные семь признаков.»')
say('«Находка, которая нас удивила: детская смертность почти зеркально связана с рождаемостью '
    '(r ≈ +0.85) и с продолжительностью жизни (r ≈ −0.89). То есть это <b>не девять независимых '
    'признаков, а две-три “оси”</b> — богатство и здоровье. Это сразу подсказало: кластеров будет '
    'немного, а PCA сожмёт данные почти без потерь.»')
E.append(Paragraph('На экране: матрица корреляций (Шаг 1.7) и итоги Шага 1.', NOTE))

# ───────── 2. KMEANS (1.5 мин) ─────────
E.append(Paragraph('Опорная мысль 2 — Сколько кластеров, как назвали, вид на PCA (~1.5 мин)', H2))
E.append(Paragraph('Спикер 2', ROLE))
say('«Меток нет — число кластеров мы <b>не угадывали</b>. Построили метод локтя и коэффициент '
    'силуэта для k от 2 до 10. Локоть чётко загибается на <b>k = 3</b>. Силуэт при этом почти '
    'плоский (≈0.28–0.30) — и это мы говорим честно: значит, группы слегка перетекают, резких '
    '“островов” нет. Первому k не поверили, проверили соседние: k = 2 — слишком грубо, k = 4–5 '
    'дают мизерный прирост силуэта и дробят группы без нового смысла. Поэтому <b>k = 3</b> — '
    'осознанный выбор в пользу смысла, а не погоня за третьим знаком метрики.»')
say('«Кластеры мы назвали по их профилю, а не номерами: <b>“Низкий доход, высокая смертность и '
    'рождаемость”</b> (47 стран — это наши “нуждающиеся”), <b>“Средний доход”</b> (84 страны) и '
    '<b>“Высокий доход, низкая детская смертность”</b> (36 стран).»')
E.append(Paragraph('Спикер 3 — PCA', ROLE))
say('«Чтобы увидеть 9 признаков глазами, мы сжали их в две главные компоненты. Они удерживают '
    '<b>63.1% дисперсии</b>. На проекции группы выстроились полосами по PC1: бедные → средние → '
    'богатые. Крайние группы отделяются чётко, а граница “средние ↔ богатые” слегка размыта — '
    '<b>запомните это место, оно всплывёт на Шаге 5</b>.»')
E.append(Paragraph('На экране: графики локтя/силуэта (2.2) и проекция PCA с раскраской по кластерам (4.2).',
                   NOTE))

# ───────── 3. CLASSIFICATION — MAIN FOCUS ─────────
E.append(HRFlowable(width='100%', thickness=1.4, color=GREEN, spaceBefore=12, spaceAfter=8))
E.append(Paragraph('★ Опорная мысль 3 — ШАГ 5. КЛАССИФИКАЦИЯ (главный блок, ~4 мин)', H2G))
E.append(Paragraph('Спикер 4 — это кульминация защиты, говорим подробно и уверенно', ROLE))

E.append(Paragraph('а) Зачем вообще этот шаг', H2))
say('«Кластеры мы придумали сами. Возникает честный вопрос: <b>а вдруг это просто разноцветные '
    'точки, а не настоящие группы?</b> Шаг 5 отвечает на него строго. Логика такая: если группы '
    'реальные и разделимые, то классификатор, обученный <b>с нуля по исходным признакам</b>, '
    'должен уверенно угадывать нашу метку. Если же метрики низкие — мы честно признаем, что '
    'кластеризация дала размытые группы. Это и есть принцип дня: <b>не верь, проверь</b>.»')

E.append(Paragraph('б) Как проверяли — без утечки данных', H2))
say('«Мы разбили 167 стран на <b>train (116) и test (51)</b> стратифицированно — классы разного '
    'размера, и мы сохранили их пропорции в тесте. Очень важная деталь: <b>StandardScaler мы '
    'положили внутрь Pipeline</b>, чтобы он обучался только на train. Иначе информация из теста '
    'просочилась бы в обучение, и метрики были бы нечестными. Обучили две базовые модели — '
    '<b>логистическую регрессию и KNN</b> — и посчитали accuracy, precision, recall, F1. '
    'А поскольку выборка маленькая, добавили ещё <b>5-fold кросс-валидацию</b>.»')

E.append(Paragraph('в) Результаты — честно train и test', H2))
body('Лучшая модель — <b>логистическая регрессия</b>. Ключевые числа:')
tbl = Table([
    [Paragraph('Метрика (test, 51 страна)', CELLB), Paragraph('Значение', CELLB),
     Paragraph('Что значит', CELLB)],
    [Paragraph('Accuracy', CELL), Paragraph('0.922', CELLB),
     Paragraph('92% стран теста отнесены в верную группу', CELL)],
    [Paragraph('Precision (macro)', CELL), Paragraph('0.927', CELLB),
     Paragraph('когда модель называет группу — она почти всегда права', CELL)],
    [Paragraph('Recall (macro)', CELL), Paragraph('0.896', CELLB),
     Paragraph('почти всех представителей группы находит', CELL)],
    [Paragraph('F1 (macro)', CELL), Paragraph('0.909', CELLB),
     Paragraph('баланс precision и recall — высокий', CELL)],
    [Paragraph('F1 на 5-fold CV', CELL), Paragraph('0.93–0.96', CELLB),
     Paragraph('на разных разбиениях результат устойчив', CELL)],
], colWidths=[40*mm, 22*mm, 100*mm])
tbl.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),BLUE), ('TEXTCOLOR',(0,0),(-1,0),HexColor('#ffffff')),
    ('FONTNAME',(0,0),(-1,0),'DJB'),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#ffffff'), LIGHT]),
    ('GRID',(0,0),(-1,-1),0.4,HexColor('#cccccc')),
    ('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('TOPPADDING',(0,0),(-1,-1),4),
    ('BOTTOMPADDING',(0,0),(-1,-1),4), ('LEFTPADDING',(0,0),(-1,-1),5),
]))
E.append(tbl); E.append(Spacer(1, 8))
say('«Обе модели предсказывают метку <b>уверенно</b>: accuracy ≈ 0.90–0.92, F1 ≈ 0.87–0.91, '
    'а на кросс-валидации F1 поднимается до 0.93–0.96. Разрыв train–test небольшой — модель '
    'не переобучилась. Вывод прямой: <b>классификатор легко выучивает границы между группами '
    'по исходным признакам, значит группы реальны и разделимы</b>.»')

E.append(Paragraph('г) Где модель ошибается — и почему это нас радует', H2))
say('«Самое интересное — <b>куда</b> уходят ошибки. Беднейший класс — “низкий доход, высокая '
    'смертность” — распознаётся <b>идеально: precision и recall = 1.000</b>. Это наше плотное, '
    'надёжное ядро — те самые страны, которым нужна помощь, и в них модель не ошибается ни разу. '
    'А все ошибки сосредоточены на границе <b>“средние ↔ богатые”</b> — ровно там, где и PCA '
    'показал размытость. То есть три независимых метода — профиль признаков, геометрия PCA и '
    'классификатор — указывают на <b>одну и ту же</b> зыбкую границу. Это не противоречие, '
    'а согласованность: данные честно говорят, где деление чёткое, а где условное.»')
E.append(Paragraph('На экране: classification_report (5.2) и матрица ошибок — показать нулевые '
                   'ошибки в беднейшем классе и путаницу средние/богатые.', NOTE))

E.append(HRFlowable(width='100%', thickness=1.4, color=GREEN, spaceBefore=10, spaceAfter=8))

# ───────── 4. VERDICT ─────────
E.append(Paragraph('Честный вердикт команды (~1 мин)', H2))
E.append(Paragraph('Спикер 4 или капитан команды', ROLE))
say('«Наш вердикт: <b>структура данных подтвердилась</b>. Деление стран на бедные / средние / '
    'богатые, которое мы <b>сконструировали</b> кластеризацией, подтверждается тремя независимыми '
    'способами: интерпретируемым профилем признаков (Шаг 3), геометрией PCA — 63% дисперсии '
    '(Шаг 4) и обучаемостью классификатора — F1 ≈ 0.91 (Шаг 5). Это <b>не разноцветные точки</b>, '
    'а реальные группы. Единственное честное “но”: граница между средними и богатыми странами '
    'размыта — и мы это видим во всех трёх проверках, а не прячем.»')
say('«Практический итог для фонда: группа “низкий доход, высокая смертность” — 47 стран — '
    'это надёжно очерченный список тех, кому помощь нужна в первую очередь.»')

# ───────── 5. Q&A ─────────
E.append(Paragraph('Подготовка к вопросам (5 минут Q&A)', H2))
qa = [
    ('Почему метку предсказывать «легко» — это не жульничество?',
     'Метку задал KMeans по масштабированным признакам, а классификатор учится с нуля на '
     'исходных признаках и проверяется на отложенном test. Высокая точность означает, что '
     'группы геометрически разделимы, а не что мы «подсмотрели ответ».'),
    ('Не переобучились ли вы? Выборка всего 167 стран.',
     'Разрыв train–test небольшой, а 5-fold кросс-валидация даёт стабильный F1 0.93–0.96 — '
     'на разных разбиениях результат держится. Поэтому уверенно, а не случайно.'),
    ('Почему именно логистическая регрессия, а не сложная модель?',
     'Задача — проверить разделимость, а не выжать максимум. Простая модель честнее: если уже '
     'линейные границы дают F1 0.91, значит группы реально разделимы. KNN дал близкий результат — '
     'вывод не зависит от выбора модели.'),
    ('Почему точность не 100%?',
     'Ошибки сидят на границе «средние ↔ богатые» — той же, что размыта на PCA. Это свойство '
     'данных, а не баг: переход между средним и высоким развитием действительно плавный.'),
    ('Зачем StandardScaler внутри Pipeline?',
     'Чтобы scaler обучался только на train. Если масштабировать до сплита, статистика теста '
     'утечёт в обучение и метрики будут завышены.'),
]
for q, a in qa:
    E.append(Paragraph('В: ' + q, ParagraphStyle(name='Q', fontName='DJB', fontSize=9.6,
                       leading=13, textColor=BLUE, spaceBefore=5, spaceAfter=1)))
    E.append(Paragraph('О: ' + a, ParagraphStyle(name='Aa', fontName='DJ', fontSize=9.6,
                       leading=13, spaceAfter=3)))

# ───────── timing box ─────────
E.append(Spacer(1, 6))
E.append(Paragraph('Тайминг (10 минут)', H2))
t2 = Table([
    [Paragraph('Блок', CELLB), Paragraph('Время', CELLB), Paragraph('Спикер', CELLB)],
    [Paragraph('Вступление + задача', CELL), Paragraph('0:30', CELL), Paragraph('1', CELL)],
    [Paragraph('Данные + находка EDA', CELL), Paragraph('1:00', CELL), Paragraph('1–2', CELL)],
    [Paragraph('Кластеры + PCA', CELL), Paragraph('1:30', CELL), Paragraph('2–3', CELL)],
    [Paragraph('★ Классификация (Шаг 5)', CELLB), Paragraph('4:00', CELLB), Paragraph('4', CELLB)],
    [Paragraph('Вердикт + список фонда', CELL), Paragraph('1:00', CELL), Paragraph('капитан', CELL)],
    [Paragraph('Резерв / переходы', CELL), Paragraph('2:00', CELL), Paragraph('—', CELL)],
], colWidths=[80*mm, 30*mm, 40*mm])
t2.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),BLUE),('TEXTCOLOR',(0,0),(-1,0),HexColor('#ffffff')),
    ('FONTNAME',(0,0),(-1,0),'DJB'),
    ('BACKGROUND',(0,4),(-1,4),HexColor('#e3f1e3')),
    ('ROWBACKGROUNDS',(0,1),(-1,3),[HexColor('#ffffff'),LIGHT]),
    ('ROWBACKGROUNDS',(0,5),(-1,-1),[HexColor('#ffffff'),LIGHT]),
    ('GRID',(0,0),(-1,-1),0.4,HexColor('#cccccc')),
    ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
]))
E.append(t2)
E.append(Spacer(1, 8))
E.append(Paragraph('Источник данных: Kaggle — rohan0301/unsupervised-learning-on-country-data '
                   '(167 стран, 9 признаков). Все числа взяты из team_task.ipynb.', NOTE))

doc.build(E)
print('PDF создан: YDL2026_w2_day3_team1_speech.pdf')
