import os
import tempfile
import pandas as pd
from typing import List, Tuple, Dict, Any
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

class DocumentAgentEngine:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("No se encontró la GEMINI_API_KEY. Por favor configura tu API key en las variables de entorno o la interfaz.")
        
        # Set environment variables for LangChain Google integration
        os.environ["GEMINI_API_KEY"] = self.api_key
        os.environ["GOOGLE_API_KEY"] = self.api_key
        
        # Initialize Embeddings & LLM
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=self.api_key
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
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
            # Store dataframe for structured tabular queries if needed
            self.raw_dataframe = pd.read_csv(file_path)
            loader = CSVLoader(file_path, encoding='utf-8')
            documents = loader.load()
        else:
            raise ValueError(f"Formato no soportado: .{ext}. Usa PDF, CSV, TXT o MD.")

        # Chunking documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150
        )
        chunks = text_splitter.split_documents(documents)

        # Create FAISS Vector Index
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        return f"Documento '{filename}' procesado exitosamente. {len(chunks)} fragmentos indexados."

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Responde la pregunta basándose en el contenido del documento indexado."""
        if not self.vector_store:
            return {"answer": "No hay ningún documento cargado. Por favor sube un archivo primero.", "sources": []}

        # Retrieval of top k relevant chunks
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 4})
        docs = retriever.invoke(question)

        context_text = "\n\n---\n\n".join([doc.page_content for doc in docs])
        sources = [doc.page_content for doc in docs]

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
