# Buddy Protocol: Neon Quarantine

**Game Design Document / Prompt Pack для Claude Code и Claude Design**  
**Формат проекта:** 2D browser action game в одном `index.html` файле, с ощущением псевдо-3D экшена.  
**Цель:** быстро собрать рабочую игру для демонстрации, а затем улучшать визуал, анимации и баланс.

---

## 1. Короткое описание игры

**Buddy Protocol: Neon Quarantine** — это 2D survival-action игра с видом сверху под углом, где игрок управляет персонажем с клавиатуры, убегает от орды мобов и автоматически стреляет в ближайших врагов. Игра визуально должна ощущаться не как плоская 2D-аркада, а как динамичный псевдо-3D экшен: тени, глубина, стены между комнатами, эффект камеры, частицы, свет, параллакс и сортировка объектов по глубине.

Игрок оказывается в заброшенном техно-комплексе после сбоя искусственного интеллекта. Его сопровождает маленький помощник **Buddy** — дрон-компаньон, который объясняет управление, правила и помогает пройти onboarding. Buddy двигается рядом с игроком, дает подсказки и в начале имеет две кнопки: **Next** и **Skip**.

Игровой цикл простой: игрок двигается по случайно сгенерированной локации, избегает мобов, оружие автоматически целится и стреляет, враги идут волнами, игрок набирает очки и пытается выжить как можно дольше.

---

## 2. Почему такой формат подходит под лабораторную

Задание из лабораторной просит к финалу собрать игру, которая открывается прямо в браузере как один HTML-файл с JavaScript внутри. Главное — сначала сделать минимально рабочую версию, затем улучшать: счет, рекорд, рестарт, уровни сложности, звук, таймер и другие детали. Поэтому проект должен быть устроен как **vibe coding MVP**: сначала запускаем базовую игру, потом добавляем polish.

**Техническая стратегия:**

- **GPT** — мозг проекта: помогает формировать механику, сюжет, баланс, промпты и логику.
- **Claude Code** — основной разработчик: пишет `index.html`, JavaScript, Canvas-логику, управление, столкновения, UI и игровые состояния.
- **Claude Design** — визуальный дизайнер: создает персонажа, Buddy, мобов, окружение, UI-кнопки, плитки карты и фон.

---

## 3. Название и жанр

**Название:** Buddy Protocol: Neon Quarantine  
**Жанр:** 2D survival shooter / auto-aim action / pseudo-3D dungeon arena  
**Камера:** top-down 3/4 view, немного похожая на изометрическую, но проще для браузерной реализации.  
**Платформа:** Browser, single HTML file.  
**Управление:** Keyboard only.

---

## 4. Сюжет

В 2086 году подземный исследовательский комплекс **N-7** был закрыт после аварии в системе защиты. Искусственный интеллект комплекса начал создавать зараженных охранных дронов и биомеханических существ. Главный герой — техник-оператор, который просыпается внутри комплекса после отключения электроэнергии.

Единственный союзник — маленький AI-дрон **Buddy**. Он был создан как обучающий помощник для сотрудников, но после аварии стал проводником героя. Buddy объясняет управление, предупреждает об опасности и помогает игроку выбраться через зараженные секции комплекса.

Игрок не управляет прицелом вручную. Его оружие подключено к системе Buddy, поэтому оно автоматически выбирает ближайшую цель и стреляет по ней. Задача игрока — правильно двигаться, держать дистанцию, использовать стены и комнаты, не дать орде окружить себя.

**Главная цель MVP:** выжить 3 минуты или набрать как можно больше очков.  
**Расширенная цель:** пройти несколько комнат, пережить волны врагов и добраться до эвакуационного портала.

---

## 5. Основной игровой цикл

1. Игрок появляется в стартовой комнате.
2. Buddy показывает onboarding: движение, авто-стрельба, враги, цель игры.
3. Игрок нажимает Start.
4. Локация генерируется случайно: комнаты, стены, коридоры, ограждения.
5. Мобы появляются волнами и идут к игроку.
6. Игрок двигается с клавиатуры и уклоняется.
7. Оружие автоматически находит ближайшего моба и стреляет.
8. За уничтожение мобов игрок получает очки.
9. Сложность постепенно растет: больше мобов, выше скорость, больше HP.
10. При смерти показывается экран Game Over с итоговым счетом и кнопкой Restart.

---

## 6. Игровые flow

### 6.1. First Launch / Onboarding

Когда пользователь впервые открывает игру, сразу появляется Buddy.

**Поведение Buddy:**

