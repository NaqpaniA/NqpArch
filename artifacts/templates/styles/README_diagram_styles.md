# Canonical PlantUML diagram styles

## Что это

- `_style_seq_canonical.puml` — базовый стиль для sequence diagram.
- `_style_c4_canonical.puml` — базовый стиль для C4-like диаграмм.
- `sequence_template_canonical.puml` — чистый шаблон sequence.
- `seq_riddle_a_i_b_on_pipe.puml` — пример sequence на загадке «А, И, Б сидели на трубе».

Все макросы вызываются **с символом `$`**.

---

## Sequence: что умеет

- единая типографика и skinparam baseline;
- generic-слои: `User`, `API`, `Core`, `Integration`, `Data`, `External`, `Configuration`, `Ops`;
- participant tags:
  - `<<p_new>>`
  - `<<p_chg>>`
  - `<<p_rm>>`
  - `<<p_legacy>>`
  - `<<p_cfg>>`
  - `<<p_ext>>`
- stereotypes are visible, so you can combine status tags with semantic labels:
  - `<<p_chg>> <<HTTP>>`
  - `<<p_ext>> <<Kafka>>`
  - `<<p_chg>> <<202 Accepted>>`
- макросы для стрелок:
  - sync request
  - async message
  - response `default / ok / warn / err`
- макросы для fragment-ов:
  - `alt / else / opt / loop / par / break / critical / group`
  - пресеты `info / warn / crit`
- секции, задержки и notes;
- встроенные legend-блоки.

### Sequence: text tags

Идея простая:

- контейнеры остаются нативными: `title`, `header`, `footer`, `note`;
- оформление текста задаётся тегами;
- теги свободно вкладываются друг в друга.

Базовые теги:

- `$B("text")` — bold
- `$I("text")` — italic
- `$FONT("DejaVu Sans Mono", "text")` — font family
- `$SIZE("12", "text")` — arbitrary size

Упрощённые size-теги:

- `$XS("text")`
- `$SM("text")`
- `$LG("text")`
- `$XL("text")`

Семантические color-теги:

- `$MUTED("text")`
- `$INFO("text")`
- `$WARN("text")`
- `$CRIT("text")`
- `$NEW("text")`
- `$CHG("text")`
- `$DEL("text")`
- `$CFG("text")`

Дополнительно:

- `$MONO("text")` — моноширинный текст

Пример:

```puml
title
    $B("Order creation")
    $SM($MUTED("Public operation / happy path"))
end title

footer $SM($MUTED("One process = one diagram"))

note right
    $MONO($WARN("payload"))
end note
```

### Sequence: базовое подключение

```puml
@startuml
!pragma teoz true
!include _style_seq_canonical.puml

$SEQ_TITLE($B("Order creation"))
$SEQ_SUBTITLE($SM($MUTED("Public operation / happy path")))
$SEQ_LEGEND_FULL_TOP_RIGHT()
$SEQ_FOOTER_NOTE("One process = one diagram")

$SEQ_LAYER_USER_BEGIN()
    actor Client
$SEQ_LAYER_END()

$SEQ_LAYER_API_BEGIN()
    boundary API <<p_chg>> <<HTTP>>
$SEQ_LAYER_END()

$SEQ_LAYER_CORE_BEGIN()
    control OrderService <<p_new>> <<Application>>
$SEQ_LAYER_END()

$SEQ_REQ_CHG(Client, API, "POST /orders")
$SEQ_REQ_NEW(API, OrderService, "createOrder()")
$SEQ_RESP(OrderService, API, "orderId")
$SEQ_RESP(API, Client, "202 Accepted")
@enduml
```

### Sequence: arrows and fragments

Если нужен полный контроль, используем нативный PlantUML, а цвета берём из style-переменных.

Стрелки:

- `a -[$C_CHG]-> b : changed sync`
- `a -[$C_NEW]>> b : new async`
- `a --[$C_NEW]> b : ok response`
- `a -[$C_DEL]-> b : removed / delete / drop`

Фрагменты:

- `group#$FR_WARN_HEAD #$FR_WARN_BG Validation`
- `group#$FR_CRIT_HEAD #$FR_CRIT_BG Hard stop`
- `alt#$FR_INFO_HEAD #$FR_INFO_BG Main path`
- `opt#$FR_WARN_HEAD #$FR_WARN_BG Fallback`

Пример:

```puml
== Validation ==
group#$FR_WARN_HEAD #$FR_WARN_BG Validation warnings
    API -[$C_CHG]-> Service : validate()
    Service --[$C_NEW]> API : ok
end
```

### Sequence: guideline

- контейнеры лучше оставлять нативными;
- текст лучше стилизовать тегами, а не raw HTML;
- стрелки лучше рисовать руками, если нужен точный контроль формы;
- semantic helpers полезны как тонкий слой стандарта, а не как новая нотация поверх PlantUML.

---

## C4-like: что умеет

- нейтральный baseline для context / container / component views;
- boundary helpers:
  - solution
  - domain
  - external
- relation helpers:
  - sync / async
  - `new / changed / removed / config / legacy`
- notes и legend-блоки;
- нейтральная семантическая палитра без проектной грязи.

### C4-like: базовое подключение

```puml
@startuml
!include _style_c4_canonical.puml

$C4_TITLE_WITH_SUBTITLE("Order flow", "Container view")
$C4_LEGEND_STATUS_BOTTOM_RIGHT()

$C4_BOUNDARY_SOLUTION_BEGIN("Order solution")
    rectangle API as api <<Service>>
    rectangle Core as core <<Service>>
    database DB as db <<Database>>
$C4_BOUNDARY_END()

rectangle Partner as ext <<External>>

$C4_SYNC_CHG(api, core, "createOrder()")
$C4_SYNC_NEW(core, db, "persist")
$C4_ASYNC_NEW(core, ext, "event")
@enduml
```

---

## Как использовать в команде

- не красить стрелки и связи руками;
- держать project-specific палитру в отдельных thin-wrapper style-файлах;
- использовать canonical styles как общий baseline;
- для sequence придерживаться правила: **1 публичная операция = 1 диаграмма**.
