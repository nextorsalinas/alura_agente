import os
import tempfile
from pathlib import Path
import pandas as pd
from typing import List, Tuple, Dict, Any
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


def load_environment_config() -> None:
    """Carga variables desde .env si están disponibles."""
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        load_dotenv(override=True)


class DocumentAgentEngine:
    def __init__(self, api_key: str = None):
        load_environment_config()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("No se encontró la GEMINI_API_KEY. Por favor configura tu API key en las variables de entorno o la interfaz.")
        
        # Set environment variables for LangChain Google integration
        os.environ["GEMINI_API_KEY"] = self.api_key
        os.environ["GOOGLE_API_KEY"] = self.api_key
        
        # Fallback de modelos de Embeddings para garantizar compatibilidad
        embedding_models = [
            "models/gemini-embedding-001",
            "models/gemini-embedding-2-preview",
            "models/text-embedding-004",
            "models/embedding-001"
        ]
        
        self.embeddings = None
        for model_name in embedding_models:
            try:
                emb = GoogleGenerativeAIEmbeddings(
                    model=model_name,
                    google_api_key=self.api_key
                )
                # Probar vectorización simple para verificar disponibilidad
                emb.embed_query("test_check")
                self.embeddings = emb
                break
            except Exception as e:
                continue
                
        if not self.embeddings:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=self.api_key
            )

        # Fallback de modelos LLM para respuestas
        llm_models = [
            "models/gemini-2.5-flash",
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-lite",
            "models/gemini-flash-latest"
        ]
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash",
            temperature=0.2,
            google_api_key=self.api_key
        )

        self.vector_store = None
        self.raw_dataframe = None

    def load_and_index_document(self, file_path: str, filename: str) -> str:
        """Lee el documento (PDF, CSV, TXT, MD) y crea el índice vectorial."""
        ext = filename.lower().split('.')[-1]
        documents = []

        if ext == 'pdf':
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        elif ext in ['txt', 'md']:
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
        elif ext == 'csv':
            self.raw_dataframe = pd.read_csv(file_path)
            from langchain_core.documents import Document
            documents = []
            rows_buffer = []
            # Agrupación dinámica: garantiza máximo 30 fragmentos para no superar el límite de 100 RPM de Gemini
            total_rows = len(self.raw_dataframe)
            chunk_batch_size = max(25, int(total_rows / 30))
            
            for idx, row in self.raw_dataframe.iterrows():
                row_str = f"Fila {idx + 1}: " + ", ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                rows_buffer.append(row_str)
                if len(rows_buffer) >= chunk_batch_size:
                    documents.append(Document(page_content="\n".join(rows_buffer), metadata={"source": filename, "start_row": idx - len(rows_buffer) + 2, "end_row": idx + 1}))
                    rows_buffer = []
            if rows_buffer:
                documents.append(Document(page_content="\n".join(rows_buffer), metadata={"source": filename}))
        elif ext in ['xlsx', 'xls']:
            from langchain_core.documents import Document
            excel_file = pd.ExcelFile(file_path)
            self.raw_dataframe = pd.read_excel(file_path)
            documents = []
            total_rows = len(self.raw_dataframe)
            chunk_batch_size = max(25, int(total_rows / 30))
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                rows_buffer = []
                for idx, row in df.iterrows():
                    row_str = f"Hoja: {sheet_name} | Fila {idx + 1}: " + ", ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                    rows_buffer.append(row_str)
                    if len(rows_buffer) >= chunk_batch_size:
                        documents.append(Document(page_content="\n".join(rows_buffer), metadata={"source": filename, "sheet": sheet_name}))
                        rows_buffer = []
                if rows_buffer:
                    documents.append(Document(page_content="\n".join(rows_buffer), metadata={"source": filename, "sheet": sheet_name}))
        else:
            raise ValueError(f"Formato no soportado: .{ext}. Usa PDF, CSV, TXT, MD, XLSX o XLS.")

        # Chunking documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)

        # Create FAISS Vector Index with retry for rate limits
        import time
        for attempt in range(3):
            try:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
                break
            except Exception as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    time.sleep(10)
                else:
                    raise e
        return f"Documento '{filename}' ({len(self.raw_dataframe) if self.raw_dataframe is not None else 0} filas) procesado exitosamente. {len(chunks)} fragmentos indexados."

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Responde la pregunta basándose en el contenido del documento indexado."""
        if not self.vector_store:
            return {"answer": "No hay ningún documento cargado. Por favor sube un archivo primero.", "sources": []}

        # Retrieval of top k relevant chunks
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(question)

        context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])
        sources = [doc.page_content for doc in docs]

        # Inyectar resumen estructural de Pandas para CSVs/Excel masivos
        if self.raw_dataframe is not None and not self.raw_dataframe.empty:
            summary_info = f"ESTRUCTURA DE TABLA DATOS (Total filas: {len(self.raw_dataframe)}, Columnas: {list(self.raw_dataframe.columns)})\n"
            summary_info += f"Muestra inicial de filas:\n{self.raw_dataframe.head(5).to_string()}\n\n---\n\n"
            context_text = summary_info + context_text

        prompt_template = """Eres 'Alura Agente', un asistente inteligente corporativo de alta precisión.
Tu objetivo es responder a las preguntas de los colaboradores basándote ÚNICAMENTE en la siguiente información de contexto extraída de los documentos internos de la empresa.

Contexto del documento:
{context}

Pregunta del usuario: {question}

Instrucciones:
1. Responde de manera clara, concisa, estructurada y profesional en lenguaje natural.
2. Si la respuesta exacta se encuentra en el contexto (por ejemplo datos numéricos, fechas, lenguajes de programación, nombres), sé preciso.
3. Si el contexto NO contiene la información necesaria para responder la pregunta, indica amablemente que el documento proporcionado no contiene dicha información. No inventes respuestas.

Respuesta:"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()

        response = chain.invoke({"context": context_text, "question": question})

        return {
            "answer": response,
            "sources": sources
        }
