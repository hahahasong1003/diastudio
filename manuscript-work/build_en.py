#!/usr/bin/env python3
"""개편판 영어 원고를 조립한다.

7/15 영어 완성본에서 다섯 장을 걷어내고, 새로 재저작한 다섯 장을 넣고,
부 구성을 9부로 다시 짠다. 보존하는 장은 원본 XML을 그대로 옮겨
서식이 한 톨도 달라지지 않게 한다.
"""
import re, shutil, zipfile, os

SRC = 'source/en_original.docx'
OUT = 'corrected/The-Best-Experience-The-Best-Cafe_EN_rev5_20260823.docx'

FONT = ('<w:rFonts w:ascii="Georgia" w:cs="Georgia" w:eastAsia="Georgia" '
        'w:hAnsi="Georgia"/>')

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def marker(text):
    return ('<w:p><w:pPr><w:spacing w:after="120" w:before="320"/></w:pPr>'
            f'<w:r><w:rPr>{FONT}<w:b/><w:bCs/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def heading(level, text):
    spec = {1: ('200', '300', '32', ''),
            2: ('180', '300', '28', ''),
            3: ('120', '300', '23', '<w:color w:val="1F3864"/>')}[level]
    after, before, sz, color = spec
    return (f'<w:p><w:pPr><w:pStyle w:val="Heading{level}"/>'
            f'<w:spacing w:after="{after}" w:before="{before}"/></w:pPr>'
            f'<w:r><w:rPr>{FONT}<w:b/><w:bCs/>{color}<w:sz w:val="{sz}"/>'
            f'<w:szCs w:val="{sz}"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def body(text):
    return ('<w:p><w:pPr><w:spacing w:after="140" w:line="340"/></w:pPr>'
            f'<w:r><w:rPr>{FONT}<w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def load_new(path):
    """탭으로 나뉜 재저작 원고를 문단 XML 목록으로 바꾼다."""
    out = []
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line:
            continue
        kind, text = line.split('\t', 1)
        out.append({'H2': lambda t: heading(2, t),
                    'H3': lambda t: heading(3, t),
                    'B': body}[kind](text))
    return out

NUM = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
       'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
       'Seventeen', 'Eighteen', 'Nineteen', 'Twenty', 'Twenty-One']

# --- 원본 해체 -------------------------------------------------------------
xml = zipfile.ZipFile(SRC).read('word/document.xml').decode('utf-8')
head, rest = xml.split('<w:body>', 1)
head += '<w:body>'
bodyxml, tail = rest.rsplit('</w:body>', 1)
tail = '</w:body>' + tail

paras = re.findall(r'<w:p\b.*?</w:p>|<w:p/>', bodyxml, re.S)
assert len(paras) == 1081, len(paras)

def ptext(p):
    return ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.S))

MARK = re.compile(r'^(Part|Chapter) [A-Z]')
marks = [i for i, p in enumerate(paras) if MARK.match(ptext(p).strip())]

# 장 이름 -> (표제 문단 index, 본문 끝 index)
chapters = {}
for i in marks:
    if not ptext(paras[i]).startswith('Chapter'):
        continue
    title = ptext(paras[i + 1])
    name = title.split(':')[-1].strip()
    nxt = [m for m in marks if m > i]
    end = (nxt[0] if nxt else len(paras)) - 1
    chapters[name] = (i + 1, end)          # 표제부터 본문 끝까지

parts = {}
for i in marks:
    if not ptext(paras[i]).startswith('Part'):
        continue
    parts[ptext(paras[i + 1])] = (i + 1, i + 2)   # (H1, 도입 문단)

def keep(name):
    a, b = chapters[name]
    return paras[a:b + 1]

# --- 새 원고 ---------------------------------------------------------------
new = {p.split('_')[1].split('.')[0]: load_new('new_en/' + p)
       for p in sorted(os.listdir('new_en')) if p != 'parts.txt'}

pieces = {}
for line in open('new_en/parts.txt', encoding='utf-8'):
    line = line.rstrip('\n')
    if line:
        k, v = line.split('\t', 1)
        pieces[k] = v