- Buddy — маленький летающий дрон 48x48 px.
- Он слегка покачивается вверх-вниз.
- Он держится рядом с игроком, но не мешает движению.
- У него есть небольшая диалоговая панель.
- В панели две кнопки: **Next** и **Skip**.

**Onboarding steps:**

1. **Welcome**  
   Buddy: “Welcome to N-7. I am Buddy. Stay close — this place is infected.”
2. **Movement**  
   Buddy: “Move with WASD or Arrow Keys. Keep moving, never stand still.”
3. **Auto-aim**  
   Buddy: “Your weapon is synced with me. It automatically targets the nearest enemy.”
4. **Enemies**  
   Buddy: “Mobs will chase you in waves. Use walls and corridors to survive.”
5. **Goal**  
   Buddy: “Survive as long as possible. Ready? Press Start.”

**Кнопки:**

- `Next` — переходит к следующему шагу.
- `Skip` — пропускает onboarding и открывает main screen.

---

### 6.2. Main Screen

Главный экран должен выглядеть как игровой терминал внутри мира, а не как обычное веб-меню.

**Элементы:**

- Название игры: `BUDDY PROTOCOL`
- Подзаголовок: `NEON QUARANTINE`
- Кнопка `START`
- Кнопка `SETTINGS`
- Маленький Buddy рядом с меню.
- Анимация ожидания: фон немного движется, неон мигает, Buddy плавает, игрок стоит в idle-позе.

**Стиль:**

- Темный sci-fi background.
- Неоновые акценты.
- Панели как holographic UI.
- Легкий эффект scanlines.
- Кнопки должны светиться при hover.

---

### 6.3. Settings Screen

Минимальные настройки:

- Difficulty: Easy / Normal / Hard
- Sound: On / Off
- Show Controls: On / Off
- Back button

Для MVP можно сделать настройки визуально, даже если часть из них пока влияет только на сложность.

---

### 6.4. Gameplay Screen

**HUD:**

- HP bar слева сверху.
- Score справа сверху.
- Timer по центру сверху.
- Wave number под таймером.
- Маленькая иконка Buddy рядом с подсказками.

**Игрок:**

- Двигается клавишами WASD или стрелками.
- Не целится вручную.
- Автоматически стреляет в ближайшего моба.
- Получает урон при контакте с мобами.
- Имеет короткую анимацию урона: красная вспышка / shake.

**Мобы:**

- Появляются волнами.
- Идут к игроку через комнаты и коридоры.
- Для MVP можно использовать простое движение по прямой с обходом стен через базовую логику.
- При касании наносят урон.
- При смерти исчезают с частицами.

**Локация:**

- Случайно сгенерированная карта.
- Комнаты связаны коридорами.
- Есть стены, ограждения, ящики, колонны.
- Игрок может бегать из комнаты в комнату.
- Стены блокируют движение.

---

## 7. Управление

| Action | Keyboard |
|---|---|
| Move up | W / Arrow Up |
| Move down | S / Arrow Down |
| Move left | A / Arrow Left |
| Move right | D / Arrow Right |
| Dash, optional | Shift |
| Pause | Esc / P |
| Restart after death | R |

**Важно:** стрельба работает автоматически. Игрок должен думать о движении, дистанции и позиционировании.

---

## 8. Механика auto-aim

Auto-aim должен работать так:

1. Каждые `300-450 ms` оружие ищет ближайшего живого моба.
2. Если моб найден в радиусе `500 px`, игрок стреляет в него.
3. Пуля летит от игрока к позиции моба на момент выстрела.
4. Если пуля попадает — моб получает урон.
5. Если моб погибает — игрок получает очки.

**Параметры MVP:**

- Player HP: `100`
- Player speed: `240 px/sec`
- Bullet speed: `650 px/sec`
- Bullet damage: `25`
- Fire rate: `350 ms`
- Mob HP: `50`
- Mob speed: `70-110 px/sec`
- Mob contact damage: `10 HP/sec`
- Score per kill: `10`

---

## 9. Псевдо-3D ощущение в 2D

Чтобы игра не ощущалась слишком плоской, нужно добавить:

1. **Top-down 3/4 camera** — вид сверху под углом.
2. **Depth sorting** — объекты ниже на экране рисуются поверх объектов выше.
3. **Shadows** — эллиптические тени под игроком, мобами, Buddy и объектами.
4. **Wall height illusion** — стены должны быть выше пола: tile 64x96, но collision area около 64x32 внизу.
5. **Camera smoothing** — камера плавно следует за игроком.
6. **Screen shake** — легкий shake при получении урона и смерти моба.
7. **Particles** — искры при выстреле, красно-фиолетовый дым при смерти моба.
8. **Lighting** — неоновые лампы, glow вокруг пуль и UI.
9. **Parallax background** — далекий темный фон движется медленнее карты.

