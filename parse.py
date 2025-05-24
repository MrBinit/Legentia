import os
import pymupdf4llm
import pathlib
from docx import Document
import ollama
import logging
from dotenv import load_dotenv

load_dotenv()

LOG_PATH = os.getenv("LOG_PATH")
PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR")
DOCX_OUTPUT_DIR = os.getenv("DOCX_OUTPUT_DIR")
IMAGE_OUTPUT_DIR = os.getenv("IMAGE_OUTPUT_DIR")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        #log to file.
        logging.FileHandler(LOG_PATH),
        # log to console.
        logging.StreamHandler()
    ]
)

# class parse_document:


#     def __init__(self):

#         pass


def get_next_filename(dir_path, base_name):
    """Find next available file name like base_name_1.md, base_name_2.md, etc."""

    dir_path = pathlib.Path(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    existing_files = list(dir_path.glob(f"{base_name}_*.md"))
    max_index = 0

    for file in existing_files:
        try:
            number = int(file.stem.split('_')[-1])
            max_index = max(max_index, number)
        except ValueError:
            continue

    return dir_path / f"{base_name}_{max_index + 1}.md"

def pdf_parse(document_path):
    """ This function parses the pdf."""
    try:
        md_text = pymupdf4llm.to_markdown(document_path, ignore_images=True)
        output_path = get_next_filename(PDF_OUTPUT_DIR,
                                         "pdf_output")
        output_path.write_bytes(md_text.encode())
        logging.info(f"PDF parsed and saved to {output_path}")
        return md_text
    except Exception as e:
        logging.error(f"Error parse PDF: {e}")
        raise

def docx_parse(document_path):
    """Parse DOCX and save as incrementing markdown file"""
    try:
        doc = Document(document_path)
        full_text = '\n'.join([para.text for para in doc.paragraphs])
        output_path = get_next_filename(DOCX_OUTPUT_DIR,
                                        "docx_output")
        output_path.write_text(full_text, encoding='utf-8')
        logging.info(f"DOCX parsed and saved to {output_path}")
        return full_text
    except Exception as e:
        logging.error(f"Error parsing DOCX: {e}")
        raise


def image_parse(document_path):
    """Parse Image using LLaMA Vision and save as incrementing markdown file"""
    try:
        response = ollama.chat(
            model='llama3.2-vision:11b',
            messages=[{
                'role': 'user',
                'content': 'Extract all the text from the image. Please don’t write anything else',
                'images': [document_path]
            }]
        )
        text = response['message']['content']
        output_path = get_next_filename(IMAGE_OUTPUT_DIR,
                                         "image_output")
        output_path.write_text(text, encoding='utf-8')
        logging.info(f"Image parsed and saved to {output_path}")
        return text
    except Exception as e:
        logging.error(f"Error parsing image: {e}")
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



parse_document("/home/binit/Legentia/legal_documents/legal.pdf")
