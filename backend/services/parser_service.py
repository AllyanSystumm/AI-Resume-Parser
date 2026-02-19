import io
import PyPDF2
from docx import Document

class ParserService:
    @staticmethod
    async def parse_pdf(file_content: bytes) -> str:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text

    @staticmethod
    async def parse_docx(file_content: bytes) -> str:
        doc = Document(io.BytesIO(file_content))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text

    async def extract_text(self, filename: str, content: bytes) -> str:
        if filename.lower().endswith(".pdf"):
            return await self.parse_pdf(content)
        elif filename.lower().endswith(".docx"):
            return await self.parse_docx(content)
        else:
            raise ValueError("Unsupported file format. Please upload PDF or DOCX.")
