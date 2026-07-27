import os
import tempfile
import shutil
import pandas as pd
import rag_engine

class DummyEmbeddings:
    def embed_query(self, text):
        return [0.1, 0.2, 0.3]

    def embed_documents(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

class DummyLLM:
    pass

rag_engine.GoogleGenerativeAIEmbeddings = lambda **kwargs: DummyEmbeddings()
rag_engine.ChatGoogleGenerativeAI = lambda **kwargs: DummyLLM()
engine = rag_engine.DocumentAgentEngine(api_key='test-key')
tmpdir = tempfile.mkdtemp()
path = os.path.join(tmpdir, 'demo.xlsx')
pd.DataFrame({'Producto':['A','B'],'Ventas':[100,200]}).to_excel(path, index=False)
print('created', path)
print(engine.load_and_index_document(path, 'demo.xlsx'))
shutil.rmtree(tmpdir, ignore_errors=True)
