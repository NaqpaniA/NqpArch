# PlantUML Diagram Styles

Базовый набор стилей для архитектурных диаграмм в PlantUML.

## Файлы

- `_style_seq_canonical.puml` — базовый стиль для sequence diagrams.
- `_style_c4_canonical.puml` — базовый стиль для C4-like диаграмм.

## Зачем это нужно

- единый визуальный стиль для команды;
- меньше ручной покраски и копипасты;
- повторно используемые макросы для типовых сценариев;
- понятная семантика изменений: new / changed / removed / config / legacy;
- более читаемые диаграммы без лишнего визуального шума.

## Sequence style: что есть

### Базовое оформление

- единая типографика;
- выровненные отступы и читаемые подписи;
- `responseMessageBelowArrow`;
- скрытый footbox;
- нейтральная базовая палитра.

### Семантические теги участников

Можно помечать участников через stereotypes:

- `<<p_new>>` — новый компонент;
- `<<p_chg>>` — изменённый компонент;
- `<<p_rm>>` — удаляемый компонент;
- `<<p_legacy>>` — legacy;
- `<<p_cfg>>` — конфиг / policy / rules source;
- `<<p_ext>>` — внешний контур / партнёр.

### Слои

Есть готовые макросы для логической группировки участников:

- `SEQ_LAYER_USER_BEGIN()`
- `SEQ_LAYER_API_BEGIN()`
- `SEQ_LAYER_CORE_BEGIN()`
- `SEQ_LAYER_INT_BEGIN()`
- `SEQ_LAYER_DATA_BEGIN()`
- `SEQ_LAYER_EXT_BEGIN()`
- `SEQ_LAYER_CFG_BEGIN()`
- `SEQ_LAYER_OPS_BEGIN()`
- `SEQ_LAYER_CUSTOM_BEGIN("...")`
- `SEQ_LAYER_END()`

### Макросы сообщений

Есть готовые макросы для стрелок, чтобы не красить их руками:

- sync request;
- async request;
- response;
- статусные варианты для `new / changed / removed / config / legacy`.

### Фрагменты и акценты

Есть макросы для акцентных блоков:

- `info`;
- `warn`;
- `crit`.

Их удобно использовать для:

- retry / timeout;
- degradation / fallback;
- идемпотентности;
- денежных и необратимых операций;
- ограничений и допущений.

### Заголовки и легенды

Есть готовые хелперы для:

- заголовка диаграммы;
- полной легенды;
- сокращённой легенды.

## C4-like style: что есть

### Базовое оформление

- единая типографика;
- ortho-линии;
- нейтральный baseline для context / container / component views;
- аккуратные package / boundary / node styles.

### Стереотипы узлов

Поддерживаются базовые stereotypes:

- `<<Service>>`
- `<<Database>>`
- `<<Broker>>`
- `<<External>>`
- `<<Legacy>>`
- `<<Config>>`
- `<<Anchor>>`

### Границы

Есть готовые boundary stereotypes:

- `<<SolutionBoundary>>`
- `<<DomainBoundary>>`
- `<<ExternalBoundary>>`

И макросы для их открытия:

- `C4_BOUNDARY_SOLUTION_BEGIN("...")`
- `C4_BOUNDARY_DOMAIN_BEGIN("...")`
- `C4_BOUNDARY_EXTERNAL_BEGIN("...")`
- `C4_BOUNDARY_END()`

### Макросы связей

Есть готовые relation helpers:

- sync / async;
- `new / changed / removed / config / legacy`.

Это позволяет:

- одинаково показывать change semantics;
- не размазывать произвольные цвета по диаграмме;
- держать единый стиль между разными авторами.

### Заголовки и легенды

Есть хелперы для:

- заголовка;
- заголовка с подзаголовком;
- легенды статусов.

## Как подключать

### Sequence

```puml
@startuml
!pragma teoz true
!include _style_seq_canonical.puml

SEQ_TITLE("Order creation")
SEQ_LEGEND_FULL_TOP_RIGHT()

SEQ_LAYER_USER_BEGIN()
    actor Client
SEQ_LAYER_END()

SEQ_LAYER_API_BEGIN()
    boundary API <<p_chg>>
SEQ_LAYER_END()

SEQ_LAYER_CORE_BEGIN()
    control OrderService <<p_new>>
SEQ_LAYER_END()

SEQ_REQ_CHG(Client, API, "POST /orders")
SEQ_REQ_NEW(API, OrderService, "createOrder()")
SEQ_RESP_OK(OrderService, API, "orderId")
SEQ_RESP_OK(API, Client, "202 Accepted")
@enduml
```

### C4-like

```puml
@startuml
!include _style_c4_canonical.puml

C4_TITLE_WITH_SUBTITLE("Order flow", "Container view")
C4_LEGEND_STATUS_BOTTOM_RIGHT()

C4_BOUNDARY_SOLUTION_BEGIN("Order solution")
    rectangle API as api <<Service>>
    rectangle Core as core <<Service>>
    database DB as db <<Database>>
C4_BOUNDARY_END()

rectangle Partner as ext <<External>>

C4_SYNC_CHG(api, core, "createOrder()")
C4_SYNC_NEW(core, db, "persist")
C4_ASYNC_NEW(core, ext, "event")
@enduml
```

## Правила использования

- не красить стрелки и элементы руками, если для этого уже есть макрос;
- один уровень абстракции на диаграмму;
- один публичный сценарий или одна операция на один sequence;
- status colors использовать как семантику изменения, а не как украшение;
- проектные расширения делать отдельным style-файлом поверх canonical base.

## Рекомендуемая структура

```text
/docs/styles/_style_seq_canonical.puml
/docs/styles/_style_c4_canonical.puml
```

## Расширение под проект

Если нужен доменный цвет, дополнительные stereotypes или специальные legend items:

- не менять canonical-файл под один проект;
- делать отдельную надстройку, например:

```text
/docs/styles/project/_style_seq_project.puml
/docs/styles/project/_style_c4_project.puml
```

И уже в ней подключать canonical base и добавлять локальные расширения.
