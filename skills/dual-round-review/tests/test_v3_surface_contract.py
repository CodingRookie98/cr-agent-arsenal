"""dual-round-review V3.0 表面、模板、防回流与体积预算契约测试。

覆盖：
- 模板/参考提示词区块标题与 `check-review-report.py` 常量逐项对齐；
- R1/R2 缺陷与裁决表头跨文档逐字一致（含 R2 三源 7 列表头）；
- `SKILL.md` YAML frontmatter、description 长度与行数/字节数预算；
- 全技能目录围栏配对平衡与退役 `Artifact Review` 关键词全目录防回流哨兵。
"""
import ast
import re
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / 'scripts' / 'check-review-report.py'
FRONTMATTER_RX = re.compile(r'\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)', re.DOTALL)
FENCE_RX = re.compile(r'^\s*(`{3,}|~{3,})')

_R1_TEMPLATES = (
    SKILL_DIR / 'references' / 'round-1-red-team.md',
    SKILL_DIR / 'templates' / 'r1-report-code.md',
)
_R2_TEMPLATES = (
    SKILL_DIR / 'references' / 'round-2-meta-architect.md',
    SKILL_DIR / 'templates' / 'r2-report.md',
)
_R2_SEVEN_COL_SOURCES = (
    SKILL_DIR / 'templates' / 'r2-report.md',
    SKILL_DIR / 'references' / 'round-2-meta-architect.md',
    SKILL_DIR / 'references' / 'verdict-rubric.md',
)
EXPECTED_R2_SEVEN_COL_HEADER = (
    '| 稳定 ID (沿用 R1) | 检查点 / 文件位置 | 原始 R1 评级 | '
    '变更归属 (本次引入/历史既有) | 终审裁决 | 最终定性分析与裁决理由 | 处置要求 |'
)
_RETIRED_ARTIFACT_KEYWORDS = (
    'artifact-contract',
    'round-1-artifact-red-team',
    'verdict-rubric-artifact',
    'r1-report-artifact',
    'Review Schema: artifact',
)


