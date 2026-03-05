"""
File Reader Module - Handles reading different file formats
"""

import os
import PyPDF2
import docx
from PyPDF2.errors import PdfReadError

class FileReader:
    """Handles reading different file formats"""
    
    @staticmethod
    def get_supported_formats():
        """Return list of supported file formats"""
        return ['.pdf', '.docx', '.doc', '.txt', '.text']
    
    @staticmethod
    def read_file(file_path):
        """Read content from various file formats"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.pdf':
                return FileReader._read_pdf(file_path)
            elif ext in ['.docx', '.doc']:
                return FileReader._read_docx(file_path)
            elif ext in ['.txt', '.text']:
                return FileReader._read_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")
    
    @staticmethod
    def _read_pdf(file_path):
        """Read PDF file"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    @staticmethod
    def _read_docx(file_path):
        """Read DOCX/DOC file"""
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    @staticmethod
    def _read_txt(file_path):
        """Read TXT file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()