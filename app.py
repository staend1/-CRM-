from flask import Flask, render_template, request, jsonify
from itertools import combinations
from collections import defaultdict
from fuzzywuzzy import fuzz
from korean_romanizer.romanizer import Romanizer
import re

app = Flask(__name__)

def parse_input(text):
    """
    입력 텍스트를 개별 항목으로 파싱
    엑셀/구글시트에서 셀 내부 줄바꿈이 있는 경우 큰따옴표로 감싸져 오는데,
    이를 처리하여 하나의 항목으로 인식
    """
    if not text:
        return set()

    items = []
    current_item = ""
    in_quotes = False

    for char in text:
        if char == '"':
            in_quotes = not in_quotes
        elif char == '\n':
            if in_quotes:
                # 큰따옴표 안의 줄바꿈은 공백으로 변환
                current_item += ' '
            else:
                # 큰따옴표 밖의 줄바꿈은 항목 구분자
                if current_item.strip():
                    items.append(current_item.strip())
                current_item = ""
        else:
            current_item += char

    # 마지막 항목 추가
    if current_item.strip():
        items.append(current_item.strip())

    return set(items)

def find_similar_items(item, candidates, threshold=75):
    """
    주어진 항목과 유사한 후보들을 찾아 반환

    Args:
        item: 비교할 항목
        candidates: 후보 항목들의 set
        threshold: 최소 유사도 (기본값 75%)

    Returns:
        유사 항목 리스트 (점수 높은 순)
    """
    suggestions = []

    for candidate in candidates:
        # 여러 방법으로 유사도 측정
        ratio1 = fuzz.ratio(item, candidate)
        ratio2 = fuzz.partial_ratio(item, candidate)
        ratio3 = fuzz.token_sort_ratio(item, candidate)

        # 가장 높은 점수 사용
        best_score = max(ratio1, ratio2, ratio3)

        if best_score >= threshold:
            suggestions.append({
                'text': candidate,
                'score': best_score
            })

    # 점수 높은 순으로 정렬
    suggestions.sort(key=lambda x: x['score'], reverse=True)

    # 상위 3개만 반환
    return suggestions[:3]

def analyze_groups(groups_data):
    """
    여러 그룹 간의 포함관계를 분석

    Args:
        groups_data: {group_name: set_of_items} 형태의 딕셔너리

    Returns:
        분석 결과 딕셔너리
    """
    if not groups_data:
        return {}

    group_names = list(groups_data.keys())
    num_groups = len(group_names)

    result = {
        'group_names': group_names,
        'group_sizes': {name: len(items) for name, items in groups_data.items()},
        'intersections': {},  # 교집합 정보
        'unique_items': {},   # 각 그룹에만 있는 고유 항목
        'combinations': {},   # 특정 조합에만 속한 항목들
        'coverage_matrix': {},  # 그룹 간 커버리지 매트릭스
    }

    # 1. 모든 조합의 교집합 계산
    for r in range(1, num_groups + 1):
        for combo in combinations(group_names, r):
            combo_key = ' ∩ '.join(combo)

            # 해당 조합에 속한 그룹들의 교집합
            intersection = groups_data[combo[0]].copy()
            for group_name in combo[1:]:
                intersection &= groups_data[group_name]

            # 다른 그룹에는 없는 항목만 필터링 (정확한 조합)
            if r < num_groups:
                other_groups = [g for g in group_names if g not in combo]
                for other_group in other_groups:
                    intersection -= groups_data[other_group]

            if intersection:
                result['combinations'][combo_key] = {
                    'count': len(intersection),
                    'items': sorted(list(intersection))
                }

    # 2. 각 그룹 쌍의 교집합 (2개 그룹씩)
    for i, group1 in enumerate(group_names):
        for group2 in group_names[i+1:]:
            key = f"{group1} ∩ {group2}"
            intersection = groups_data[group1] & groups_data[group2]
            result['intersections'][key] = {
                'count': len(intersection),
                'items': sorted(list(intersection))
            }

    # 3. 각 그룹에만 있는 고유 항목
    for group_name in group_names:
        unique = groups_data[group_name].copy()
        for other_group in group_names:
            if other_group != group_name:
                unique -= groups_data[other_group]

        result['unique_items'][group_name] = {
            'count': len(unique),
            'items': sorted(list(unique))
        }

    # 4. 커버리지 매트릭스 (그룹1의 항목이 그룹2에 얼마나 포함되는지)
    for group1 in group_names:
        for group2 in group_names:
            if group1 != group2:
                key = f"{group1}→{group2}"
                coverage = groups_data[group1] & groups_data[group2]
                total = len(groups_data[group1])
                percentage = (len(coverage) / total * 100) if total > 0 else 0

                missing_items = groups_data[group1] - groups_data[group2]

                # 각 missing 항목에 대해 유사 항목 찾기
                missing_with_suggestions = []
                for item in sorted(list(missing_items)):
                    similar = find_similar_items(item, groups_data[group2])
                    missing_with_suggestions.append({
                        'item': item,
                        'suggestions': similar
                    })

                result['coverage_matrix'][key] = {
                    'covered': len(coverage),
                    'total': total,
                    'percentage': round(percentage, 2),
                    'missing': missing_with_suggestions
                }

    return result

