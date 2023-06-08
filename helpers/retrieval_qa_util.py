from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

class RetrievalQAUtil:
    def __init__(self, retriever, model_name='gpt-3.5-turbo', prompt_template=None, chain_type="stuff"):
        prompt = None
        if prompt_template:
            prompt = PromptTemplate(
                template=prompt_template, input_variables=["context", "question"]
            )

        self.prompt = prompt
        self.chain_type = chain_type
        self.model_name = model_name
        self.retriever = retriever

    def create_qa_chain(self):
        llm = ChatOpenAI(model_name=self.model_name, openai_api_key=OPENAI_API_KEY)
        qa = RetrievalQA.from_llm(llm=llm, retriever=self.retriever, prompt=self.prompt)
        return qa