# 실로의 마지막 문단은 책 전체를 닫고 있어 장의 맺음으로 다시 쓴다.
silo = keep('Silo')
silo[-1] = body(pieces['SILO'])

# 레인의 피날레가 웨이브와 같은 문장이라 그 장의 이미지로 새로 짓는다.
def repl(block, before, after):
    hit = 0
    for i, p in enumerate(block):
        if before in ptext(p):
            block[i] = p.replace(esc(before), esc(after))
            hit += 1
    assert hit == 1, (before, hit)
    return block

rain = repl(keep('Rain'), 'Admission is a cup of coffee.',
            'The rain is free; the roof over it costs a cup of coffee.')

# 오리엔트는 트래블러로 개명한다. 행선지 안내판에 그 이름의 뜻을 한 줄 붙인다.
traveler = keep('Orient')
traveler = repl(
    traveler,
    'The board updates itself every hour, and people stand in front of it for longer than they mean to.',
    'The board updates itself every hour, and people stand in front of it for longer than they mean to. '
    'At the top of it, in larger letters, is the only word written anywhere on the building: Traveler.')

# 창은 진짜 창이다. 화면이라는 장치를 걷어내고 바깥의 한적한 풍경을 그대로 쓴다.
traveler = repl(
    traveler,
    'The window beside you shows a dark landscape sliding past.',
    'Through the window beside you the old line runs off between the trees, and beyond it the lights of '
    'the town lie low and steady.')
traveler = repl(
    traveler,
    'The window can be a screen. The whistle can be a recording.',
    'The view costs nothing — the old line and the trees and the town were already out there. '
    'The whistle can be a recording.')
for i, para in enumerate(traveler):
    if 'Orient' in ptext(para):
        traveler[i] = para.replace('Orient', 'Traveler')
assert not any('Orient' in ptext(p) for p in traveler)

BOOK = [
    ('Leaving Without Leaving', None, [keep('Altitude'), traveler, keep('Lux')]),
    ('What Water Makes', None, [keep('Wave'), keep('Pool'), rain]),
    ('What the Forest Offers', pieces['P3B'], [keep('Moss'), keep('Birch'), new['tropical']]),
    ('Past the Atmosphere', None, [keep('Orbit'), keep('Mars'), keep('Deep Space')]),
    ('Into the Age of Paper and Ink', None, [keep('Ink'), keep('Post'), keep('Atlas')]),
    (pieces['P6H'], pieces['P6B'], [new['lemon'], new['igloo']]),
    (pieces['P7H'], pieces['P7B'], [keep('Beehive'), new['viking']]),
    ('On the Things We Store', pieces['P8B'], [silo]),
    (pieces['P9H'], pieces['P9B'], [new['pyramid']]),
]

out = paras[0:9]                      # 표제지와 서문
chapter_no = 0
for part_no, (title, intro, chaps) in enumerate(BOOK, 1):
    out.append(marker(f'Part {NUM[part_no]}'))
    if intro is None:                 # 원본의 부를 그대로 옮긴다
        h1, lead = parts[title]
        out.extend([paras[h1], paras[lead]])
    else:
        out.extend([heading(1, title), body(intro)])
    for chap in chaps:
        chapter_no += 1
        out.append(marker(f'Chapter {NUM[chapter_no]}'))
        out.extend(chap)

assert chapter_no == 21, chapter_no

# --- 다시 묶는다 -----------------------------------------------------------
sect = re.search(r'<w:sectPr\b.*?</w:sectPr>', bodyxml, re.S)
newbody = head + ''.join(out) + (sect.group() if sect else '') + tail

os.makedirs('work_en3', exist_ok=True)
with zipfile.ZipFile(SRC) as z:
    z.extractall('work_en3')
with open('work_en3/word/document.xml', 'w', encoding='utf-8') as fh:
    fh.write(newbody)

if os.path.exists(OUT):
    os.remove(OUT)
shutil.make_archive('_tmp_en3', 'zip', 'work_en3')
os.rename('_tmp_en3.zip', OUT)
print(f'{OUT}  문단 {len(out)}개, 장 {chapter_no}개, 부 {len(BOOK)}개')