---

## 10. Требования к Claude Code

Claude Code должен сделать игру в одном файле:

```text
index.html
```

Внутри файла должны быть:

- HTML markup
- CSS styles
- JavaScript game logic
- Canvas 2D rendering
- No external dependencies
- No build step
- No npm required
- Игра должна запускаться двойным кликом по `index.html`

### 10.1. Game states

Использовать состояния:

```js
const GameState = {
  ONBOARDING: 'onboarding',
  MENU: 'menu',
  SETTINGS: 'settings',
  PLAYING: 'playing',
  PAUSED: 'paused',
  GAME_OVER: 'game_over'
};
```

### 10.2. Code structure

Желательная структура внутри JS:

- `InputManager`
- `Game`
- `Player`
- `Buddy`
- `Mob`
- `Bullet`
- `Particle`
- `LevelGenerator`
- `CollisionSystem`
- `Renderer`
- `UIManager`

### 10.3. Минимальный MVP

Первый рабочий результат должен включать:

- Main menu
- Start button
- Player movement
- Random map with rooms and walls
- Mobs chasing player
- Auto-aim shooting
- HP, score, timer
- Game over and restart

### 10.4. После MVP добавить polish

- Onboarding Buddy with Next / Skip
- Settings screen
- Idle animation on main menu
- Particles
- Screen shake
- Difficulty
- Sound effects
- Best score in localStorage
- Better map generation
- Better enemy waves

---

## 11. Prompt для Claude Code

Скопируй этот prompt в Claude Code:

```text
Create a browser game in a single index.html file. Do not use external libraries, npm, or build tools. Use HTML, CSS, JavaScript, and Canvas 2D only.

Game title: Buddy Protocol: Neon Quarantine.

I need a 2D survival action game with a pseudo-3D feeling. The player moves with WASD or Arrow Keys. The player does not aim manually. The weapon must auto-aim at the nearest mob and shoot automatically every 350ms.

Game flow:
1. First launch onboarding with a floating AI companion named Buddy. Buddy has a dialogue box and two buttons: Next and Skip. Buddy explains movement, auto-aim, enemies, and survival goal.
2. Main menu with game-style animated background, title, Start button, Settings button, idle player animation, and floating Buddy animation.
3. Settings screen with difficulty Easy / Normal / Hard, sound On / Off, and Back button.
4. Gameplay screen.
5. Game over screen with score, best score, Restart, and Main Menu.

Gameplay:
- Player has 100 HP and moves at 240 px/sec.
- Mobs spawn in waves and chase the player.
- Mobs deal contact damage.
- Auto-aim finds nearest mob within 500px and fires bullets.
- Bullets travel at 650 px/sec and deal 25 damage.
- Killing mobs gives score.
- Difficulty increases over time.

Map:
- Generate a random dungeon-like map with rooms, corridors, walls, fences, crates, and obstacles.
- Use a grid/tile system.
- Walls and obstacles must block movement.
- Player should be able to run from one room to another.
- Add simple collision detection.

Visual style:
- Dark sci-fi neon quarantine facility.
- Pseudo-3D top-down 3/4 style.
- Use shadows under characters.
- Sort entities by Y position for depth.
- Add glowing bullets, particle effects, damage flash, and small screen shake.
- If image assets are not available, draw high-quality placeholder shapes on Canvas but structure the code so assets can be replaced later.

UI:
- HP bar, score, timer, wave number.
- Neon game-style buttons.
- Smooth hover effects.
- Pause with P or Esc.
- Restart with R after death.

Code requirements:
- One index.html file only.
- Clean readable JS classes: Game, Player, Buddy, Mob, Bullet, Particle, LevelGenerator, InputManager, UIManager.
- Add comments where important.
- Make it playable immediately.
- Do not make a static mockup; it must be a working game.
```

---

## 12. Claude Design: общий визуальный стиль

### 12.1. Art direction

**Style:** dark sci-fi, neon, pseudo-3D top-down, action survival, polished game UI.  
**Mood:** dangerous but playful, intense but readable.  
**Camera feel:** 2D sprites with top-down 3/4 perspective.  
**Lighting:** cyan, purple and red neon highlights.  
**Important:** Do not add text inside generated images unless specifically requested. Text should be made in HTML/CSS.

### 12.2. Color palette

