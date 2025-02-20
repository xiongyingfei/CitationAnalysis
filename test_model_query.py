import pytest
import json
import openai
import os
import config
from common import loadPaperInfo, extract_references, extract_citation_positions, extract_citation_snippets
from common import validate_output
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List

def query_model(paper_id, citation_id, snippet_index, reference_number, config):
    snippet_path = f"testfiles/{paper_id}_{citation_id}_snippets.json"
    
    if not os.path.exists(snippet_path):
        raise FileNotFoundError(f"Snippets file {snippet_path} does not exist.")
    
    with open(snippet_path, "r", encoding="utf-8") as f:
        (snippets, reference_number) = json.load(f)
    
    if snippet_index < 1 or snippet_index > len(snippets):
        raise IndexError(f"Snippet index {snippet_index} is out of range.")
    
    snippet = snippets[snippet_index - 1]
    print("snippet:\n", snippet)
    
    # Load paper info
    paper_info = loadPaperInfo(paper_id, f"testfiles/{paper_id}_info.json")
    
    user = config.user_prompt_template.format(paper=paper_info.citation(),
                                              reference_number=reference_number,
                                              approach_name=", 或者".join(paper_info.approach_name),
                                              text=snippet)
    
    result = invoke_model_openai(config, user)
    return result

def invoke_model_openai(config, user):
    client = openai.OpenAI(api_key=config.api_key, base_url=config.base_url)
    response = client.chat.completions.create(
        model=config.model,
        messages=[
            {"role": "system", "content": config.system_prompt},
            {"role": "user", "content": user}
        ],
        response_format=config.response_format,
        temperature=0.2
        # ,
        # max_tokens=8192,
    )
    print("response:\n", response.choices[0].message.content)
    if response.choices[0].finish_reason != "stop" and response.choices[0].finish_reason != "normal":
        raise Exception(f"OpenAI API response did not finish normally: {response.choices[0].finish_reason}")
    msg = response.choices[0].message.content.strip()
    msg = msg[msg.find("{"):msg.rfind("}")+1]
    result = json.loads(msg)
    validate_output(result)
    return result

def validate_result(result, expected):
    result = result["Citations"]
    assert len(result) == len(expected)
    for i, citation in enumerate(result):
        if expected[i][1] != None:
            assert citation["Positive"] == expected[i][1]
        assert expected[i][0] in citation["Text"]

def invoke_model_langchain(config, user):
    class CitationItem(BaseModel):
        Text: str = Field(description="The text of the citation snippet")
        Analysis: str = Field(description="Analysis for the snippet")
        Positive: bool = Field(description="Whether the snippet is positive")

    class CitationList(BaseModel):
        Citations: List[CitationItem] = Field(description="List of citation objects")

    llm = ChatOpenAI(
        api_key=config.api_key,
        model_name=config.model,
        base_url=config.base_url,
        temperature=0.0
    )
    structured_llm = llm.with_structured_output(CitationList)
    prompt_text = f"{config.system_prompt}\n{user}"
    response = structured_llm.invoke(prompt_text)
    return response

        
def validate_number_only_citation(config):
    paper_id = "AAAI20"
    citation_id = 4
    snippet_index = 1
    reference_number = 38
    expected = [
        ("[5, 16, 17, 22, 38, 39, 48, 49]", False)]
    result = query_model(paper_id, citation_id, snippet_index, reference_number, config)
    validate_result(result, expected)

def validate_novel_quotation(config):
    paper_id = "AAAI20"
    citation_id = 2
    snippet_index = 3
    reference_number = 106
    expected = [
        ("Sun et al. [106] proposed a novel", True)]
    result = query_model(paper_id, citation_id, snippet_index, reference_number, config)
    validate_result(result, expected)
    
def validate_name_citation(config):
    paper_id = "AAAI20"
    citation_id = 3
    snippet_index = 1
    reference_number = None
    expected = [
        ("(Mou et al., 2015; Svyatkovskiy et al., 2020; Sun et al., 2020)", None),
        ("transformer-based techniques (Svyatkovskiy et al., 2020; Sun et al., 2020)", None)
    ]
    result = query_model(paper_id, citation_id, snippet_index, reference_number, config)
    validate_result(result, expected)
    
    
def validate_confusing_numbers(config): #aliyun's deepseek fails on this case very often
    paper_id = "FSE21"
    citation_id = 12
    snippet_index = 16
    reference_number = 16
    result = query_model(paper_id, citation_id, snippet_index, reference_number, config)
    result = result["Citations"]
    probdd_count = sum(citation["Text"].count("ProbDD") for citation in result)
    assert probdd_count >= 8, f"Expected 16 'ProbDD' substrings, but found {probdd_count}"
    
def validate_confusing_snippet(config): #aliyun's deepseek failed on this case 
    paper_id = "FSE21"
    citation_id = 42
    snippet_index = 1
    reference_number = 41
    result = query_model(paper_id, citation_id, snippet_index, reference_number, config)
    expected = [
        ("[18, 24, 17, 39, 43, 4, 41, 40]", None)
    ]    
    validate_result(result, expected)

def validate_important_citation(config): 
    paper_id = "FSE21"
    citation_id = 48
    snippet_index = 1
    reference_number = 20
    result = query_model(paper_id, citation_id, snippet_index, reference_number, config)
    expected = [
        ("One important enhancement", True)
    ]    
    validate_result(result, expected)


def validate_complex_snippet_extraction(config): #aliyun's deepseek failed on this case
    paper_id = "FSE21"
    citation_id = 43
    snippet_index = 1
    reference_number = 10
    expected = [
        ("ProbDD", None)
    ]
    result = query_model(paper_id, citation_id, snippet_index, reference_number, config)
    validate_result(result, expected)
    

@pytest.mark.skip(reason="Skipping this test because it is expensive. Comment this line to execute")
def test_all_validations():
    model = config.model
    validate_number_only_citation(model)
    validate_novel_quotation(model)
    validate_name_citation(model)
    validate_confusing_numbers(model)
    validate_confusing_snippet(model)
    validate_complex_snippet_extraction(model)
    validate_important_citation(model)


# validate_confusing_numbers(config.model)