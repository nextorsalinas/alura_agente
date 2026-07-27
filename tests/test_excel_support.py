import os
import tempfile
import unittest

import pandas as pd

import rag_engine


class DummyEmbeddings:
    def embed_query(self, text):
        return [0.1, 0.2, 0.3]

    def embed_documents(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


class DummyLLM:
    pass


class ExcelSupportTests(unittest.TestCase):
    def test_xlsx_is_supported(self):
        original_embeddings = rag_engine.GoogleGenerativeAIEmbeddings
        original_llm = rag_engine.ChatGoogleGenerativeAI
        try:
            rag_engine.GoogleGenerativeAIEmbeddings = lambda **kwargs: DummyEmbeddings()
            rag_engine.ChatGoogleGenerativeAI = lambda **kwargs: DummyLLM()

            engine = rag_engine.DocumentAgentEngine(api_key="test-key")

            with tempfile.TemporaryDirectory() as tmp_dir:
                xlsx_path = os.path.join(tmp_dir, "demo.xlsx")
                df = pd.DataFrame({"Producto": ["A", "B"], "Ventas": [100, 200]})
                df.to_excel(xlsx_path, index=False)

                result = engine.load_and_index_document(xlsx_path, "demo.xlsx")

                self.assertIn("procesado exitosamente", result)
                self.assertIsNotNone(engine.vector_store)
        finally:
            rag_engine.GoogleGenerativeAIEmbeddings = original_embeddings
            rag_engine.ChatGoogleGenerativeAI = original_llm


if __name__ == "__main__":
    unittest.main()
