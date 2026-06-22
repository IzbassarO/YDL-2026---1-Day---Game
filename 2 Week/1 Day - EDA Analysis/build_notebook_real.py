"""Second EDA notebook — REAL data (California Housing, sklearn).
Mirror of the synthetic-traffic notebook to contrast 'lying statistics' on real data."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s))
code = lambda s: cells.append(nbf.v4.new_code_cell(s))

# ───────────────────────── TITLE ─────────────────────────
md(r"""# 🏠 Лаборатория: статистика, которая врёт — РЕАЛЬНЫЕ данные
### EDA · California Housing (перепись 1990) · YDL 2026 · Неделя 2, День 1 (часть 2)

> Первый датасет (Smart Traffic) оказался синтетическим шумом — там статистика «врала» от пустоты.
> Теперь берём **настоящие данные** и смотрим, как они врут **по-другому**: перекос, выбросы,
> цензурирование и реальный confounding. Та же методика расследования, противоположная картина.

**Датасет:** `sklearn.datasets.fetch_california_housing` — 20 640 жилых районов Калифорнии.
Признаки: медианный доход (`MedInc`, десятки тыс. $), возраст домов, среднее число комнат/спален,
население, заселённость, широта/долгота и цель — **медианная цена дома** (`MedHouseVal`, сотни тыс. $).

> ⚠️ **Спойлер:** здесь почти нет пропусков, но данные совсем не «чистые». Цена дома **обрезана сверху**
> на $500 001 (цензура), у заселённости есть район с 1243 жильцами на дом (выброс-ошибка),
> а «очевидная» связь *больше комнат → дороже* **переворачивается**, стоит учесть доход. Ловим всё это по шагам.""")

md("## 0. Подготовка и загрузка (офлайн, из sklearn)")
code(r"""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.datasets import fetch_california_housing

pd.set_option('display.max_columns', None); pd.set_option('display.width', 140)
sns.set_theme(style='whitegrid', palette='deep'); plt.rcParams['figure.dpi'] = 110
RNG = np.random.default_rng(42)

raw = fetch_california_housing(as_frame=True)
df = raw.frame.copy()
print('Размер:', df.shape)
print('Цель: MedHouseVal — медианная цена дома в районе (в сотнях тысяч $)')
df.head()""")

code(r"""df.info()
num_cols = ['MedInc','HouseAge','AveRooms','AveBedrms','Population','AveOccup','MedHouseVal']""")

# ───────────────────────── 1. DATA QUALITY ─────────────────────────
md(r"""## 1. Качество данных — привычка №2

Пропусков нет. Но «нет пропусков» ≠ «данные чистые» — ищем скрытые дефекты глубже.""")
code(r"""quality = pd.DataFrame({
    'dtype'    : df.dtypes.astype(str),
    'n_null'   : df.isna().sum(),
    'null_%'   : (df.isna().mean()*100).round(2),
    'n_unique' : df.nunique(),
    'min'      : df.min(numeric_only=True),
    'max'      : df.max(numeric_only=True),
})
print('Дубликатов строк:', df.duplicated().sum())
quality""")
code(r"""# Скрытый дефект №1 — ЦЕНЗУРА: сколько домов «упёрлись» в потолок цены?
cap = df['MedHouseVal'].max()
n_cap = (df['MedHouseVal'] >= cap - 1e-6).sum()
print(f'Максимум цены = {cap:.5f} (= $500 001).')
print(f'Ровно на потолке: {n_cap} районов ({n_cap/len(df)*100:.1f}%).')
print('Это не настоящие цены, а обрезка сверху — все дороже $500k записаны как $500k.\n')
# Скрытый дефект №2 — невозможные выбросы
print('AveRooms : медиана = {:.1f}, а максимум = {:.1f} комнат на жильё (?!)'.format(
      df['AveRooms'].median(), df['AveRooms'].max()))
print('AveOccup : медиана = {:.1f}, а максимум = {:.1f} человек на жильё (?!)'.format(
      df['AveOccup'].median(), df['AveOccup'].max()))""")
md(r"""**Вердикт по качеству.** Формально 0 пропусков, 0 дублей — но это обманчивая чистота:
1. **Цензура цели:** ~4.8% районов искусственно «обрезаны» на $500k. Любая статистика по цене будет занижена.
2. **Невозможные выбросы:** районы со средними 142 комнатами и 1243 жильцами на дом — это ошибки/крошечные районы.

