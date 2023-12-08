from uploaders.langchain_pdf import upload as load_pdf
from uploaders.langchain_txt import upload as load_txt
from uploaders.langchain_csv import upload as load_csv
import requests
import logging

def type_supported(type:str) -> bool:
    if type in ["application/pdf", "text/csv", "text/plain"]:
        return True
    return False

def upload(file:any) -> bool:
    if file.type == "application/pdf":
        return load_pdf(file)
    elif file.type == "text/csv":
        return load_csv(file)
    elif file.type == "text/plain":
        return load_txt(file)
    else:
        logging.error(f'file type not supported')
        return False

def process_url(url:str) -> bool:
    response = requests.get(url)
    type = response.headers['Content-Type']
    if type == "application/pdf":
        load_pdf(response.content)
    else:
        return False
    return True