def is_hangul(text):
    """한글이 포함되어 있는지 확인"""
    return bool(re.search('[가-힣]', text))

def calculate_similarity_with_romanization(text1, text2, threshold=75):
    """
    두 텍스트의 유사도를 계산 (로마자 변환 포함)

    Returns:
        best_score (int): 0-100 사이의 점수
    """
    # 1. 기본 fuzzy matching
    ratio1 = fuzz.ratio(text1, text2)
    ratio2 = fuzz.partial_ratio(text1, text2)
    ratio3 = fuzz.token_sort_ratio(text1, text2)
    best_score = max(ratio1, ratio2, ratio3)

    # 이미 threshold 넘으면 로마자 변환 불필요
    if best_score >= threshold:
        return best_score

    # 2. 로마자 변환 후 비교 (한글과 영문이 섞인 경우)
    # 한글 포함 여부 확인
    has_hangul_1 = is_hangul(text1)
    has_hangul_2 = is_hangul(text2)

    # 둘 중 하나만 한글이면 로마자 변환해서 비교
    if has_hangul_1 != has_hangul_2:
        try:
            if has_hangul_1:
                # text1이 한글이면 로마자로 변환
                romanized1 = Romanizer(text1).romanize().lower()
                rom_ratio1 = fuzz.ratio(romanized1, text2.lower())
                rom_ratio2 = fuzz.partial_ratio(romanized1, text2.lower())
                rom_ratio3 = fuzz.token_sort_ratio(romanized1, text2.lower())
                rom_score = max(rom_ratio1, rom_ratio2, rom_ratio3)
                best_score = max(best_score, rom_score)
            else:
                # text2가 한글이면 로마자로 변환
                romanized2 = Romanizer(text2).romanize().lower()
                rom_ratio1 = fuzz.ratio(text1.lower(), romanized2)
                rom_ratio2 = fuzz.partial_ratio(text1.lower(), romanized2)
                rom_ratio3 = fuzz.token_sort_ratio(text1.lower(), romanized2)
                rom_score = max(rom_ratio1, rom_ratio2, rom_ratio3)
                best_score = max(best_score, rom_score)
        except Exception as e:
            # 로마자 변환 실패 시 기본 점수 사용
            pass

    return best_score

def find_all_similar_groups(groups_data, threshold=75):
    """
    모든 시트의 모든 항목을 분석하여 유사한 것끼리 그룹화

    Returns:
        [
            {
                'items': [
                    {'text': '건국대학교', 'groups': ['그룹1', '그룹2']},
                    {'text': '건국대학교 연구실', 'groups': ['그룹2']}
                ],
                'representative': '건국대학교'  # 가장 많이 등장하는 항목
            }
        ]
    """
    # 모든 항목 수집 (중복 포함, 어느 그룹에서 왔는지 기록)
    all_items_with_source = []
    for group_name, items in groups_data.items():
        for item in items:
            all_items_with_source.append({
                'text': item,
                'group': group_name
            })

    # 유사도 기반 그룹화
    groups = []
    processed = set()

    for i, item1 in enumerate(all_items_with_source):
        if item1['text'] in processed:
            continue

        # 새 그룹 시작
        group = {
            'items': {}  # text -> [groups]
        }
        group['items'][item1['text']] = [item1['group']]
        processed.add(item1['text'])

        # 유사한 항목 찾기
        for j, item2 in enumerate(all_items_with_source):
            if i >= j or item2['text'] in processed:
                continue

            # 유사도 계산 (로마자 변환 포함)
            best_score = calculate_similarity_with_romanization(item1['text'], item2['text'], threshold)

            if best_score >= threshold:
                if item2['text'] not in group['items']:
                    group['items'][item2['text']] = []
                group['items'][item2['text']].append(item2['group'])
                processed.add(item2['text'])

        # 그룹에 2개 이상 항목이 있을 때만 추가
        if len(group['items']) > 1:
            # 가장 많이 등장하는 항목을 대표로 선택
            item_counts = {}
            for text, source_groups in group['items'].items():
                item_counts[text] = len(source_groups)

            representative = max(item_counts.items(), key=lambda x: (x[1], len(x[0])))[0]
            group['representative'] = representative

            # 리스트 형태로 변환
            group['items_list'] = [
                {'text': text, 'groups': list(set(grps)), 'count': len(set(grps))}
                for text, grps in group['items'].items()
            ]
            group['items_list'].sort(key=lambda x: (-x['count'], x['text']))

            groups.append(group)

    return groups

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        num_groups = data.get('num_groups', 2)

        # 각 그룹의 데이터 파싱
        groups_data = {}
        for i in range(num_groups):
            group_name = data.get(f'group_{i}_name', f'그룹 {i+1}')
            group_text = data.get(f'group_{i}_data', '')
            groups_data[group_name] = parse_input(group_text)

        # 빈 그룹 제거
        groups_data = {k: v for k, v in groups_data.items() if v}

        if not groups_data:
            return jsonify({'error': '최소 1개 그룹에 데이터를 입력해주세요.'}), 400

        # 분석 실행
        analysis_result = analyze_groups(groups_data)

        # 유사 항목 그룹 분석 추가
        similar_groups = find_all_similar_groups(groups_data)
        analysis_result['similar_groups'] = similar_groups

        return jsonify(analysis_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