В синтетике дефектом была *слишком идеальная* чистота. Здесь дефекты реальные и их нужно учитывать в каждом выводе.""")

# ───────────────────────── 2. INTERROGATE COLUMN ─────────────────────────
md(r"""## 2. Допрос колонки `MedHouseVal` (цена дома)

Среднее, медиана, std, квартили — и главный вопрос: **расходятся ли среднее и медиана?**""")
code(r"""s = df['MedHouseVal']
Q1,Q2,Q3 = s.quantile([.25,.5,.75])
for k,v in {
    'count':int(s.count()),'mean':round(s.mean(),3),'median':round(s.median(),3),
    'std':round(s.std(),3),'min':round(s.min(),3),'Q1':round(Q1,3),'Q3':round(Q3,3),
    'max':round(s.max(),3),'IQR':round(Q3-Q1,3),'mean - median':round(s.mean()-s.median(),3),
    'skew (перекос)':round(s.skew(),3),'CV %':round(s.std()/s.mean()*100,1),
}.items(): print(f'  {k:16s}: {v}')""")
md(r"""**Протокол.** `mean = 2.07` заметно **больше** `median = 1.80` (разрыв +0.27, ~15%), `skew ≈ +0.98` →
распределение **скошено вправо**: дорогих районов меньше, но они тянут среднее вверх.

В отличие от синтетики, где `mean ≈ median`, **здесь среднее уже врёт**: «средняя» цена 2.07 выше,
чем у типичного района (1.80). Для скошенных данных честнее опираться на медиану. А ещё помним про цензуру —
истинное среднее ещё выше, потому что дорогие дома обрезаны (раздел 8).""")

# ───────────────────────── 3. DISTRIBUTION + NORMALITY ─────────────────────────
md(r"""## 3. Форма распределения + нормальность (задание №4)""")
code(r"""fig, axes = plt.subplots(2, 4, figsize=(18, 8))
for ax, col in zip(axes.ravel(), num_cols):
    sns.histplot(df[col], kde=True, ax=ax, color='teal', edgecolor='white')
    ax.axvline(df[col].mean(),   color='red',   ls='--', lw=1.5, label='mean')
    ax.axvline(df[col].median(), color='orange',ls=':',  lw=1.5, label='median')
    ax.set_title(col); ax.legend(fontsize=8)
axes.ravel()[-1].axis('off')
plt.suptitle('Распределения: реальные данные скошены, не плоские', y=1.02, fontsize=14)
plt.tight_layout(); plt.show()""")
code(r"""rows=[]
for col in num_cols:
    samp = df[col].sample(min(500,len(df)), random_state=42)
    _,p_sh = stats.shapiro(samp); _,p_da = stats.normaltest(df[col])
    rows.append({'feature':col,'shapiro_p':p_sh,'dagostino_p':p_da,'skew':round(df[col].skew(),2),
                 'нормальное?':'да' if min(p_sh,p_da)>0.05 else 'НЕТ'})
pd.DataFrame(rows).set_index('feature')""")
code(r"""# Q-Q график цены: видно правый скос и «полку» цензуры наверху
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
stats.probplot(df['MedHouseVal'], dist='norm', plot=ax[0]); ax[0].set_title('Q-Q: MedHouseVal (скос + цензура)')
sns.histplot(df['MedHouseVal'], bins=50, ax=ax[1], color='teal')
ax[1].axvline(5.0, color='red', ls='--'); ax[1].set_title('Пик на $500k = обрезанные дома (цензура)')
plt.tight_layout(); plt.show()""")
md(r"""**Вердикт по форме.** Нормальность отвергнута везде — но **причина другая, чем в синтетике**.
Там были плоские равномерные «столешницы»; здесь — **правый скос** (доход, население, цена) и
аномальный **пик на $500k** у цены (цензура видна глазом как столбик у правого края).
Q-Q отклоняется вверх на хвосте — почерк скошенных, а не равномерных данных.""")

