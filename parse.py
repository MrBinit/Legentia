import pymupdf4llm
import pathlib
from docx import Document
import ollama
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        #log to file.
        logging.FileHandler("/home/binit/Legentia/parser.log"),
        # log to console.
        logging.StreamHandler()
    ]
)

# class parse_document:


#     def __init__(self):

#         pass

def pdf_parse(document_path):
    """ This function parses the pdf."""
    try:
        md_text = pymupdf4llm.to_markdown(document_path, ignore_images=True)
        pathlib.Path("/home/binit/Legentia/legal_document_parsed/pdf_output.md").write_bytes(md_text.encode())
        return md_text
    except Exception as e:
        logging.error(f"Error parse PDF: {e}")
        raise

def docx_parse(document_path):
    """This function parses the document."""
    try:
        doc = Document(document_path)
        full_text = []

        for para in doc.paragraphs:
            full_text.append(para.text)

        final_text = '\n'.join(full_text)
        pathlib.Path("/home/binit/Legentia/legal_document_parsed/docx_output.md").write_text(final_text, encoding='utf-8')

        return final_text
    except Exception as e:
        logging.error(f"Error parse DOC: {e}")
        raise

def image_parse(document_path):
    """This document will parse image using LLM(llama 3 11b vision)"""
    try:

        response = ollama.chat(
        model='llama3.2-vision:11b',
        messages=[{
            'role': 'user',
            'content': 'Extract all the text from the image. Please dont write anything else',
            'images': [document_path]
        }]
        )

        llm_response = response['message']['content']
        pathlib.Path("/home/binit/Legentia/legal_document_parsed/image_output.md").write_text(response, encoding='utf-8')

        return response
    except Exception as e:
        logging.info(f"Error in parse image {e}")
        raise

def parse_document(document_path):
    """This parses documents of any extension"""
    extension = pathlib.Path(document_path).suffix.lower()
    logging.info(f"Received file with extension: {extension}")

    if extension == ".pdf":
        return pdf_parse(document_path)
    elif extension in ['.doc', '.docx']:
        return docx_parse(document_path)
    elif extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        return image_parse(document_path)
    else:
        logging.error(f"Unsupported file format: {extension}")
        raise ValueError(f"Unsupported file format: {extension}")



parse_document("/home/binit/Legentia/legal_documents/Binuja-MOA.pdf")
