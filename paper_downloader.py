import requests_cache
import requests
import os
import json
import random
import common
from common import load_citation_info, save_citation_info
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
import Levenshtein
from fuzzywuzzy import process
import config



############################################
# 一些公共代码

session = requests_cache.CachedSession('cache/http.db', expire_after=30*86400)

############################################
# 读取info.json文件

paper_id = config.paper_download_id
scholar_id = common.loadPaperInfo(paper_id).scholar_id

############################################
# 下载谷歌学术引用页

def wait_for_page_load(driver, timeout=20):
    wait = WebDriverWait(driver, timeout)
    # 检查scholar页面是否加载完成
    wait.until(EC.presence_of_element_located((By.ID, "gs_res_ccl_top")))
    wait.until(EC.presence_of_element_located((By.ID, "gs_res_ccl_mid")))
    wait.until(EC.presence_of_element_located((By.ID, "gs_res_ccl_bot")))

start_page_number = 1 # 默认为1，设置成其他值用于下载中断时的恢复
page_number = start_page_number 
url = f"https://scholar.google.com/scholar?cites={scholar_id}"
if page_number > 1:
    url += f"&start={page_number - 1}0"
file_path_pattern = os.path.join(paper_id, f"scholar_page_{{number}}.html")

# 检查文件是否存在
if not os.path.exists(file_path_pattern.format(number=page_number)):
    # 设置浏览器选项
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 无头模式
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    # 启动浏览器
    driver = webdriver.Chrome(options=options)
    print(f"Starting download from {url}")
    driver.get(url)
    # time.sleep(5)  # 等待页面加载
    try:
        while True:
            # 等待页面加载
            while True:
                try:
                    wait_for_page_load(driver)
                except TimeoutException:
                    driver = webdriver.Chrome(options=options)
                    driver.get(url)
                    print ("Timeout ! retry!")
                    time.sleep(5)
                    continue
                break
            # 加载完成后读取页面内容
            page_content = driver.page_source

            # 将内容保存到文件
            file_path = file_path_pattern.format(number=page_number)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(page_content)
                
            print(f"Downloaded page {page_number} at {driver.current_url}")
                
            # 检查是否存在下一页按钮
            try:
                next_button = driver.find_element(By.LINK_TEXT, 'Next')
            except:
                try:
                    next_button = driver.find_element(By.LINK_TEXT, '下一页')
                except:
                    try:
                        next_button = driver.find_element(By.XPATH, "//a[normalize-space(.)='下一页']")
                    except:
                        try:
                            next_button = driver.find_element(By.XPATH, "//a[normalize-space(.)='Next']")
                        except:
                            next_button = None

            if next_button:
                time.sleep(5 + 10 * random.random())  # Random wait between 5-15 seconds
                # next_button.click()
    
                next_href = next_button.get_attribute('href')
                if next_href:
                    driver.get(next_href)
                else:
                    # 如果没有href则尝试JavaScript点击
                    actions = ActionChains(driver)
                    actions.move_to_element(next_button).perform()
                    wait = WebDriverWait(driver, 10)
                    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space(.)='下一页']")))
                    driver.execute_script("arguments[0].click();", next_button)

                page_number += 1
            else:
                print("No next button found, stopping.")
                break

    finally:
        driver.quit()

############################################
# 解析引用页，获得引用下载信息

def parse_citations_from_html(html_content):
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    citations_data = []

    # 查找所有引文条目
    citations = soup.find_all('div', class_='gs_r gs_or gs_scl')
    
    for citation in citations:
        try:
            # 提取下载链接
            download_link = "No Link"
            first_div = citation.find('div', class_='gs_ggs gs_fl')
            if first_div:
                pdf_link_tag = first_div.find('a')
                if pdf_link_tag:
                    download_link = pdf_link_tag['href']
            
            # 提取标题和作者列表
            second_div = citation.find('div', class_='gs_ri')
            title_tag = second_div.find('h3', class_='gs_rt') if second_div else None
            title = title_tag.text if title_tag else "No Title"
            
            # 提取页面链接
            page_link_tag = title_tag.find('a') if title_tag else None
            page_link = page_link_tag['href'] if page_link_tag else "No Link"
            
            authors_tag = second_div.find('div', class_='gs_a') if second_div else None
            authors = authors_tag.text if authors_tag else "No Authors"
            
            citations_data.append({
                'Title': title,
                'Authors': authors,
                'DownloadLink': download_link,
                'PageLink': page_link
            })
        except Exception as e:
            print(f"Error extracting citation: {e}")

    return citations_data

