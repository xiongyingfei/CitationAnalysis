import json
from common import extract_references, loadPaperInfo, extract_citation_positions, extract_citation_snippets
from common import load_citation_info, save_citation_info, validate_output
import requests_cache
import openai
import os
import fitz  # PyMuPDF
import config as configs
import time
import traceback
import prompts
import logging
from logging.handlers import TimedRotatingFileHandler

config = configs.model

session = requests_cache.CachedSession('cache/http.db', expire_after=30*86400)


paper_id = configs.citation_analysis_id

paper_info = loadPaperInfo(paper_id)

"""
该代码块将指定目录中的PDF文件转换为文本，并将提取的文本保存到相应的.txt文件中。
"""
import os

import fitz  # PyMuPDF

def pdf_to_text(paper_id):
    i = 1
    while True:
        info_path = f"{paper_id}/Citation_{i}.json"
        if not os.path.exists(info_path):
            break

        pdf_path = f"{paper_id}/Citation_{i}.pdf"
        if not os.path.exists(pdf_path):
            # print(f"{pdf_path} does not exist. Skipping extraction.")
            i += 1
            continue
        
        txt_path = f"{paper_id}/Citation_{i}.txt"
        if os.path.exists(txt_path):
            # print(f"{txt_path} already exists. Skipping extraction.")
            i += 1
            continue
        
        try:
            with fitz.open(pdf_path) as pdf_document:
                text = ""
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    text += page.get_text()
                
                # 保存提取的文本到对应的 .txt 文件
                with open(txt_path, "w", encoding="utf-8") as txt_file:
                    txt_file.write(text)
                print(f"Extracted text from {pdf_path} and saved to {txt_path}")
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
        i += 1

def text_to_citation_snippets(paper_id, citation_id):
    # paper_info = loadPaperInfo(paper_id)
    with open(f"{paper_id}/Citation_{citation_id}.txt", "r", encoding="utf-8") as file:
        paper_text = file.read()
    
    reference_number = extract_references(paper_info.title, paper_text)
    
    positions = extract_citation_positions(paper_text, paper_info.authors, paper_info.year, reference_number, paper_info.approach_name)
    
    snippets = extract_citation_snippets(paper_text, positions)
    
    return (snippets, reference_number)

def text_to_analyzed_snippets(paper_id, citation_id):
    
    analysis_path = f"{paper_id}/Citation_{citation_id}_analysis.json"
    analyzed_snippet_indices = set()
    results = []

    if os.path.exists(analysis_path):
        with open(analysis_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            analyzed_snippet_indices = set(existing_data["AnalyzedSnippetIndices"] 
                                           if "AnalyzedSnippetIndices" in existing_data else [])
            results = existing_data["Citations"]
        
    print("Analyzing Citation", citation_id)

    snippets_path = f"{paper_id}/Citation_{citation_id}_snippets.json"
    def extract_citation_snippets(paper_id, citation_id, snippets_path):
        snippets, reference_number = text_to_citation_snippets(paper_id, citation_id)
        with open(snippets_path, "w", encoding="utf-8") as f:
            json.dump((snippets, reference_number), f, ensure_ascii=False, indent=2)
        return snippets, reference_number

    if os.path.exists(snippets_path):
        try:
            with open(snippets_path, "r", encoding="utf-8") as f:
                (snippets, reference_number) = json.load(f)
                if not isinstance(snippets, list) or not all(isinstance(snippet, str) for snippet in snippets):
                    raise TypeError("Snippets must be a list of strings.")
                if not isinstance(reference_number, int) and reference_number is not None:
                    raise TypeError("Reference number must be an integer or None.")
        except (IOError, json.JSONDecodeError, TypeError, ValueError) as e:
            print(f"Error loading snippets from {snippets_path}: {e}")
            snippets, reference_number = extract_citation_snippets(paper_id, citation_id, snippets_path)
    else:
        snippets, reference_number = extract_citation_snippets(paper_id, citation_id, snippets_path)
    
    exceptions = []
    
    for index, snippet in enumerate(snippets, start=1):
        if index in analyzed_snippet_indices:
            continue

        user = config.user_prompt_template.format(paper=paper_info.citation(),
                                            reference_number=reference_number,
                                            approach_name=", 或者".join(paper_info.approach_name),
                                            text=snippet)

        try:
            result = json_model_query(config.system_prompt, user)
            results.extend(result["Citations"])
            analyzed_snippet_indices.add(index)
            print(f"Analyzed snippet {index} of Citation {citation_id}")
        except Exception as e:
            print(f"Error analyzing snippet {index} of Citation {citation_id}:\n", traceback.format_exc())
            exceptions.append((index, str(e)))
        
        # Save results after analyzing each snippet
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump({
                "Citations": results, 
                "AnalyzedSnippetIndices": list(analyzed_snippet_indices),
                "EncounteredExceptions": exceptions}, f, ensure_ascii=False, indent=2)

    return results


# Configure logging: logs rotate daily and older than 30 days will be deleted.
handler = TimedRotatingFileHandler('cache/model_dialog.log', when='D', interval=1, backupCount=30, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])

