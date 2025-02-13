import pytest
from common import extract_citation_positions

def test_numeric_citations():
    paper_text = "This is a sample text with citations [1, 2, 3]. Another citation [4-6]."
    authors = ["John Doe", "Jane Smith"]
    year = 2021
    reference_number = 2
    result = extract_citation_positions(paper_text, authors, year, reference_number)
    assert len(result) == 1
    assert "2" in paper_text[slice(*result[0])]

def test_numeric_citations_range():
    paper_text = "This is a sample text with citations [1, 2, 3]. Another citation [4-6]."
    authors = ["John Doe", "Jane Smith"]
    year = 2021
    reference_number = 5
    result = extract_citation_positions(paper_text, authors, year, reference_number)
    assert len(result) == 1
    assert "[4-6]" in paper_text[slice(*result[0])]

def test_author_year_citations():
    paper_text = "This is a sample text with citations (Doe, 2021). Another citation (Doe and Smith, 2021)."
    authors = ["John Doe", "Jane Smith"]
    year = 2021
    result = extract_citation_positions(paper_text, authors, year)
    assert len(result) == 1
    assert "Doe and Smith, 2021" in paper_text[slice(*result[0])]

def test_author_year_citations_et_al():
    paper_text = "This is a sample text with citations (Doe et al., 2021). Another citation (Doe, Smith, and et al., 2021)."
    authors = ["John Doe", "Jane Smith"]
    year = 2021
    result = extract_citation_positions(paper_text, authors, year)
    assert len(result) == 1
    assert "Doe et al., 2021" in paper_text[slice(*result[0])]

def test_no_citations():
    paper_text = "This is a sample text with no citations."
    authors = ["John Doe", "Jane Smith"]
    year = 2021
    expected_positions = []
    result = extract_citation_positions(paper_text, authors, year)
    assert result == expected_positions
    
def test_multiple_approach_names():
    paper_text = "This paper uses TreeGen and another method called GraphGen. TreeGen is used for generating trees, while GraphGen is used for generating graphs."
    authors = ["John Doe", "Jane Smith"]
    year = 2021
    approach_names = ["TreeGen", "GraphGen"]
    result = extract_citation_positions(paper_text, authors, year, None, approach_names)
    assert len(result) == 4
    assert "TreeGen" in paper_text[slice(*result[0])]
    assert "GraphGen" in paper_text[slice(*result[1])]
    assert "TreeGen" in paper_text[slice(*result[2])]
    assert "GraphGen" in paper_text[slice(*result[3])]
    
def checkAAAI20(citation_id, expected, reference_number):
    paper_id = "AAAI20"
    authors = ["Zeyu Sun", "Qihao Zhu", "Yingfei Xiong", "Yican Sun", "Lili Mou", "Lu Zhang"]
    year = 2020
    approach_name = ["TreeGen"]
    extract_validate_citations(citation_id, expected, reference_number, paper_id, authors, year, approach_name)

def checkOOPSLA20(citation_id, expected, reference_number):
    paper_id = "OOPSLA20"
    authors = ["Ruyi Ji", "Yican Sun", "Yingfei Xiong", "Zhenjiang Hu"]
    year = 2020
    approach_name = ["MaxFlash"]
    extract_validate_citations(citation_id, expected, reference_number, paper_id, authors, year, approach_name)



def extract_validate_citations(citation_id, expected, reference_number, paper_id, authors, year, approach_name):
    with open(f"testfiles/{paper_id}_{citation_id}.txt", "r", encoding="utf-8") as file:
        paper_text = file.read()
    results = extract_citation_positions(paper_text, authors, year, reference_number, approach_name) 
    for result in results:
        print(paper_text[slice(*result)])
    
    assert len(results) == len(expected)
    for result, expected_result in zip(results, expected):
        assert expected_result.lower() in paper_text[slice(*result)].lower()

def test_AAAI20_1():
    checkAAAI20(1, ["TreeGen", "[51]", "TreeGen", "[51]", "TreeGen", "TreeGen"], 51)
    
def test_AAAI20_3():
    checkAAAI20(3, ["Sun et al., 2020", "Sun et al., 2020", "TreeGen"], None)    
    
def test_AAAI20_18():
    checkAAAI20(18, ["Sun et al. [2020]", "TreeGen"], None)
    
def test_OOPSLA20_3():
    checkOOPSLA20(3, ["[14–18, 24, 33, 35]", "[24]"], 24)    

def test_OOPSLA20_23():
    checkOOPSLA20(23, ["[65]", "[65]", "[65]", "[ 65 ]"], 65)    
    
def test_OOPSLA20_18():
    checkOOPSLA20(18, ["[3, 4, 14–21]", "[21]"], 21)        
    
def test_OOPSLA20_6():
    checkOOPSLA20(6, ["[31–35, 45, 55, 60]", "[45]"], 45)    


def test_OOPSLA20_5():
    checkOOPSLA20(5, ["Ji et al., 2020"], None)    
