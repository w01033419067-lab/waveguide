#!/usr/bin/env python3
"""미리보기(preview/index.html)를 본페이지(index.html)로 배포한다.

    python3 _tools/deploy.py          # 배포
    python3 _tools/deploy.py --check  # 쓰지 않고 결과만 확인

하는 일
  1. <!-- PREVIEW-ONLY:START --> ~ <!-- PREVIEW-ONLY:END --> 구간 삭제
     (검토용 배지, noindex, 제목 접두어 등)
  2. preview/ 기준 상대경로 ../assets/ → assets/ 로 변환 (이미지 등)
  3. 남은 흔적이 없는지 검사한 뒤 index.html에 기록
     — data-todo="..." (작성 예정 자리)가 하나라도 있으면 배포하지 않는다

미리보기에 미완성 내용이 있는 동안 본페이지만 고쳐야 할 때(단순 수정)는
이 스크립트를 쓰지 말고 preview/index.html과 index.html에 같은 수정을 각각 한다.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'preview', 'index.html')
DST = os.path.join(ROOT, 'index.html')

START = '<!-- PREVIEW-ONLY:START'
END = '<!-- PREVIEW-ONLY:END -->'
# 구간 안에 또 다른 START가 끼면 매칭하지 않음 — END 하나가 빠졌을 때
# 다음 구간의 END까지 본문을 통째로 지워버리는 사고를 막는다.
BLOCK = re.compile(r'[ \t]*<!-- PREVIEW-ONLY:START(?:(?!<!-- PREVIEW-ONLY:START).)*?<!-- PREVIEW-ONLY:END -->[ \t]*\n?', re.S)


def build(src_text):
    problems = []
    n_start, n_end = src_text.count(START), src_text.count(END)
    if n_start != n_end:
        problems.append('PREVIEW-ONLY 표식 짝이 안 맞음 (START %d개 / END %d개)' % (n_start, n_end))

    out, n_blocks = BLOCK.subn('', src_text)
    out, n_assets = re.subn(r'(["\'(])\.\./assets/', r'\1assets/', out)

    if 'PREVIEW-ONLY' in out:
        problems.append('PREVIEW-ONLY 표식이 남아 있음 (START/END 짝이 안 맞을 수 있음)')
    if re.search(r'(["\'(])\.\./', out):
        problems.append('preview 밖을 가리키는 ../ 경로가 남아 있음')
    if '</html>' not in out:
        problems.append('</html> 이 없음 — 파일이 잘렸을 수 있음')
    missing = sorted({a for a in re.findall(r'["\'(](assets/[^"\')\s]+)', out)
                      if not os.path.exists(os.path.join(ROOT, a))})
    if missing:
        problems.append('본페이지 기준으로 없는 이미지·파일: ' + ', '.join(missing))
    todos = re.findall(r'data-todo="([^"]*)"', out)
    if todos:
        problems.append('작성 예정 자리 %d곳이 남아 있음 — 미완성 내용은 배포하지 않습니다: %s'
                        % (len(todos), ', '.join(todos)))
    return out, n_blocks, n_assets, problems


def main():
    check_only = '--check' in sys.argv
    src = io.open(SRC, encoding='utf-8').read()
    out, n_blocks, n_assets, problems = build(src)

    print('미리보기 → 본페이지')
    print('  검토용 구간 삭제 : %d곳' % n_blocks)
    print('  assets 경로 변환 : %d곳' % n_assets)
    if problems:
        print('\n중단 — 확인 필요:')
        for p in problems:
            print('  ✗ ' + p)
        sys.exit(1)

    old = io.open(DST, encoding='utf-8').read() if os.path.exists(DST) else ''
    if old == out:
        print('\n본페이지와 내용이 같습니다. 바꿀 것이 없습니다.')
        return
    if check_only:
        print('\n(--check) 문제 없음. 실제로 쓰지는 않았습니다.')
        return
    io.open(DST, 'w', encoding='utf-8').write(out)
    print('\n✓ index.html 갱신 (%d → %d 줄)' % (old.count('\n'), out.count('\n')))


if __name__ == '__main__':
    main()