Use these colors consistently:

| Purpose | Color |
|---|---|
| Deep background | `#080B16` |
| Dark floor | `#12192B` |
| Panel dark | `#172033` |
| Neon cyan | `#42E8F4` |
| Neon purple | `#7D4DFF` |
| Warning amber | `#FFB84D` |
| Damage red | `#FF4D6D` |
| Toxic green | `#66FF99` |
| Soft white | `#EAF6FF` |
| Shadow | `rgba(0,0,0,0.45)` |

### 12.3. Asset format rules

- Sprites: PNG with transparent background.
- UI panels: PNG or can be recreated with CSS.
- Tile assets: PNG, no text.
- Keep consistent perspective.
- Use clean silhouettes because the game is fast.
- Avoid tiny details that disappear at 64x64.
- All animation frames must have the same canvas size.
- Character feet should stay in the same position across frames.

---

## 13. Claude Design prompts

### 13.1. Player character sprite sheet

```text
Create a 2D game character sprite sheet for a browser survival action game.

Style: dark sci-fi neon, pseudo-3D top-down 3/4 perspective, readable at small size, clean silhouette, polished indie game asset.

Character: young technician survivor wearing a compact dark tactical jacket, small glowing cyan visor, light armor plates, small backpack power unit, and a compact energy blaster. The character should look agile, not bulky.

Color palette: dark navy base, cyan neon highlights, subtle purple rim light, small amber details.

Output requirements:
- PNG with transparent background.
- Sprite sheet with equal frame sizes.
- Each frame: 64x64 pixels.
- 4 rows, 3 columns.
- Row 1: idle animation, 3 frames.
- Row 2: running animation, 3 frames.
- Row 3: shooting animation, 3 frames.
- Row 4: damage / hit reaction animation, 3 frames.
- Keep feet aligned in every frame.
- No text, no background, no UI.
```

### 13.2. Buddy companion sprite sheet

```text
Create a small floating AI drone companion named Buddy for a 2D browser game.

Style: cute but futuristic, dark sci-fi neon, pseudo-3D top-down 3/4 perspective.

Design: small round drone with one cyan glowing eye, tiny side wings, holographic ring, soft blue glow, friendly expression. It should feel like a helpful AI companion.

Output requirements:
- PNG with transparent background.
- Sprite sheet with equal frame sizes.
- Each frame: 48x48 pixels.
- 1 row, 4 columns.
- Animation: idle floating / bobbing, 4 frames.
- No text, no background.
```

### 13.3. Basic mob sprite sheet

```text
Create an enemy mob sprite sheet for a 2D survival action game.

Style: dark sci-fi infected creature, pseudo-3D top-down 3/4 perspective, readable at 64x64, dangerous but not too detailed.

Enemy design: corrupted bio-mechanical zombie creature, hunched body, glowing red/purple cracks, dark shell, aggressive posture. It should look like it can run toward the player in a horde.

Output requirements:
- PNG with transparent background.
- Sprite sheet with equal frame sizes.
- Each frame: 64x64 pixels.
- 3 rows, 3 columns.
- Row 1: walking animation, 3 frames.
- Row 2: attack / lunge animation, 3 frames.
- Row 3: death / dissolve animation, 3 frames.
- Keep feet aligned.
- No text, no background.
```

### 13.4. Dungeon floor tiles

```text
Create a tile set for a dark sci-fi quarantine facility in a 2D pseudo-3D top-down game.

Style: neon sci-fi, abandoned underground lab, dark floor panels, subtle cyan and purple light, clean readable game asset.

Output requirements:
- PNG tile sheet.
- Each tile: 64x64 pixels.
- 4 rows, 4 columns.
- Include: normal floor, cracked floor, metal floor, glowing floor line, hazard floor, dark corner floor, dirty floor, wet floor, small debris floor, energy cable floor, broken panel floor, clean panel floor, and several variations.
- No text.
- No characters.
```

### 13.5. Walls, fences and obstacles

```text
Create a tile sheet of walls and obstacles for a dark sci-fi 2D pseudo-3D top-down game.

Style: abandoned neon quarantine facility, dark metal walls, cyan/purple highlights, readable silhouettes.

Output requirements:
- PNG with transparent background where needed.
- Each wall/object frame should fit into 64x96 pixels.
- Include wall segments, corner walls, metal fences, broken fences, crates, energy barriers, pillars, door frame, and broken lab equipment.
- The bottom 64x32 area should visually represent the collision base.
- Objects should look taller than floor tiles to create pseudo-3D depth.
- No text.
```