def _checker_sections() -> tuple[list[str], list[str]]:
    """从门禁 Python 实现中解析必需区块常量（AST 字面量序列提取）。"""
    tree = ast.parse(SCRIPT.read_text(encoding='utf-8'))
    found: dict[str, list[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in ('R1_SECTIONS', 'R2_SECTIONS'):
                found[target.id] = list(ast.literal_eval(node.value))
    return found.get('R1_SECTIONS', []), found.get('R2_SECTIONS', [])


def _template_headings(path: Path) -> list[str]:
    body = path.read_text(encoding='utf-8').split('## Output Format')[-1].split('## 输出格式')[-1]
    return re.findall(r'^## \d+\. .+$', body, re.M)


def _parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RX.match(text)
    assert m, 'SKILL.md 缺少合法 YAML frontmatter'
    body = m.group(1)
    if yaml is not None:
        parsed = yaml.safe_load(body)
        assert isinstance(parsed, dict), 'frontmatter 顶层必须为 mapping'
        return parsed
    meta, lines, i = {}, body.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.lstrip().startswith('#'):
            i += 1
            continue
        key, sep, raw = ln.partition(':')
        assert sep, f'非法 YAML 行: {ln!r}'
        v = raw.strip()
        if v in ('>', '|', '>-', '|-'):
            blk, i = [], i + 1
            while i < len(lines) and (lines[i].startswith((' ', '\t')) or not lines[i].strip()):
                blk.append(lines[i].strip())
                i += 1
            meta[key.strip()] = ' '.join(x for x in blk if x)
            continue
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        else:
            assert not re.search(r':(?:\s|$)', v), f'{key} 含未加引号的 ": "'
        meta[key.strip()], i = v, i + 1
    return meta


def _fences_balanced(text: str) -> bool:
    fence = ''
    for line in text.splitlines():
        m = FENCE_RX.match(line)
        if not m:
            continue
        tok, rest = m.group(1), line[m.end():]
        if not fence and (tok[0] == '~' or '`' not in rest):
            fence = tok
        elif fence and tok[0] == fence[0] and len(tok) >= len(fence) and not rest.strip():
            fence = ''
    return not fence


def test_template_headings_match_checker_constants():
    """模板与参考提示词的输出区块标题必须逐项匹配门禁必需常量——防止独立漂移。"""
    r1_secs, r2_secs = _checker_sections()
    assert r1_secs and r2_secs, '未能从门禁脚本解析出必需区块常量'
    for path in _R1_TEMPLATES:
        hs = _template_headings(path)
        assert len(hs) == len(r1_secs), f'{path.name} R1 区块数不匹配: {hs}'
        for h, expected in zip(hs, r1_secs):
            assert h.startswith(expected), f'{path.name} R1 标题不匹配: {h} != {expected}'
    for path in _R2_TEMPLATES:
        hs = _template_headings(path)
        assert len(hs) == len(r2_secs), f'{path.name} R2 区块数不匹配: {hs}'
        for h, expected in zip(hs, r2_secs):
            assert h.startswith(expected), f'{path.name} R2 标题不匹配: {h} != {expected}'


def test_r1_template_and_reference_defect_headers_aligned():
    """R1 模板与参考提示词的缺陷清单表头须均含「稳定 ID」与「是否由当前 Diff 引入」。"""
    for path in _R1_TEMPLATES:
        body = path.read_text(encoding='utf-8').split('## 4. 潜在缺陷清单', 1)[-1]
        header = next((ln for ln in body.splitlines() if ln.lstrip().startswith('|') and '稳定 ID' in ln), '')
        assert header, f'{path.name} 缺少缺陷清单表头'
        assert '是否由当前 Diff 引入' in header, f'{path.name} 缺陷表头缺少「是否由当前 Diff 引入」: {header}'


def test_r2_three_sources_seven_col_header_aligned():
    """R2 模板、R2 参考提示词与裁决细则的 7 列裁决明细表头必须逐字一致。"""
    for path in _R2_SEVEN_COL_SOURCES:
        lines = [ln.strip() for ln in path.read_text(encoding='utf-8').splitlines()]
        assert EXPECTED_R2_SEVEN_COL_HEADER in lines, (
            f'{path.relative_to(SKILL_DIR)} 缺少统一 7 列 R2 表头: {EXPECTED_R2_SEVEN_COL_HEADER}'
        )


def test_v3_skill_surface_frontmatter_fences_and_no_artifact_backflow():
    """V3.0 表面与防回流哨兵：frontmatter 与体积预算、围栏配对及全目录退役关键词扫描。"""
    skill_text = (SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8')
    assert len(skill_text.splitlines()) <= 130, f'SKILL.md 行数超 130 预算: {len(skill_text.splitlines())}'
    assert len(skill_text.encode('utf-8')) <= 12 * 1024, (
        f'SKILL.md 字节数超 12 KB 预算: {len(skill_text.encode("utf-8"))}'
    )
    meta = _parse_frontmatter(skill_text)
    assert meta.get('name') == SKILL_DIR.name == 'dual-round-review'
    assert str(meta.get('license', '')).strip().upper() == 'MIT'
    desc = meta.get('description', '')
    assert isinstance(desc, str) and desc.strip() and len(desc) <= 500, f'description 非法或超 500 字符: {len(desc)}'
    for path in sorted(p for p in SKILL_DIR.rglob('*.md') if '__pycache__' not in str(p)):
        assert _fences_balanced(path.read_text(encoding='utf-8')), f'围栏未闭合: {path.relative_to(SKILL_DIR)}'

    scanned = [
        p for p in sorted(SKILL_DIR.rglob('*'))
        if p.is_file() and not set(p.relative_to(SKILL_DIR).parts).intersection({'tests', '__pycache__'})
    ]
    top_entries = {p.relative_to(SKILL_DIR).parts[0] for p in scanned}
    assert {'SKILL.md', 'references', 'templates', 'scripts', 'examples'} <= top_entries
    for path in scanned:
        text = path.read_text(encoding='utf-8')
        for retired in _RETIRED_ARTIFACT_KEYWORDS:
            assert retired not in text, f'{path.relative_to(SKILL_DIR)} 含已退役关键词: {retired}'
