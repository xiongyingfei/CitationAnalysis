import pytest
from common import extract_references

def test_extract_references_no_references_section():
    title = "Sample Title"
    paper_text = "This is a sample paper text without a references section."
    result = extract_references(title, paper_text)
    assert result is None

def test_extract_references_with_references_section():
    title = "Sample Title"
    paper_text = """
    This is a sample paper text.
    
    References
    [1] Sample Title. Sample Author. Sample Journal. 2020.
    """
    result = extract_references(title, paper_text)
    assert result == 1

def test_extract_references_with_bibliography_section():
    title = "Sample Title"
    paper_text = """
    This is a sample paper text.
    
    Bibliography
    1. Sample Title. Sample Author. Sample Journal. 2020.
    """
    result = extract_references(title, paper_text)
    assert result == 1

def test_extract_references_with_works_cited_section():
    title = "Sample Title"
    paper_text = """
    This is a sample paper text.
    
    Works Cited
    Sample Title. Sample Author. Sample Journal. 2020.
    """
    result = extract_references(title, paper_text)
    assert result is None  # No number format found

def test_extract_references_with_chinese_references_section():
    title = "Sample Title"
    paper_text = """
    This is a sample paper text.
    
    参考文献
    [1] Sample Title. Sample Author. Sample Journal. 2020.
    """
    result = extract_references(title, paper_text)
    assert result == 1

def test_extract_references_best_match():
    title = "Sample Title"
    paper_text = """
    This is a sample paper text.
    
    References
    [1] Another Title. Another Author. Another Journal. 2020.
    [2] Sample Title. Sample Author. Sample Journal. 2020.
    """
    result = extract_references(title, paper_text)
    assert result == 2

def checkAAAI20(citation_id, expected):
    title = "Treegen: A tree-based transformer architecture for code generation"
    paper_id = "AAAI20"
    check_paper(citation_id, expected, title, paper_id)


def checkOOPSLA20(citation_id, expected):
    title = "Guiding Dynamic Programming via Structural Probability for Accelerating Programming by Example"
    paper_id = "OOPSLA20"
    check_paper(citation_id, expected, title, paper_id)


def check_paper(citation_id, expected, title, paper_id):
    with open(f"testfiles/{paper_id}_{citation_id}.txt", "r", encoding="utf-8") as file:
        paper_text = file.read()
    result = extract_references(title, paper_text)
    if expected is None:
        assert result is None
    else:    
        assert result == expected

def test_AAAI20_1():
    checkAAAI20(1, 51)

def test_AAAI20_2():
    checkAAAI20(2, 106)
    
def test_AAAI20_3():
    checkAAAI20(3, None)
    
def test_AAAI20_4():
    checkAAAI20(4, 38)


def test_AAAI20_5():
    checkAAAI20(5, 50)

def test_AAAI20_6():
    checkAAAI20(6, None)

def test_AAAI20_10():
    checkAAAI20(10, 19)

def test_AAAI20_12():
    checkAAAI20(12, None)

def test_OOPSLA20_3():
    checkOOPSLA20(3, 24)
    
def test_OOPSLA20_23():
    checkOOPSLA20(23, 65)