# ───────────────────────── 4. BOX PLOT + OUTLIERS ─────────────────────────
md(r"""## 4. Box plot + выбросы (задание №5): здесь они НАСТОЯЩИЕ""")
code(r"""z = (df[num_cols]-df[num_cols].mean())/df[num_cols].std()
plt.figure(figsize=(14,6)); sns.boxplot(data=z, orient='h', palette='Set2')
plt.axvline(0,color='gray',lw=1); plt.title('Box plot (z-стандартизованные) — длинные хвосты выбросов')
plt.xlabel('z-score'); plt.tight_layout(); plt.show()""")
code(r"""rows=[]
for col in num_cols:
    sc=df[col]; Q1,Q3=sc.quantile([.25,.75]); IQR=Q3-Q1
    zc=(sc-sc.mean())/sc.std()
    rows.append({'feature':col,'выбросов_IQR':int(((sc<Q1-1.5*IQR)|(sc>Q3+1.5*IQR)).sum()),
                 '|z|>3':int((zc.abs()>3).sum()),'макс |z|':round(zc.abs().max(),1)})
pd.DataFrame(rows).set_index('feature')""")
code(r"""# Как ОДИН выброс ломает среднее: AveOccup (есть район с 1243 чел/дом)
ao = df['AveOccup']
trimmed = ao[ao < ao.quantile(0.99)]
print(f'AveOccup: mean = {ao.mean():.2f}, median = {ao.median():.2f}, '
      f'mean без верхнего 1% = {trimmed.mean():.2f}, максимум = {ao.max():.0f}')
print('-> Несколько ошибочных районов раздувают среднюю заселённость. Медиана устойчива, среднее — нет.')""")
md(r"""**Вердикт по выбросам.** В отличие от синтетики (0 выбросов), здесь хвосты длинные и реальные:
тысячи точек за усами, `|z|` доходит до десятков. Один район с заселённостью 1243 чел/дом тянет
*среднее* `AveOccup` заметно выше *медианы*. Урок: на реальных данных к среднему всегда прикладывай медиану —
один выброс умеет соврать за всю колонку.""")

# ───────────────────────── 5. CORRELATIONS ─────────────────────────
md(r"""## 5. Корреляции (задание №2): здесь связь ЕСТЬ""")
code(r"""corr = df[num_cols].corr()
plt.figure(figsize=(9,7))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0, vmin=-1, vmax=1, square=True, linewidths=.5)
plt.title('Матрица корреляций — есть реальные связи (в отличие от синтетики)')
plt.tight_layout(); plt.show()""")
code(r"""r,p = stats.pearsonr(df['MedInc'], df['MedHouseVal'])
print(f'MedInc ~ MedHouseVal : r = {r:.3f},  p = {p:.2e}')
print('Доход — сильнейший и осмысленный предиктор цены. Это НАСТОЯЩАЯ связь, а не шум.')""")
md(r"""**Вердикт.** `MedInc ~ MedHouseVal` r ≈ **0.69** — сильная, устойчивая, осмысленная связь
(богаче район → дороже жильё). Контраст с синтетикой, где max |r| был ≈ 0.05.
Но «осмысленная» ≠ «прямая причинно-следственная» — проверяем confounding ниже.""")

# ───────────────────────── 6. PAIR PLOT + CONFOUNDING ─────────────────────────
md(r"""## 6. Pair plot и confounding: связь, которая ПЕРЕВОРАЧИВАЕТСЯ

Самый показательный сюжет реальных данных: «больше комнат → дороже дом» — кажется очевидным.
Проверим частной корреляцией, удержав доход постоянным.""")
code(r"""sample = df.sample(800, random_state=42)
g = sns.pairplot(sample[['MedInc','AveRooms','AveOccup','MedHouseVal']],
                 diag_kind='kde', plot_kws=dict(s=12, alpha=0.3))
g.fig.suptitle('Pair plot (подвыборка): видны реальные тренды и хвосты', y=1.01)
plt.show()""")
code(r"""def partial_corr(d,x,y,z):
    # частная корреляция x,y при контроле z
    rxy=d[x].corr(d[y]); rxz=d[x].corr(d[z]); ryz=d[y].corr(d[z])
    return (rxy-rxz*ryz)/np.sqrt((1-rxz**2)*(1-ryz**2))

simple = df['AveRooms'].corr(df['MedHouseVal'])
part   = partial_corr(df, 'AveRooms', 'MedHouseVal', 'MedInc')
print(f'AveRooms ~ MedHouseVal  (простая)            : r = {simple:+.3f}')
print(f'AveRooms ~ MedHouseVal  (контроль дохода)    : r = {part:+.3f}')
print(f'AveRooms ~ MedInc                            : r = {df.AveRooms.corr(df.MedInc):+.3f}')
print('\n>>> Связь МЕНЯЕТ ЗНАК с + на -. Дело не в комнатах, а в доходе:')
print('    богатые районы имеют и больше комнат, и более дорогое жильё (доход — конфаундер).')""")
md(r"""**Вердикт по confounding.** Простая корреляция говорит «больше комнат → дороже» (r=+0.15).
Но при контроле дохода она **переворачивается в −0.11**: при равном доходе район с *большими* домами
(больше комнат на жильё — это пригороды/село) стоит даже *дешевле*. Иллюзию создавал доход —
он одновременно поднимает и число комнат, и цену.

📌 Это и есть «проверка действительности корреляции»: знак связи может развернуться, стоит учесть третий фактор.
Pearson r из раздела 5 — повод копать, а не готовый вывод.""")

