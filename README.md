# 语文考试试卷蒸馏

这个项目用于把语文试卷能力蒸馏结果整理成 Markdown 复习文档。

它的目标不是按题号复盘，而是把题目背后的可迁移能力、常见问法、答题路径和易错点抽出来，方便学生按“考点 / 技能”复习。

## 功能

- 将 distilled skills 渲染成考点复盘 Markdown
- 将 general skills 渲染成通用能力复习 Markdown
- 支持 brief / normal / detailed 三种渲染模式
- 支持按技能类型自动切换简略或详细展示
- 支持保存为 `.md` 文件，后续可转 PDF、HTML 或导入笔记软件

## 输入格式

### Distilled Skills

适合单份试卷或一批题目蒸馏后的技能结果。

示例：

```json
[
  {
    "skill_type": "句子作用分析",
    "core_ability": "考查学生理解句子在内容、结构和表达效果中的作用。",
    "common_question_forms": [
      "某句话在文中有什么作用？",
      "请分析画线句子的表达效果。"
    ],
    "answering_framework": "内容作用 + 结构作用 + 情感 / 主旨作用",
    "step_by_step_method": [
      "审清题干，确定分析对象。",
      "回到原文，结合上下文理解句意。",
      "从内容、结构、情感三个角度组织答案。"
    ],
    "answer_templates": [
      "这句话写出了……，表现了……，为下文……作铺垫。"
    ],
    "high_score_expressions": [
      "推动情节发展",
      "照应标题",
      "突出人物形象"
    ],
    "common_mistakes": [
      "只解释句子表层意思，没有分析作用。",
      "脱离文本空套术语。"
    ]
  }
]
```

也支持对象形式：

```json
{
  "句子作用分析": {
    "core_ability": "考查学生理解句子在内容、结构和表达效果中的作用。"
  }
}
```

### General Skills

适合多份试卷汇总后形成的通用能力模型。

示例：

```json
{
  "skills": [
    {
      "skill_id": "memory_context_validation",
      "skill_name": "古诗文名句准确记忆与语境验证能力",
      "description": "能够准确回忆指定篇目中的名句，并结合语境判断填写内容。",
      "transferable_ability": "该能力可迁移至古诗文默写、语言积累和文学常识类任务。",
      "prerequisites": [
        "熟悉课内必背篇目",
        "掌握常见易错字",
        "理解句子基本语境"
      ],
      "subskills": [
        {
          "name": "精确记忆",
          "description": "能够准确回忆指定篇目中的名句，包括字词顺序和标点。",
          "observable_behavior": "学生能不看原文完整默写句子。"
        }
      ],
      "exam_application": [
        {
          "source_skill_type": "名句默写与诗文积累",
          "common_question_forms": [
            "按要求填空。",
            "补写出下列句子中的空缺部分。"
          ],
          "answering_patterns": [
            "审题定位→回忆原文→逐字核对→规范书写→检查语境"
          ]
        }
      ]
    }
  ]
}
```

## Markdown 渲染

核心渲染逻辑在：

```text
skill_renderer.py
```

主要函数：

```python
render_skill_markdown(skills, mode="normal")
save_skill_markdown(skills, output_path, mode="normal")
```

示例：

```python
import json
from skill_renderer import save_skill_markdown

with open("data/general_skills/sample.json", "r", encoding="utf-8") as f:
    skills = json.load(f)

save_skill_markdown(
    skills,
    "data/study_guides/sample_general.md",
    mode="normal",
)
```

如果项目中已经接入 CLI，可以使用类似命令：

```bash
ced render data/general_skills/sample.json data/study_guides/sample_general.md
```

## 渲染模式

支持三种模式：

```text
brief
normal
detailed
```

### brief

适合基础识记类考点，输出更短：

- 考什么
- 怎么做
- 易错点

### normal

默认模式，适合大多数技能：

- 这类题在考什么
- 常见问法
- 答题框架
- 解题步骤
- 答题模板
- 高分表达
- 易错点

### detailed

适合阅读理解、作文、文言文、古诗赏析等复杂技能，会尽量输出完整信息，并包含例题分析。

## 自动简略 / 详细分类

`skill_renderer.py` 内置两组默认分类：

```python
DEFAULT_BRIEF_SKILL_TYPES
DEFAULT_DETAILED_SKILL_TYPES
```

例如：

- 名句默写与诗文积累：默认 brief
- 字音字形与词语运用：默认 brief
- 句子作用分析：默认 detailed
- 人物形象分析：默认 detailed
- 古诗表现手法赏析：默认 detailed

也可以在调用时覆盖：

```python
render_skill_markdown(
    skills,
    mode="normal",
    brief_types={"文学文化常识"},
    detailed_types={"句子作用分析", "语言赏析"},
)
```

## 字段兼容

### 技能名称字段

渲染器会依次读取：

```text
skill_type
skill_name
type
name
question_type
skill_id
```

### 核心能力字段

渲染器会依次读取：

```text
core_ability
transferable_ability
what_it_tests
exam_focus
description
summary
```

### 常见问法字段

```text
common_question_forms
common_questions
question_forms
常见问法
```

### 解题步骤字段

```text
step_by_step_method
steps
method_steps
solving_steps
解题步骤
```

### 答题框架字段

```text
answering_framework
answer_framework
framework
template
答题框架
```

### 易错点字段

```text
common_mistakes
mistakes
pitfalls
易错点
```

## 常见问题

### 生成的 Markdown 只有大标题

通常是输入结构不匹配。

如果输入是 general skills，需要保证外层结构是：

```json
{
  "skills": []
}
```

并且 `_normalize_skills()` 支持读取 `skills` 字段。

### 子能力显示成 Python dict

如果 Markdown 中出现类似内容：

```text
{'name': '精确记忆', 'description': '...', 'observable_behavior': '...'}
```

说明嵌套对象被直接转成了字符串。

应使用 general skill 专用 formatter，例如：

- `_subskill_lines()`
- `_exam_application_lines()`

不要直接用 `_bullet_lines()` 渲染 dict list。

### 想减少 token 消耗

建议把 general skills 生成作为显式选项，而不是 pipeline 默认步骤。

例如只在用户传入：

```bash
--general-skills
```

时才运行通用能力汇总。

这样普通试卷蒸馏不会额外调用大模型生成全局能力模型。

## 推荐输出目录

```text
data/
  distilled_skills/
  general_skills/
  study_guides/
```

示例：

```bash
data/general_skills/sample.json
data/study_guides/sample_general.md
```

## 开发建议

- renderer 只负责格式化，不负责调用模型
- CLI 负责读取 JSON、调用 renderer、写入文件
- pipeline 负责蒸馏流程编排
- general skill 和 distilled skill 最好保持不同 schema
- 对嵌套 dict 使用专用 formatter，避免 Markdown 中出现原始 Python dict