### 13.6. Main menu background

```text
Create a game main menu background for Buddy Protocol: Neon Quarantine.

Style: dark sci-fi neon quarantine facility, cinematic pseudo-3D, abandoned lab corridor, glowing cyan and purple lights, subtle fog, dramatic but clean.

Composition:
- Empty center area for game title and buttons.
- Player character silhouette on the left side in idle pose.
- Small floating Buddy drone on the right side.
- Background should feel alive and atmospheric but not too busy.

Output requirements:
- 1280x720 image.
- No text.
- Leave space in the center for UI.
- Dark background with neon accents.
```

### 13.7. UI button style

```text
Create a game UI button design set for a dark sci-fi neon browser game.

Style: holographic terminal UI, cyan neon border, dark transparent fill, subtle purple glow, sharp but readable.

Output requirements:
- Transparent PNG.
- Include 3 button states: normal, hover, pressed.
- Button size: 260x72 pixels.
- Do not include text inside the buttons.
- Text will be added in HTML/CSS.
```

### 13.8. HUD icons

```text
Create small HUD icons for a dark sci-fi survival action game.

Style: neon cyber interface, simple, readable at 32x32.

Icons needed:
- HP / heart or shield
- Score / energy core
- Timer
- Wave
- Settings gear
- Pause
- Bullet / weapon

Output requirements:
- PNG with transparent background.
- Each icon: 32x32 pixels.
- Consistent cyan/purple neon style.
- No text.
```

---

## 14. Asset naming convention

Use this structure:

```text
/assets
  /characters
    player_spritesheet_64.png
    buddy_idle_48.png
  /enemies
    mob_basic_spritesheet_64.png
  /environment
    floor_tiles_64.png
    walls_obstacles_64x96.png
  /ui
    button_states_260x72.png
    hud_icons_32.png
  /backgrounds
    main_menu_bg_1280x720.png
```

Even if the final lab version is one HTML file, keep this naming convention while developing. For final one-file version, assets can be embedded as base64 or replaced with Canvas placeholders.

---

## 15. Visual acceptance checklist

Claude Design assets are acceptable only if:

- All frames in a sprite sheet have the same size.
- Player, Buddy and mobs are clearly readable at gameplay scale.
- There is no text inside images.
- Transparent backgrounds are clean.
- Perspective is consistent.
- Colors match dark sci-fi neon style.
- Player does not blend into the floor.
- Mobs look clearly dangerous and visually different from the player.
- Environment tiles can be repeated without looking broken.

---

## 16. Gameplay acceptance checklist

The game is acceptable only if:

- `index.html` opens in browser by double click.
- Start button begins the game.
- Player moves smoothly with keyboard.
- Mobs chase the player.
- Player auto-shoots without mouse input.
- Bullets hit mobs and mobs die.
- HP decreases when mobs touch the player.
- Score increases after kills.
- Timer works.
- Game over screen appears when HP reaches zero.
- Restart works.
- There is at least basic random map generation with walls and rooms.
- Onboarding with Buddy has Next and Skip.

---

## 17. Recommended development order

### Phase 1 — Working prototype

1. Create `index.html`.
2. Add canvas and game loop.
3. Add player movement.
4. Add simple rectangular map boundaries.
5. Add mobs chasing player.
6. Add auto-aim and bullets.
7. Add HP, score and game over.

### Phase 2 — Game flow

1. Add onboarding with Buddy.
2. Add main menu.
3. Add settings.
4. Add restart and best score.

### Phase 3 — Map and action feel

1. Add random rooms and corridors.
2. Add wall collision.
3. Add camera smoothing.
4. Add Y-depth sorting.
5. Add shadows.

### Phase 4 — Polish

1. Add particles.
2. Add screen shake.
3. Add glow effects.
4. Add difficulty scaling.
5. Add sound.
6. Replace placeholders with Claude Design assets.

---

## 18. Short pitch for presentation

**Buddy Protocol: Neon Quarantine** is a browser-based 2D survival action game with a pseudo-3D feel. The player moves through a randomly generated quarantine facility while hordes of mobs chase them. Instead of manual aiming, the weapon uses Buddy AI to auto-target enemies, so the core gameplay is movement, positioning and survival. The project uses GPT for game logic and design planning, Claude Code for implementation, and Claude Design for characters, enemies and environment assets.

---

## 19. One-sentence concept

A keyboard-controlled pseudo-3D 2D survival shooter where a Buddy AI companion teaches the player, follows them, and powers an auto-aim weapon against endless waves of mobs inside a neon quarantine facility.
