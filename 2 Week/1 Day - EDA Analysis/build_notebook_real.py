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

# ═════════════════════════════════════════════════════════════════════
#  REVIEW: другие связи, omitted variable bias, обрезка колонок
# ═════════════════════════════════════════════════════════════════════

md(r"""# 🔬 11. Review всех связей: что меняется при контроле остальных признаков

В разделе 6 мы разобрали одну пару (комнаты ~ цена). Теперь проверим **все** признаки разом:
сравним простую корреляцию с ценой и коэффициент регрессии, где *одновременно* учтены все остальные
признаки (это многомерный аналог частной корреляции). Где знак меняется — там пряталось искажение.""")
code(r"""import statsmodels.api as sm
feats  = ['MedInc','HouseAge','AveRooms','AveBedrms','Population','AveOccup','Latitude','Longitude']
target = 'MedHouseVal'
# стандартизуем, чтобы коэффициенты были сопоставимы (как корреляции)
Z = (df[feats+[target]] - df[feats+[target]].mean()) / df[feats+[target]].std()
ols = sm.OLS(Z[target], sm.add_constant(Z[feats])).fit()

review = pd.DataFrame({
    'simple_r'              : [df[f].corr(df[target]) for f in feats],
    'beta (контроль всех)'  : [ols.params[f] for f in feats],
}, index=feats)
review['знак сменился?'] = np.where(
    np.sign(review['simple_r']) != np.sign(review['beta (контроль всех)']), 'ДА', '')
print('R^2 полной модели:', round(ols.rsquared, 3))
review.round(3)""")
code(r"""ax = review[['simple_r','beta (контроль всех)']].plot.barh(figsize=(10,6))
ax.axvline(0, color='k', lw=1)
ax.set_title('Простая корреляция vs коэффициент при контроле ВСЕХ признаков')
ax.set_xlabel('сила связи с ценой')
plt.tight_layout(); plt.show()""")
md(r"""**Вердикт по связям.** Картина «больше комнат → дороже» была не единственной иллюзией:

- **`AveRooms`**: simple +0.15 → beta **−0.23** (знак сменился). Конфаундер — доход.
- **`AveBedrms`**: simple −0.05 → beta **+0.27** (знак сменился). При равных комнатах больше спален = чуть дороже,
  но в одиночку признак выглядел нейтральным — его маскировала корреляция с `AveRooms`.
- **`Latitude`/`Longitude`**: маленькая простая связь (−0.14 / −0.05), но огромные beta (−0.78 / −0.75).
  Это **подавление (suppression)**: по отдельности гео-координата почти ни о чём, но вместе они кодируют
  «насколько южнее и западнее = ближе к побережью = дороже». География — мощнейший фактор после дохода.
- **`MedInc`** — единственный, кто и в простой, и в полной модели сильнейший (+0.69 / +0.72). Настоящий драйвер.

📌 Простая корреляция — это первый взгляд. Истину показывает только модель, где факторы конкурируют за объяснение.""")

md(r"""# 🧪 12. Что будет, если убрать колонку (ablation + omitted variable bias)

Два эксперимента: (1) убираем по одному признаку из модели и смотрим, насколько просядет R²
(кто реально несёт сигнал); (2) убираем **конфаундер** и наблюдаем, как оживает ложная связь.""")
code(r"""full_r2 = ols.rsquared
drops = []
for f in feats:
    sub = [c for c in feats if c != f]
    r2 = sm.OLS(Z[target], sm.add_constant(Z[sub])).fit().rsquared
    drops.append({'убрали колонку': f, 'R2 без неё': round(r2,3), 'падение R2': round(full_r2-r2,4)})
drops = pd.DataFrame(drops).sort_values('падение R2', ascending=False).reset_index(drop=True)
print('R2 полной модели:', round(full_r2,3))
drops""")
code(r"""plt.figure(figsize=(10,5))
sns.barplot(data=drops, y='убрали колонку', x='падение R2', palette='Reds_r')
plt.title('Насколько падает R², если убрать колонку (вклад в объяснение цены)')
plt.tight_layout(); plt.show()""")
code(r"""# OMITTED VARIABLE BIAS: коэффициент AveRooms с доходом и без
b_alone = sm.OLS(Z[target], sm.add_constant(Z[['AveRooms']])).fit().params['AveRooms']
b_ctrl  = sm.OLS(Z[target], sm.add_constant(Z[['AveRooms','MedInc']])).fit().params['AveRooms']
print(f'AveRooms БЕЗ дохода в модели : beta = {b_alone:+.3f}  -> «больше комнат = дороже»')
print(f'AveRooms С доходом в модели  : beta = {b_ctrl:+.3f}  -> правда: при равном доходе ДЕШЕВЛЕ')
print('\n>>> Стоит выкинуть конфаундер (доход) — и ложная положительная связь возвращается как «реальная».')
print('>>> Это omitted variable bias: пропущенная переменная переписывает выводы.')""")
md(r"""**Вердикт по ablation.**
- **Сигнал держится на немногих колонках.** Убрать `MedInc` → R² рушится 0.61 → 0.40. Убрать `Latitude`/`Longitude` →
  −0.06 каждая. А `Population`, `AveOccup`, `AveRooms`, `AveBedrms`, `HouseAge` можно выкинуть почти без потерь
  (−0.01 и меньше) — по отдельности они мало что добавляют поверх дохода и географии.
- **Omitted variable bias — главная ловушка.** Уберёшь доход из модели — и `AveRooms` снова «доказывает»,
  что комнаты повышают цену (+0.15). Это ровно тот механизм, которым отчёты обманывают: показать связь,
  *умолчав* о третьей переменной, которая всё объясняет.""")