def json_model_query(system, user):
    time.sleep(config.pause_seconds)
    
    # Log outgoing messages
    logging.info("Sending request with system message: %s", system)
    logging.info("Sending request with user message: %s", user)
    
    client = openai.OpenAI(api_key=config.api_key, base_url=config.base_url)
    response = client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                response_format=config.response_format,
                temperature=0.2
            )
    
    # Log full response content from the model
    logging.info("Received response: %s", response.choices[0].message.content)
    
    if response.choices[0].finish_reason != "stop":
        raise Exception(f"OpenAI API response did not finish normally: {response.choices[0].finish_reason}")
    try:
        msg = response.choices[0].message.content.strip()
        msg = msg[msg.find("{"):msg.rfind("}")+1]
        result = json.loads(msg)
        validate_output(result)
    except Exception as e:
        raise Exception(f"Parsing failed.\nResponse:\n{response.choices[0].message.content}\nMessage:\n{str(e)}")
    return result

def get_citation_text(citation_info):
    title = citation_info["Title"]
    rest = citation_info["Title"]
    if "SemScholar_authors" in citation_info and "SemScholar_venue" in citation_info and "SemScholar_year" in citation_info:
        authors = ", ".join(author["name"] for author in citation_info["SemScholar_authors"])        
        rest = f"{authors}. {citation_info['SemScholar_venue']}. {citation_info['SemScholar_year']}."
    return f"{title}. {rest}"
    
pdf_to_text(paper_id)

i = 1
all_citation_papers = []
while True:
    info_path = f"{paper_id}/Citation_{i}.json"
    if not os.path.exists(info_path):
        break
    
    txt_path = f"{paper_id}/Citation_{i}.txt"
    if not os.path.exists(txt_path):
        i += 1
        continue
    
    snippets = text_to_analyzed_snippets(paper_id, i)    
    
    snippets.sort(key=lambda x: not x["Positive"])  # Sort with Positive=True first
    
    paper = dict(Citations=snippets, 
                 Paper=get_citation_text(load_citation_info(paper_id, i)),
                 ID = i)
    
    all_citation_papers.append(paper)

    i += 1
    
# Sort papers by number of positive citations
sorted_papers = sorted(all_citation_papers, 
                        key=lambda paper: sum(1 for snippet in paper["Citations"] if snippet["Positive"]), 
                        reverse=True)

# Save sorted results
with open(f"{paper_id}/all_snippets.json", "w", encoding="utf-8") as f:
    json.dump(sorted_papers, f, ensure_ascii=False, indent=2)

with open(f"{paper_id}/all_snippets.txt", "w", encoding="utf-8") as f:
    for paper in sorted_papers:
        f.write(f"Paper {paper['ID']}: {paper['Paper']}\n")
        for citation in paper["Citations"]:
            f.write(f"  - Analysis: {citation['Analysis']}\n")
            f.write(f"    Positive: {citation['Positive']}\n")
            f.write(f"    Citation: {citation['Text']}\n")
            f.write("\n")
        f.write("\n")