# 遍历所有 scholar_page 文件并解析

def parse_download_citations(start_page=1):
    page_number = start_page
    citation_index = (start_page - 1) * 10 + 1
    while True:
        file_path = file_path_pattern.format(number=page_number)
        if not os.path.exists(file_path):
            break
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Parse citations from current page
        citations_data = parse_citations_from_html(html_content)
        
        # Save each citation to individual JSON file
        for citation in citations_data:
            citation_file = f"{paper_id}/Citation_{citation_index}.json"
            if os.path.exists(citation_file):
                citation_index += 1
                continue
            citation["SemScholarQueried"] = False
            save_citation_info(paper_id, citation_index, citation)
            citation_index += 1
        
        page_number += 1
        
# Check if any citation files exist
citation_file = f"{paper_id}/Citation_{(start_page_number - 1)*10+1}.json"
if not os.path.exists(citation_file):
    parse_download_citations(start_page_number)

############################################
# 利用Semantic Scholar API获取更精确的信息

def download_semantic_scholar_info(paper_id, citation_id):
    citation_info = load_citation_info(paper_id, citation_id)
        
    if citation_info["SemScholarQueried"]:
        return
    
    print(f"Getting Semantic Scholar info for citation {citation_id}: {citation_info['Title']}")
    
    title = citation_info["Title"]
    
    # https://api.semanticscholar.org/api-docs/
    NECESSARY_FIELDS = ['title', 'paperId', 'authors', 'venue', 'year', 'externalIds', 'citationCount', 'openAccessPdf']
    SEARCHED_FIELDS = ['Computer Science']

    def search_paper(title: str):
        response = session.get('https://api.semanticscholar.org/graph/v1/paper/search/match', params={
        'query': title,
        'fields': ','.join(NECESSARY_FIELDS), 
        'fieldsOfStudy': SEARCHED_FIELDS,
        })
        # Return empty list for 404 Not Found
        if response.status_code == 404:
            raise Exception
            return []
        response.raise_for_status()
        return response.json()['data']
    
    data = search_paper(title)
    
    if not data:
        citation_info["SemScholarQueried"] = True
        save_citation_info(paper_id, citation_id, citation_info)
        return
    
    if len(data) > 1:
        # Extract title and author/venue info from Google Scholar citation
        scholar_title = citation_info['Title'].lower()
        scholar_text = citation_info['Authors'].lower()
        scholar_combined = f"{scholar_title}. {scholar_text}"
        
        # Create combined strings for each paper in data
        paper_texts = {i: 
            f"{p['title'].lower()}. {' '.join(a['name'].lower() for a in p['authors'])} - {p['venue'].lower() if p['venue'] else ''}"
            for i, p in enumerate(data)}
        
        # Find best match using process.extractOne
        best_match_index = process.extractOne(scholar_combined, paper_texts.values())[2]
        best_match = data[best_match_index]
        
        data = [best_match]

    
    # Remove matchScore from data dictionary
    if 'matchScore' in data[0]:
        del data[0]['matchScore']
    
        
    # 将data字典的每个key前面加上"SemScholar_"前缀，并和citation_info合并
    citation_info.update({f"SemScholar_{k}": v for k, v in data[0].items()})
    citation_info["SemScholarQueried"] = True

    save_citation_info(paper_id, citation_id, citation_info)
    
    print(f"Done")
    
        
    time.sleep(1)  # Rate limiting

# 遍历citation_i.json文件，下载Semantic Scholar信息
i = 1
while True:
    citation_file = f"{paper_id}/Citation_{i}.json"
    if not os.path.exists(citation_file):
        break
    times = 0
    while True:
        try:
            download_semantic_scholar_info(paper_id, i)
        except Exception as e:
            print(f"Error processing citation {i}: {e}")
            times += 1
            time.sleep(1)
            if times >= 10:
                print ("Fail!")
                break
            continue
        break
    i += 1

############################################
# 下载引用的文件

class PDFDownloadException(Exception):
    def __init__(self, message, content):
        super().__init__(message)
        self.content = content

def download_pdf_file(url, file_name):
    response = getURL(url)
    response.raise_for_status()  # 检查请求是否成功
    
    # Check if the content is a PDF by looking for the PDF header signature
    if not response.content.startswith(b'%PDF'):
        raise PDFDownloadException("Downloaded content is not a PDF file.", response.content)

    # 将内容保存到文件
    with open(file_name, 'wb') as file:
        file.write(response.content)
    print(f"Downloaded {file_name} from {url}.")

