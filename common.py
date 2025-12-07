import json
import os
import time

from fuzzywuzzy import fuzz
import re

import jsonschema 

def load_citation_info(paper_id, citation_id):
    with open(f"{paper_id}/Citation_{citation_id}.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_citation_info(paper_id, citation_id, citation_info):
    with open(f"{paper_id}/Citation_{citation_id}.json", "w", encoding="utf-8") as f:
        json.dump(citation_info, f, ensure_ascii=False, indent=4)

            
def loadPaperInfo(paper_id, info_file_path=None):
    if info_file_path is None:
        info_file_path = os.path.join(paper_id, "info.json")

    with open(info_file_path, 'r', encoding='utf-8') as file:
        info_data = json.load(file)

    scholar_id = info_data.get("ScholarID")
    authors = info_data.get("Authors")
    approachName = info_data.get("ApproachName")
    title = info_data.get("Title")
    venue = info_data.get("Venue")
    year = info_data.get("Year")
    class PaperInfo:
        def __init__(self, scholar_id, authors, approach_name, title, venue, year):
            self.scholar_id = scholar_id
            self.authors = authors
            self.approach_name = approach_name
            self.title = title
            self.venue = venue
            self.year = year

        def __repr__(self):
            return (f"PaperInfo(scholar_id={self.scholar_id}, authors={self.authors}, "
                f"approach_name={self.approach_name}, title={self.title}, "
                f"venue={self.venue}, year={self.year})")

        def citation(self):
            return f"{', '.join(self.authors)}. {self.title}. {self.venue}. {self.year}."

    return PaperInfo(scholar_id, authors, approachName, title, venue, year)


def extract_references(title, paper_text):
    """
    从给定的论文文本中提取参考文献部分，并找到与给定标题最匹配的参考文献，并返回参考文献的编号
    参数:
        title (str): 要匹配的引用标题。
        paper_text (str): 论文的全文文本，从中提取参考文献。
    返回:
        list: 包含最佳匹配参考文献及其编号的列表（如果找到）。如果没有找到参考文献部分或匹配的参考文献，则返回空列表。
    该函数执行以下步骤:
    1. 使用常见的参考文献部分标题识别参考文献部分的开始。
    2. 使用滑动窗口方法在参考文献部分中搜索与给定标题最匹配的参考文献。
    3. 提取与最佳匹配参考文献相关的参考文献编号（如果有）。
    """
    # 定义参考文献部分的常见标题
    reference_titles = ["References", "Bibliography", "Works Cited", "参考文献"]

    # 使用正则表达式查找参考文献部分的开始位置
    reference_start = None
    for rt in reference_titles:
        matches = list(re.finditer(rf"^\s*{rt}\s*$", paper_text, re.IGNORECASE | re.MULTILINE))
        match = matches[0] if matches else None
        if match:
            reference_start = match.start()
            break

    if reference_start is None:
        print("No references section found.")
        reference_start = 0

    # 根据title的长度开启滑动窗口，在references_text中查找和title最相似的子段
    window_size = len(title)

    max_similarity = 0
    match_position = -1

    for i in range(reference_start, len(paper_text) - window_size + 1):
        window_text = paper_text[i:i + window_size]
        similarity = fuzz.ratio(title.lower(), window_text.lower())

        if similarity > max_similarity:
            max_similarity = similarity
            match_position = i

    matched_reference = paper_text[match_position:match_position + window_size]
    # print(f"Best match with similarity {max_similarity}: {matched_reference}")
    
    # 接下来分析论文中引用格式
    analysis_length = 1000  # 用来分析的片段的长度  
    expected_consecutive_numbers = 3 # 片段中期望引用的数量
    
    # 提取被分析的片段
    distance_to_start = analysis_length // 2 if match_position - reference_start > analysis_length // 2 else match_position - reference_start
    distance_to_end = analysis_length // 2 if len(paper_text) - match_position > analysis_length // 2 else len(paper_text) - match_position    
    snippet = paper_text[max(match_position - (analysis_length - distance_to_end), reference_start)
                         : min(match_position + (analysis_length - distance_to_start), len(paper_text))]
    # print("##################pattern analysis##################")
    # print(snippet)

    all_patterns = [r'\[\s*(\d+)\s*\]', r'\b(\d+)\s*\.', r'^\s*(\d+)\s*$']
    
    # 检查片段中是否包含连续的引用
    def contains_subsequence(nums, expected):
        dp = {}
        for num in nums:
            prev = num - 1
            current_length = dp.get(prev, 0) + 1
            if current_length >= expected:
                return True
            if current_length > dp.get(num, 0):
                dp[num] = current_length
        return False

    patterns = []
    if (len(snippet) < analysis_length):
        patterns = all_patterns
    else:
        # 遍历引用格式，判断是哪个格式
        for pattern in all_patterns:
            matches = re.findall(pattern, snippet, re.MULTILINE)
            numbers = [int(match) for match in matches if 0 <= int(match) <= 1500]  # 把引用编号限制在合理范围内，过滤掉年份等其他数字
            if contains_subsequence(numbers, expected_consecutive_numbers):
                # print(f"found pattern: {numbers}")
                patterns.append(pattern)
                break
        
        if len(patterns) == 0:
            # print("No reference pattern found.")
            return None
        
        
    # 提取匹配位置前最后一项符合模式的数字
    search_text = paper_text[match_position - 500: match_position]
    
    # print("##################index search##################")
    # print(search_text)

    reference_number = None
    def find_last_match(search_text, patterns):
        last_match = None
        last_pos = -1        
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, search_text, re.IGNORECASE | re.MULTILINE))
            match = matches[-1] if matches else None
            if match is None:
                continue
            if (match.start() > last_pos):
                last_match = match
                last_pos = match.start()
       
        return last_match  
    
    # print("Searching with patterns:", patterns)
    match = find_last_match(search_text, patterns)
    reference_number = int(match.group(1)) if match else None
    
    # if reference_number:
    #     print(f"Reference number found: {reference_number}")
    # else:
    #     print("No reference number found.")

    return reference_number


