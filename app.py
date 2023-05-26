from flask import Flask, request, jsonify
from chroma_db_util import ChromaDBUtil
from retrieval_qa_util import RetrievalQAUtil

app = Flask(__name__)


@app.route('/create_db', methods=['POST'])
def create_db():
    # docs is list of files in text format
    data = request.json
    db_util = ChromaDBUtil()
    db_util.create_db(data['docs'], data['collection_name'])
    return jsonify({'message': 'Database created successfully'})


@app.route('/ask_qa_chain', methods=['POST'])
def ask_qa_chain():
    data = request.json
    collection_name = data.pop('collection_name', None)
    if collection_name:
        db_utils = ChromaDBUtil()
        db = db_utils.get_db(collection_name)
        retriever = db.as_retriever(search_type="similarity", search_kwargs={"k":1})
        data["retriever"] = retriever
    message = data.pop("message")

    qa_util = RetrievalQAUtil(**data)
    qa_chain = qa_util.create_qa_chain()
    op = qa_chain(message)
    print(op)

    return jsonify({'message': op})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