md(r"""# ✂️ 13. Что будет, если обрезать колонку (выбросы и цензура)

Обрезка — не косметика. Покажем три случая, где удаление «кривых» значений **меняет вывод**.""")
code(r"""rows = []
cap = df[target].max()
# 1) убрать цензурированные дома (цена упёрта в потолок)
nocap = df[df[target] < cap - 1e-6]
rows.append({'операция':'убрать цензуру (цена = потолок $500k)','связь':'corr(MedInc, price)',
             'было':round(df['MedInc'].corr(df[target]),3),
             'стало':round(nocap['MedInc'].corr(nocap[target]),3)})
# 2) обрезать топ-1% выбросов AveOccup
q=df['AveOccup'].quantile(0.99); t=df[df['AveOccup']<q]
rows.append({'операция':'убрать топ-1% AveOccup (выбросы)','связь':'corr(AveOccup, price)',
             'было':round(df['AveOccup'].corr(df[target]),3),
             'стало':round(t['AveOccup'].corr(t[target]),3)})
# 3) обрезать топ-1% выбросов AveRooms
q=df['AveRooms'].quantile(0.99); t=df[df['AveRooms']<q]
rows.append({'операция':'убрать топ-1% AveRooms (выбросы)','связь':'corr(AveRooms, price)',
             'было':round(df['AveRooms'].corr(df[target]),3),
             'стало':round(t['AveRooms'].corr(t[target]),3)})
trunc = pd.DataFrame(rows)
trunc['изменение'] = (trunc['стало']-trunc['было']).round(3)
trunc""")
code(r"""# Наглядно: выбросы AveOccup ПРЯТАЛИ реальную отрицательную связь с ценой
q = df['AveOccup'].quantile(0.99); clean = df[df['AveOccup'] < q]
fig, ax = plt.subplots(1, 2, figsize=(14,5))
sns.scatterplot(x='AveOccup', y=target, data=df, s=8, alpha=.3, ax=ax[0])
ax[0].set_title(f'С выбросами: связь почти плоская (r={df.AveOccup.corr(df[target]):.2f})')
sns.regplot(x='AveOccup', y=target, data=clean, scatter_kws=dict(s=8,alpha=.2),
            line_kws=dict(color='red'), ax=ax[1])
ax[1].set_title(f'Без топ-1%: проступает связь (r={clean.AveOccup.corr(clean[target]):.2f}) — теснее = дешевле')
plt.tight_layout(); plt.show()""")
md(r"""**Вердикт по обрезке.** Удаление значений меняет не цифру после запятой, а сам вывод:

- **Выбросы могут ПРЯТАТЬ связь.** `corr(AveOccup, price)` был ≈ **−0.02** («связи нет») — но это эффект
  нескольких районов с заселённостью в сотни человек. Уберём топ-1% → corr становится **−0.28**:
  чем теснее живут, тем жильё дешевле. Реальная связь была погребена под выбросами.
- **Выбросы могут РАЗМЫВАТЬ связь.** `corr(AveRooms, price)` 0.15 → **0.33** после обрезки — выбросы её ослабляли.
- **Цензура завышает связь.** `corr(MedInc, price)` 0.69 → **0.64** без обрезанных домов: потолок $500k
  искусственно «выпрямляет» верх облака и раздувает корреляцию.

📌 Поэтому к любому числу — вопрос: *на каких строках оно посчитано и что выкинули перед подсчётом?*
Обрезка выбросов и цензура способны и создать связь, и убить её.""")

md(r"""# 🧾 14. Итог review

| Что проверяли | Находка | Чему учит |
|---------------|---------|-----------|
| Все связи при контроле остальных | `AveRooms` +→−, `AveBedrms` −→+, гео даёт suppression | Простая корреляция врёт; нужна модель |
| Drop-one (важность колонок) | Сигнал на `MedInc` (−0.21 R²) и гео; остальное лишнее | Объяснение держится на 2–3 признаках |
| Убрать конфаундер (доход) | `AveRooms` beta +0.15 → −0.08 | **Omitted variable bias** — ложная связь оживает |
| Обрезать выбросы `AveOccup` | corr −0.02 → −0.28 | Выбросы **прячут** реальную связь |
| Обрезать выбросы `AveRooms` | corr 0.15 → 0.33 | Выбросы **размывают** связь |
| Убрать цензуру цены | corr 0.69 → 0.64 | Цензура **завышает** корреляцию |

> **Главный вывод review:** ни одну связь в реальных данных нельзя брать по простой корреляции.
> Знак переворачивается при контроле конфаундера, важность колонки видна только в ablation,
> а обрезка выбросов/цензуры способна и создать связь, и стереть её. Скепсис — не к данным, а к каждому числу.""")

nb['cells'] = cells
nb['metadata'] = {'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                  'language_info':{'name':'python'}}
with open('YDL2026_w2_day1_EDA_real_california.ipynb','w',encoding='utf-8') as f:
    nbf.write(nb,f)
print('Real-data notebook written with', len(cells), 'cells')
