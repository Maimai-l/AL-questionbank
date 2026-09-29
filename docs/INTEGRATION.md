# 题库数据库与接口对接

本文以 `data/caie.db` 当前结构为准。题目内容是只读主数据；学习进度是用户数据。

## 文件与约定

| 项目 | 位置 / 约定 |
| --- | --- |
| SQLite 主库 | `data/caie.db` |
| 题目主键 | `questions.id`，全局唯一字符串；接口和 LLM JSON 一律使用它 |
| 题图 | `data/<questions.image>` |
| 教材章节文件 | `chapters.path`，相对项目根目录 |
| 时间 | ISO 8601 UTC，例如 `2026-08-18T10:30:00Z` |
| JSON 文本列 | `parts`、`marks_parts`、`topic_all`、`mark_codes`、`qp_pages`、`options`；读取后解析 JSON |

题库目前共 4,844 题：9231、9618、9709、BMAT、TMUA、TSA。不要把导出 ZIP 当作本地题库的数据源：ZIP 是可分发子集，`caie.db` 是全集。

## 现有数据表

### `questions`（只读）

一行是一道题。常用字段：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `id` | TEXT PK | 全局题目 ID，例如 `9709_m21_12_q01`、`TSA-2023-S1-q50` |
| `syllabus` | TEXT | `9709` / `9231` / `9618` / `TMUA` / `TSA` / `BMAT` |
| `component`, `component_name` | TEXT | 试卷组件及显示名 |
| `paper`, `variant`, `year`, `month`, `session`, `series` | TEXT / INTEGER | 试卷来源 |
| `q`, `parts`, `marks`, `marks_parts` | INTEGER / TEXT | 题号、小问、分值 |
| `topic`, `topic_name`, `subtopic`, `subtopic_name` | TEXT | 知识点标签；可能为空 |
| `qtype`, `options`, `answer` | TEXT | 题型、选择项、答案；主要适用于 admission MCQ |
| `image` | TEXT | 主题图相对 `data/` 的路径；可能为空 |
| `question_text`, `question_latex` | TEXT | OCR 文本 / 富文本；可能为空或含内嵌图片引用 |
| `ms_text`, `ms_latex` | TEXT | 评分标准文本 |
| `q_quality`, `ms_quality` | TEXT | OCR 质量：`ok`、`degraded`、`severe`、`garbled`、`missing` |

读取题目：

```sql
SELECT id, syllabus, paper, session, q, marks,
       topic, topic_name, question_text, question_latex,
       ms_text, ms_latex, image
FROM questions
WHERE id = :question_id;
```

按题图显示时，将 `image` 拼到 `data/` 下。题干 Markdown/HTML 中还可能有 `img9709/`、`img9231/`、`img9618/`、`img_adm/` 或 `img_tara/` 开头的内嵌图片路径，也以该 assets 目录为根。

### `chapters`（只读）

教材章节索引。`id` 是章节 ID；`path` 指向 Markdown；`topic` / `subtopic` 可用来匹配题目。`coverage` 为已匹配题覆盖率，并非学习进度。

### `attempts`（已存在，可写）

做题事件日志，**只增不改**。已有字段：

```text
id INTEGER PRIMARY KEY
question_id TEXT NOT NULL
grade TEXT NOT NULL CHECK (grade IN ('good','ok','bad'))
at TEXT NOT NULL
seconds INTEGER
note TEXT
source TEXT
```

含义：`good`=独立做对；`ok`=部分正确/困难后完成；`bad`=未能完成。`attempts` 没有外键约束，因此写入前接口必须确认 `questions.id` 存在。现有唯一索引会忽略同一 `question_id + at + grade + source` 的完全重复事件。

记录一次作答：

```sql
INSERT OR IGNORE INTO attempts (question_id, grade, at, seconds, note, source)
VALUES (:question_id, :grade, :at, :seconds, :note, :source);
```

判断“是否做过”不需要新字段：

```sql
SELECT EXISTS(
  SELECT 1 FROM attempts WHERE question_id = :question_id
) AS attempted;
```

取得当前结果时，按时间和自增 ID 取最后一次；不能用最早一次：

```sql
SELECT grade, at, seconds, note, source
FROM attempts
WHERE question_id = :question_id
ORDER BY at DESC, id DESC
LIMIT 1;
```

批量题目列表同时带状态：

