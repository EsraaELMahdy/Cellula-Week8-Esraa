from langchain_text_splitters import RecursiveCharacterTextSplitter

from retriever.cleaner import clean_text

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)


def chunk_pages(pages: list[dict]) -> list[dict]:
    
    chunks = []
    for page in pages:
        text = clean_text(page["text"])
        if not text:
            continue
        for i, piece in enumerate(_splitter.split_text(text)):
            chunks.append({
                "document": page["document"],
                "page": page["page"],
                "chunk_id": f'{page["document"]}-p{page["page"]}-c{i}',
                "text": piece,
            })
    return chunks