# ───────────────────────── 7. TWO-GROUP T-TEST ─────────────────────────
md(r"""## 7. Сравнение двух групп + t-тест (задание №8): эффект РЕАЛЬНО большой

Делим районы на «богатые» (верхняя треть по доходу) и «бедные» (нижняя треть) и сравниваем цену.
Считаем p-value и Cohen's d.""")
code(r"""lo = df['MedInc'].quantile(1/3); hi = df['MedInc'].quantile(2/3)
poor = df.loc[df['MedInc']<=lo, 'MedHouseVal']
rich = df.loc[df['MedInc']>=hi, 'MedHouseVal']
t,p = stats.ttest_ind(rich, poor, equal_var=False)
pooled = np.sqrt((rich.std()**2 + poor.std()**2)/2)
d = (rich.mean()-poor.mean())/pooled
print(f'Бедные районы (n={len(poor)}): mean цена = {poor.mean():.2f}')
print(f'Богатые районы (n={len(rich)}): mean цена = {rich.mean():.2f}')
print(f'Разница: {rich.mean()-poor.mean():+.2f} (сотен тыс. $)')
print(f't = {t:.1f},  p-value = {p:.2e}')
print(f"Cohen's d = {d:.2f}  (>0.8 — БОЛЬШОЙ эффект)")
plt.figure(figsize=(8,5))
sns.boxplot(x=pd.cut(df['MedInc'],[0,lo,hi,df.MedInc.max()],labels=['бедные','средние','богатые']),
            y=df['MedHouseVal'], palette='YlGnBu')
plt.xlabel('группа по доходу'); plt.title('Цена жилья по доходу района')
plt.tight_layout(); plt.show()""")
md(r"""**Вердикт по t-тесту.** Здесь и p-value ничтожно мал, **и Cohen's d велик** (≫ 0.8) — эффект реальный
и большой. Контраст с синтетикой (там d ≈ 0.04, эффекта не было). Это и есть честный «значимый» результат:
малый p подкреплён большим размером эффекта.""")

# ───────────────────────── 8. STATISTICS THAT LIE (REAL) ─────────────────────────
md(r"""## 8. 🎭 Статистика, которая врёт — на реальных данных

В синтетике мы добывали ложную связь из шума (p-hacking). На реальных данных ложь приходит иначе —
через **дефекты данных**. Два честных примера и одна проверка устойчивости.""")
code(r"""# ЛОЖЬ №1 — ЦЕНЗУРА занижает среднюю цену
cap = df['MedHouseVal'].max(); capped = df['MedHouseVal']>=cap-1e-6
print('Записанное среднее цены        :', round(df['MedHouseVal'].mean(),3))
print(f'Из них {capped.sum()} домов обрезаны на потолке {cap:.2f} — их РЕАЛЬНАЯ цена выше.')
print('=> Истинное среднее БОЛЬШЕ записанного. Статистика занижена самой обрезкой данных.')""")
code(r"""# ЛОЖЬ №2 — ВЫБРОС раздувает среднюю заселённость
ao = df['AveOccup']
print(f'AveOccup: записанное среднее = {ao.mean():.2f}, медиана = {ao.median():.2f}')
print(f'Уберём {int((ao>=ao.quantile(0.999)).sum())} район(ов) с явными ошибками (топ 0.1%):',
      f'среднее -> {ao[ao<ao.quantile(0.999)].mean():.2f}')
print('=> Несколько ошибочных точек двигают «среднюю заселённость города». Медиана им не поддалась.')""")
code(r"""# ПРОВЕРКА устойчивости: настоящая связь доход~цена выживает на 50 случайных подвыборках
rs = []
for i in range(50):
    sub = df.sample(500, random_state=i)
    rs.append(stats.pearsonr(sub['MedInc'], sub['MedHouseVal'])[0])
rs = np.array(rs)
print(f'r(доход, цена) на 50 подвыборках по 500: среднее = {rs.mean():.3f}, '
      f'разброс [{rs.min():.3f}; {rs.max():.3f}]')
print('=> Связь стабильна везде. В отличие от синтетического «призрака», она не исчезает при перепроверке.')""")
md(r"""**Вердикт.** На реальных данных статистика врёт не от пустоты, а от **скрытых дефектов**:
цензура занижает среднюю цену, единичные выбросы раздувают среднюю заселённость. Но настоящая связь
(доход → цена) **устойчива** к перепроверке — это и отличает сигнал от призрака из первого ноутбука.""")