```sql
WITH latest AS (
  SELECT a.*, ROW_NUMBER() OVER (
    PARTITION BY question_id ORDER BY at DESC, id DESC
  ) AS rn
  FROM attempts a
)
SELECT q.id, q.paper, q.q, q.topic_name, q.image,
       l.grade AS latest_grade, l.at AS last_attempted_at,
       l.seconds AS last_seconds,
       EXISTS(SELECT 1 FROM attempts a WHERE a.question_id = q.id) AS attempted
FROM questions q
LEFT JOIN latest l ON l.question_id = q.id AND l.rn = 1
WHERE q.syllabus = :syllabus
ORDER BY q.year, q.month, q.paper, q.q;
```

## 建议的用户状态扩展

`attempts` 负责历史；不要在它上面覆盖旧记录。若界面需要手动标记、收藏、笔记、复习日期等当前状态，新增 `question_state`。以下是**建议迁移**，尚未自动应用：

```sql
CREATE TABLE question_state (
  profile_id TEXT NOT NULL DEFAULT 'local',
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'new'
    CHECK (status IN ('new', 'in_progress', 'done', 'review')),
  starred INTEGER NOT NULL DEFAULT 0 CHECK (starred IN (0, 1)),
  note TEXT,
  completed_at TEXT,
  next_review_at TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (profile_id, question_id)
);

CREATE INDEX question_state_review
  ON question_state(profile_id, next_review_at);
CREATE INDEX question_state_status
  ON question_state(profile_id, status);
```

推荐规则：写入 `good` 作答事件时，客户端可将 `status` 设为 `done`；写入 `bad` 时可设为 `review`。这是界面策略，不应修改历史 `attempts`。单机应用保持 `profile_id='local'`；多用户时传入稳定用户 ID。

状态 upsert：

```sql
INSERT INTO question_state
  (profile_id, question_id, status, starred, note, completed_at, next_review_at, updated_at)
VALUES
  (:profile_id, :question_id, :status, :starred, :note,
   :completed_at, :next_review_at, :updated_at)
ON CONFLICT(profile_id, question_id) DO UPDATE SET
  status = excluded.status,
  starred = excluded.starred,
  note = excluded.note,
  completed_at = excluded.completed_at,
  next_review_at = excluded.next_review_at,
  updated_at = excluded.updated_at;
```

## 推荐接口契约

以下是给本地 Python 服务或其他后端的最小 REST 契约；路径只是建议，不代表现有服务已经全部实现。

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/api/questions/:id` | 取一题及其当前状态 |
| `GET` | `/api/questions?syllabus=9709&topic=1.2` | 筛题；支持 `paper`、`qtype`、`limit`、`offset` |
| `POST` | `/api/attempts` | 追加一次作答事件 |
| `GET` | `/api/questions/:id/attempts` | 某题历史作答，按时间倒序 |
| `PUT` | `/api/questions/:id/state` | 写入/覆盖当前用户状态 |
| `GET` | `/api/review?before=<ISO-8601>` | 获取到期复习题 |
| `GET` | `/api/images?path=<assets-relative-path>` | 在浏览器中安全提供题图 |

`POST /api/attempts` 请求：

```json
{
  "question_id": "9709_m21_12_q01",
  "grade": "good",
  "at": "2026-08-18T10:30:00Z",
  "seconds": 245,
  "note": "展开式系数相乘时漏项",
  "source": "practice"
}
```

成功响应：

```json
{
  "attempt_id": 42,
  "question_id": "9709_m21_12_q01",
  "attempted": true,
  "latest_grade": "good"
}
```

`PUT /api/questions/:id/state` 请求：

```json
{
  "profile_id": "local",
  "status": "review",
  "starred": false,
  "note": "二项展开复习",
  "next_review_at": "2026-08-25T00:00:00Z"
}
```

## LLM 题组 JSON 与本地题库

导出 ZIP 内的 `index.json` 用题目 ID 标识题目。LLM 只需返回：

```json
{
  "schema": "alevel-question-set/v1",
  "title": "练习题组",
  "items": [
    {
      "archive_id": "9709_p1_question_bank",
      "question_ids": ["9709_m21_12_q01", "9709_m21_12_q06"]
    }
  ]
}
```

本地端按 `question_ids` 查询 `questions.id`；`archive_id` 用于追踪 LLM 使用了哪个导出包，不可作为本地查询范围，也不应读取 ZIP。

## 实施边界

- 用参数化 SQL；禁止把筛选文本直接拼进 SQL。
- `question_id` 先查存在再写 `attempts` / `question_state`。
- SQLite 写入使用短事务；浏览器不直接打开数据库，交由本地后端。
- 题图路径必须限制在 `data/` 及其允许的子目录内，拒绝 `..`、绝对路径和任意文件路径。
- 备份时将 `caie.db` 及其 SQLite sidecar 文件（若有 `-wal`、`-shm`）作为同一组处理。
