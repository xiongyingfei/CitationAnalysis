import pytest
import json
import jsonschema
from common import validate_output


def test_parse_json_valid():
    jsonstring = """{
    "Citations": [
        {
            "Text": "Sequence-to-sequence models such as BART [49], T5 (Text-to-Text Transfer Transformer) [50], and TreeGen [51] are well-suited for tasks that involve generating new text based on an input, such as code generation, code reﬁnement, defect detection, and clone detection, for AI-assisted programming tasks.",      
            "Analysis": "列举了包括TreeGen在内的序列到序列模型，并指出它们适用于基于输入生成新文本的任务，如代码生成、代码精炼、缺陷检测和克隆检测等AI辅助编程任务。",
            "Positive": true
        }
    ]
}"""

    validate_output(json.loads(jsonstring)) # Should not raise exception
    

def test_validate_output_valid():
    valid_json = {
        "Citations": [
            {
                "Text": "Sample text",
                "Analysis": "Sample analysis", 
                "Positive": True
            }
        ]
    }
    validate_output(valid_json) # Should not raise exception

def test_validate_output_missing_citations():
    invalid_json = {
        "SomethingElse": []
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_output(invalid_json)

def test_validate_output_missing_required_field():
    invalid_json = {
        "Citations": [
            {
                "Text": "Sample text",
                "Analysis": "Sample analysis"
                # Missing Positive field
            }
        ]
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_output(invalid_json)

def test_validate_output_wrong_type():
    invalid_json = {
        "Citations": [
            {
                "Text": "Sample text",
                "Analysis": "Sample analysis",
                "Positive": "true" # Should be boolean not string
            }
        ]
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_output(invalid_json)

def test_validate_output_extra_field():
    invalid_json = {
        "Citations": [
            {
                "Text": "Sample text", 
                "Analysis": "Sample analysis",
                "Positive": True,
                "Extra": "Not allowed"
            }
        ]
    }
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_output(invalid_json)