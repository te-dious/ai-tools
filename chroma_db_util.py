import os
from chromadb import Client
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings

OPENAI_API_KEY = "sk-"

class ChromaDBUtil:
    def __init__(self, db_path=None):
        self.db_path = os.path.join(os.path.dirname(__file__), "indexes")
        self.settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.db_path)
        self.client = Client(self.settings)

    def create_db(self, docs, collection_name):
        client_settings = self.settings
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            client_settings=client_settings,
            persist_directory=f"{self.db_path}",
        )
        text_splitter = CharacterTextSplitter(chunk_size=1600, chunk_overlap=0)

        for doc in docs:
            texts = text_splitter.split_text(doc)

            vectorstore.add_texts(texts=texts, embedding=embeddings)
            vectorstore.persist()
            print(vectorstore)


    def get_db(self, collection_name):
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

        db = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            client_settings=self.settings,
            persist_directory=f"{self.db_path}",
        )
        return db