def extract_citation_positions(paper_text, authors, year, reference_number = None, methodNames = []):
    results = []
    
    # Match numeric citations
    if reference_number is not None:
        numeric_pattern = r'\[([0-9\,\-\–\s\[\]]+)\]'
        numeric_matches = re.finditer(numeric_pattern, paper_text)
        for match in numeric_matches:
            elements = match.group(1).replace(" ", "").replace("][", ",").replace("]-[", "-").replace("]–[", "–").split(',')
            found = False
            for elem in elements:
                if '-' in elem or '–' in elem:
                    parts = re.split(r'[-–]', elem)
                    if len(parts) != 2:
                        continue
                    try:
                        start_num = int(parts[0].strip())
                        end_num = int(parts[1].strip())
                    except ValueError:
                        continue
                    if start_num <= reference_number <= end_num:
                        found = True
                        break
                else:
                    try:
                        num = int(elem.strip())
                    except ValueError:
                        continue
                    if num == reference_number:
                        found = True
                        break                    
            if found:
                results.append((match.start(), match.end()))

    # Match author and year citations
    surnames = [name.split()[-1] for name in authors]
    separator = r'(?:\s+and\s+|\s*&\s*|\s*,\s*|\s+)'
    author_pattern = rf'(?P<name0>{surnames[0]}){separator}+'
    for i in range(1, len(surnames)):
        author_pattern += rf'((?P<name{i}>{surnames[i]}){separator}+)?'
    author_pattern += rf'(?P<etal>et\s+al\.?)?\s*(,\s*)?(?:\(\s*{year}\s*\)|{year}|\[\s*{year}\s*\])'
    author_regex = re.compile(author_pattern, re.IGNORECASE)
    for match in author_regex.finditer(paper_text):
        if match.group('etal') and match.group(f'name{len(surnames) - 1}'):
            continue
        if not match.group('etal') and not match.group(f'name{len(surnames) - 1}'):
            continue
        results.append((match.start(), match.end()))
        
    # Match method name citations
    for methodName in methodNames:
        method_pattern = rf'{methodName}'
        method_regex = re.compile(method_pattern, re.IGNORECASE)
        for match in method_regex.finditer(paper_text):
            results.append((match.start(), match.end()))
    
    # Sort results by start position
    results.sort(key=lambda x: x[0])
    
    return results


def extract_citation_snippets(paper_text, citation_positions):
    snippet_length = 1000
    snippets = []
    for start, end in citation_positions:
        snippet_start = max(0, start - snippet_length // 2)
        snippet_end = min(len(paper_text), end + snippet_length // 2)
        snippets.append((snippet_start, snippet_end))
        
    # Merge overlapping snippets
    merged_snippets = []
    for snippet in snippets:
        if not merged_snippets or merged_snippets[-1][1] < snippet[0]:
            merged_snippets.append(snippet)
        else:
            merged_snippets[-1] = (merged_snippets[-1][0], max(merged_snippets[-1][1], snippet[1]))
            
    snippet_strings = [paper_text[start:end] for start, end in merged_snippets]
    return snippet_strings

def validate_output(json_result):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "Citations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "Text": {"type": "string"},
                        "Analysis": {"type": "string"},
                        "Positive": {"type": "boolean"}
                    },
                    "required": ["Text", "Analysis", "Positive"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["Citations"],
        "additionalProperties": False
    }
    
    jsonschema.validate(instance=json_result, schema=schema)


def retry(operation, max_retries=10, delay=1):
    """
    Retry an operation up to max_retries times.
    
    Args:
        operation: A parameterless function to execute.
        max_retries: Maximum number of retries.
        delay: Delay between retries in seconds.
    """
    times = 0
    exceptions = []
    while True:
        try:
            return operation()
        except Exception as e:
            exceptions.append(e)
            print(f"Error: {str(e)}, retry {times+1}/{max_retries}")
            times += 1
            time.sleep(delay)
            if times >= max_retries:
                print("Fail!")
                raise Exception(f"All retries failed: {'; '.join(str(e) for e in exceptions)}")