# ───────────────────────── 9. MANUAL CHECK ─────────────────────────
md(r"""## 9. Проверка руками (привычка №3)""")
code(r"""head10 = df['MedInc'].head(10).tolist()
manual = sum(head10)/len(head10); pandas_mean = df['MedInc'].head(10).mean()
print('Первые 10 значений MedInc:', [round(v,3) for v in head10])
print(f'Руками: {manual:.6f} | pandas: {pandas_mean:.6f} | совпадает: {np.isclose(manual,pandas_mean)}')""")

# ───────────────────────── 10. MINI-INVESTIGATION + COMPARISON ─────────────────────────
md(r"""## 10. Мини-расследование + сравнение двух датасетов

| # | Вопрос | Число | Проверка | Вердикт |
|---|--------|-------|----------|---------|
| 1 | Данные чистые? | 0 пропусков, но 4.8% цены обрезаны | потолок $500k, выбросы AveRooms/AveOccup | Чисто от NaN, но есть **цензура и выбросы** |
| 2 | Среднее цены врёт? | mean 2.07 > median 1.80, skew +0.98 | сравнение mean/median | **Скос вправо** — среднее завышает «типичный» район |
| 3 | Распределения нормальные? | Shapiro p<0.05 | Q-Q (скос вверх) + пик цензуры | НЕТ — **скошены**, не равномерны |
| 4 | Есть ли связь? | r(доход, цена) ≈ 0.69 | корреляция + 50 подвыборок | **Настоящая и устойчивая** связь |
| 5 | Связь комнат и цены реальна? | r: +0.15 → −0.11 | частная корреляция (контроль дохода) | **Confounding**: знак переворачивается |

### ⚔️ Синтетика vs Реальность

| Свойство | Smart Traffic (синтетика) | California Housing (реал) |
|----------|---------------------------|---------------------------|
| Пропуски/дубли | 0 (подозрительно идеально) | 0, но есть цензура и выбросы |
| Форма | равномерная (плоская) | скошенная вправо |
| mean vs median | совпадают | расходятся (скос) |
| Выбросы | нет | реальные, длинные хвосты |
| Корреляции | ≈ 0 (шум) | сильные (доход→цена 0.69) |
| Confounding | нечего проверять | связь меняет знак |
| t-тест (Cohen's d) | ≈ 0.04 (нет эффекта) | ≫ 0.8 (большой эффект) |
| Как врёт статистика | p-hacking из шума | цензура + выбросы данных |

### 🎯 Открытие за 30 секунд
> «Реальные данные о жилье врут не как синтетика. Здесь среднее цены завышено скосом и одновременно
> занижено цензурой ($500k-потолок), один район с 1243 жильцами раздувает среднюю заселённость,
> а "больше комнат → дороже" переворачивается в минус, стоит учесть доход. Но настоящая связь
> доход→цена (r=0.69) выдержала 50 перепроверок — это сигнал, а не призрак.»

---
*Формулы посчитала машина. Скепсис остался за мной.* 🕵️""")

nb['cells'] = cells
nb['metadata'] = {'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                  'language_info':{'name':'python'}}
with open('YDL2026_w2_day1_EDA_real_california.ipynb','w',encoding='utf-8') as f:
    nbf.write(nb,f)
print('Real-data notebook written with', len(cells), 'cells')
