from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

OPENAI_API_KEY = "sk-"

class RetrievalQAUtil:
    def __init__(self, model_name='gpt-3.5-turbo', prompt=None, chain_type="stuff", retriever=None):
        self.prompt = prompt
        self.chain_type = chain_type
        self.model_name = model_name
        self.retriever = retriever

    def create_qa_chain(self):
        chain_type_kwargs = {}
        if self.prompt:
            chain_type_kwargs = {"prompt": self.prompt}
        llm = ChatOpenAI(model_name=self.model_name, openai_api_key=OPENAI_API_KEY)
        qa = RetrievalQA.from_llm(llm=llm, retriever=self.retriever, prompt=self.prompt)
        return qa
