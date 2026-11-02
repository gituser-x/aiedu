"""Normalize model formatting without inventing missing question content."""
import hashlib
import re


def rich_text(value):
    if isinstance(value, dict):
        return str(value.get('text') or value.get('content_markdown') or value.get('content') or value.get('value') or '').strip()
    if isinstance(value, list):
        return '\n'.join(filter(None, (rich_text(v) for v in value)))
    return str(value if value is not None else '').strip()


def normalize_options(value):
    if isinstance(value, dict):
        value = [{'label': key, 'text': text} for key, text in value.items()]
    if not isinstance(value, list):
        return []
    result = []
    for i, option in enumerate(value):
        label = chr(65 + i)
        if isinstance(option, dict):
            label = str(option.get('label') or option.get('key') or option.get('id') or label).upper().rstrip('.、) ')
            text = rich_text(option)
        else:
            text = rich_text(option)
            match = re.match(r'^([A-Z])[.、:：)\s]+(.+)$', text, re.S)
            if match:
                label, text = match.groups()
        result.append({'label': label, 'text': text})
    return result


def normalize_generated_content(raw):
    nested = raw.get('content')
    content = dict(nested) if isinstance(nested, dict) else {}
    for key in ('stem', 'options', 'answer', 'analysis', 'material', 'passage', 'sub_questions', 'extensions'):
        if not content.get(key) and raw.get(key) is not None:
            content[key] = raw[key]
    for target, aliases in {'stem': ('question', 'question_text'), 'answer': ('correct_answer',), 'analysis': ('explanation',)}.items():
        if not content.get(target):
            content[target] = next((raw[k] for k in aliases if raw.get(k) is not None), '')
    stem = rich_text(content.get('stem'))
    material = rich_text(content.get('material') or content.get('passage') or raw.get('shared_material'))
    if material:
        content['material'] = material
        extensions = dict(content.get('extensions') or {})
        extensions['material_group'] = hashlib.sha256(material.encode()).hexdigest()[:16]
        content['extensions'] = extensions
        core = re.sub(r'[（(](?:本文为)?原创[）)]', '', material).strip()
        compact = lambda value: re.sub(r'\s+', '', value).translate(str.maketrans('“”‘’', '\"\"\'\''))
        if compact(core or material) not in compact(stem):
            stem = '【阅读材料】\n' + material + '\n\n' + stem
    content['stem'] = {'format': 'markdown', 'text': stem}
    if content.get('options') is not None:
        content['options'] = normalize_options(content['options'])
    if isinstance(content.get('answer'), list):
        content['answer'] = '、'.join(rich_text(v) for v in content['answer'])
    content['schema_version'] = 1
    return content


def subject_generation_rules(subject):
    common = ('所有题目必须自包含，不能依赖未提供的图片、音频或附件。没有实际配图时不得写“如图”“下图”，必须用完整文字描述所有条件。'
              '选择题必须提供A、B、C、D四个非空选项，答案必须对应已有选项，单选只有一个正确选项。'
              '题干、选项、答案、解析全部放入content对象内；不得省略答案和解析。')
    if '语文' in subject:
        return common + '语文阅读题提供完整原创阅读材料和有依据的解析；不伪造真实作品引文。作文提供写作材料、要求与参考范文或评分要点。'
    if '英语' in subject:
        return common + '英语阅读和完形填空提供完整英文原文；空格、小题编号和答案一一对应。写作提供任务和参考范文。语法、拼写及答案须复核。'
    if any(s in subject for s in ('数学', '代数')):
        return common + '数学需独立复算答案，条件充分，变量定义清楚，计算步骤与最终答案一致。公式可以使用合法转义的LaTeX。'
    if subject in ('物理', '化学', '生物'):
        return common + '理科题明确实验条件、数据及单位，物理量量纲一致，化学方程式配平，解析说明推理依据。'
    return common + '史地政等学科明确材料、时间和情境，区分史实与虚构材料，答案有依据，避免存在争议的模糊设问。'