def getURL(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    return response

def download_gScholar_file_link(citation, file_name) -> bool:
    url = citation['DownloadLink']
    if url == "No Link":
        return False
    download_pdf_file(url, file_name)
    return True
    
def download_semScholar_file_link(citation, file_name) -> bool:
    if 'SemScholar_openAccessPdf' not in citation:
        return False
    url = citation['SemScholar_openAccessPdf']['url']
    if not url:
        return False
    download_pdf_file(url, file_name)
    return True
    

def download_arxiv(citation, file_name) -> bool:
    url = citation['PageLink']
    if "arxiv.org/abs" not in url:
        return False
    url = url.replace("arxiv.org/abs", "arxiv.org/pdf")
    download_pdf_file(url, file_name)
    return True

def download_acm(citation, file_name) -> bool:
    url = citation['PageLink']
    if "https://dl.acm.org/doi/abs" in url:
        url = url.replace("https://dl.acm.org/doi/abs", "https://dl.acm.org/doi/pdf")
    elif not "https://dl.acm.org/doi/pdf" in url:
        return False
    download_pdf_file(url, file_name)
    return True


def download_ieee(citation, file_name) -> bool:
    url = citation['PageLink']
    if "ieeexplore.ieee.org/abstract/document/" not in url:
        return False
    match = re.search(r'document/(\d+)', url)
    if not match:
        raise Exception(f"Invalid IEEE URL: {url}")
    ieee_number = match.group(1)
    download_pdf_file(f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={ieee_number}", file_name)
    return True

def download_springer_article(citation, file_name) -> bool:
    url = citation['PageLink']
    if "link.springer.com/article" not in url:
        return False
    response = getURL(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    div_tag = soup.find('div', class_='c-pdf-container')
    if div_tag:
        pdf_link_tag = div_tag.find('a', href=True)
        if pdf_link_tag:
            pdf_link = pdf_link_tag['href']
            download_pdf_file("http://link.springer.com" + pdf_link, file_name)
            return True
        else:
            raise Exception("PDF link not found in the HTML content.")
    else:
        raise Exception("c-pdf-container not found in the HTML content.")

def download_springer_chapter(citation, file_name) -> bool:
    url = citation['PageLink']
    if "link.springer.com/chapter" not in url:
        return False
    response = getURL(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    div_tag = soup.find('div', class_='c-article-access-provider')
    if div_tag:
        pdf_link_tag = div_tag.find('a', href=True)
        if pdf_link_tag:
            pdf_link = pdf_link_tag['href']
            download_pdf_file("http://link.springer.com" + pdf_link, file_name)
            return True
        else:
            raise Exception("PDF link not found in the HTML content.")
    else:
        raise Exception("c-pdf-container not found in the HTML content.")

def try_downloaders(downloaders, citation, file_name) -> None:
    exceptions = []
    if os.path.exists(file_name):
        print(f"File already exists: {file_name}, skipping download.")
        return

    for downloader in downloaders:
        try:
            if downloader(citation, file_name):
                return 
        except Exception as e:
            exceptions.append(e)
            print(f"Downloader {downloader.__name__} failed: {e}")
            
            if isinstance(e, PDFDownloadException):
                with open(file_name.replace(".pdf", f'_{downloader.__name__}_failed.html'), 'wb') as file:
                    file.write(e.content)

    
    # If all downloaders failed, raise an exception that combines all preivous exceptions
    if exceptions:
        raise Exception(f"All downloaders failed: {'; '.join(str(e) for e in exceptions)}")
    else:
        raise Exception("No downloader applicable")

# 下载每个引用的文件
i = 1
while True:
    citation_file = f"{paper_id}/Citation_{i}.json"
    if not os.path.exists(citation_file):
        break
    
    citation = load_citation_info(paper_id, i)
    
    file_name = os.path.join(paper_id, f"Citation_{i}.pdf")
    missing_name = os.path.join(paper_id, f"Citation_{i}_missing.txt")
    if os.path.exists(file_name) or os.path.exists(missing_name):
        i += 1
        continue

    downloaders = [
        download_gScholar_file_link,
        download_arxiv,
        download_ieee,
        download_acm,
        download_springer_article,
        download_springer_chapter
    ]

    print(f"Downloading {file_name}")
    times = 0
    while True:
        try:
            try_downloaders(downloaders, citation, file_name)
        except Exception as e:
            if times >= 5:
                msg = f"Failed to download {file_name} : {e}"
                print(msg)
                with open(missing_name, 'w', encoding='utf-8') as file:
                    file.write(msg)
            times += 1
            time.sleep(1)
            continue
        break
    i += 1
