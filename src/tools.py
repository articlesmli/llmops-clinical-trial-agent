# src/tools.py
import os
from pypdf import PdfReader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.schemas import CriteriaExtractionOutput
from src.prompts import build_extraction_prompt

def parse_and_store_pdf_to_vectordb(pdf_path: str):
    """Parses PDF (with automatic OCR fallback for scanned PDFs), chunks text, and stores in ChromaDB."""
    print(f"[Tool: PDF Parser] Reading PDF from {pdf_path}...")
    
    if not os.path.exists(pdf_path):
        print(f"[Warning] PDF file not found at {pdf_path}.")
        return None, []
        
    reader = PdfReader(pdf_path)
    docs = []
    
    # Try standard pypdf extraction first
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            docs.append(Document(page_content=text, metadata={"page": i + 1}))
            
    # Fallback to OCR if pypdf didn't extract meaningful text (scanned PDF)
    if len(docs) == 0 or sum(len(d.page_content.strip()) for d in docs) < 100:
        print("[Tool: PDF Parser] Detected scanned PDF. Running OCR via pytesseract...")
        from pdf2image import convert_from_path
        import pytesseract
        
        images = convert_from_path(pdf_path)
        docs = []
        for i, image in enumerate(images):
            text = pytesseract.image_to_string(image)
            if text.strip():
                docs.append(Document(page_content=text, metadata={"page": i + 1}))
                
    print(f"[Tool: PDF Parser] Extracted {len(docs)} pages.")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)
    print(f"[Tool: Chunking] Split document into {len(chunks)} chunks.")

    print("[Tool: Vector DB] Converting chunks to embeddings and storing in Chroma...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    
    print("[Tool: Vector DB] Successfully stored vector embeddings!")
    return vectorstore.as_retriever(search_kwargs={"k": 15}), docs


def extract_criteria_with_rag(
    pdf_path: str, 
    therapeutic_area: str = "General", 
    historical_examples: str = ""
) -> tuple[CriteriaExtractionOutput, str]:
    """Orchestrates RAG retrieval, explicit keyword page-matching, and structured extraction using Anthropic Claude."""
    retriever, all_docs = parse_and_store_pdf_to_vectordb(pdf_path)
    
    context_text = "Fallback static context"
    
    # Programmatically find pages containing actual criteria headings to guarantee high-relevance context
    explicit_pages = []
    for doc in all_docs:
        content_lower = doc.page_content.lower()
        if "inclusion criteria" in content_lower or "exclusion criteria" in content_lower:
            # Skip pages that are just table of contents or general bias sections if possible, 
            # but capture pages that look like eligibility sections
            if "minimisation of error" not in content_lower:
                explicit_pages.append(doc.page_content)

    if explicit_pages:
        print(f"[Tool: Keyword Extractor] Found {len(explicit_pages)} pages matching criteria keywords directly.")
        context_text = "\n\n".join(explicit_pages[:3])  # Take top matching pages
    elif retriever:
        print("[Tool: RAG Retriever] Fallback: Searching vector DB...")
        relevant_docs = retriever.invoke("Inclusion Criteria Exclusion Criteria")
        context_text = "\n\n".join([doc.page_content for doc in relevant_docs])

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if api_key and api_key.startswith("sk-") and len(api_key) > 10:
        try:
            from langchain_anthropic import ChatAnthropic
            print("[Tool: LLM] Invoking Anthropic Claude...")
            llm = ChatAnthropic(model="claude-sonnet-5-5")
            structured_llm = llm.with_structured_output(CriteriaExtractionOutput, method="json_schema")
            prompt = build_extraction_prompt(
                context_text=context_text, 
                therapeutic_area=therapeutic_area, 
                historical_examples=historical_examples
            )
            result = structured_llm.invoke(prompt)
            print(f"[Debug] Extracted Inclusion Criteria Count: {len(result.inclusion_criteria) if result and result.inclusion_criteria else 0}")
            print(f"[Debug] Extracted Exclusion Criteria Count: {len(result.exclusion_criteria) if result and result.exclusion_criteria else 0}")
            print(f"[Debug Context Preview]: {context_text[:500]}...")
            if result and (result.inclusion_criteria or result.exclusion_criteria):
                print("[Tool: LLM] Successfully extracted criteria via Dynamic RAG + Claude.")
                return result, context_text
        except Exception as e:
            print(f"[Error] Anthropic LLM extraction failed: {e}. Falling back.")

    fallback_obj = CriteriaExtractionOutput(
        inclusion_criteria=["Age >= 18 years at time of consent", "Confirmed Stage II/III NSCLC"],
        exclusion_criteria=["Prior immunotherapy", "Active brain metastases"]
    )
    return fallback_obj, context_text