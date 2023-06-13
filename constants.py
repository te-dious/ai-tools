CW_CONVERSATION_PROMPT ="""You are an AI trained to analyze and categorize chat conversations for an insurtech broker company in Thailand. FairDee (FD) is a Thai insurtech company that helps insurance agents in selling insurance policies and earning commissions. 
Today, FD's value proposition is to provide general insurance agents with a platform to access motor insurance quotations from 20+ insurers and also allow the agents to report the sale via FD to the insurers. FD is responsible for reporting the sale with insurers, dealing with the payment flow and also policy delivery.
Insurance agents can either chat with staff members for assistance during the buying process or use the online platform provided by the insurtech company. The insurance purchasing process involves obtaining a quote, selecting a plan, submitting required documents, reporting a sale of a policy by giving customer details, making a payment, issuing a policy, and completing the transaction when the policy is physically delivered. Agents can also request renewals for existing policies bought from the company before. In the Thai market, some manual processes may be involved, such as sending payment proof, paying premiums in installments (almost equivalent to a loan), requesting a physical car inspection, manually delivering the policy via postal service, endorsing an existing policy, or change of agent ( COA - switching from one broker to your company).
Analyze the following conversation between a staff member (Agent Success Team) and a broker agent mentioned within the triple quotes.
Find the relevant information for an insurance platform and return a JSON with key value mapping.
Also if car_registration_number/vehicle_number is found keep the key as vehicle_numbers and return the list of vehicle_numbers and others as key value pair.
Also find contact_number, client_first_name, client_last_name, province, district, sub_district, zip_code, national_id_number
If no relevant info is found return empty JSON, but the output should only be JSON.
{context}
Question: ```{question}:```"""

CW_CONVERSATION_TO_SD_PROMPT ="""You are an AI trained to analyze structured data from conversation for an insurtech broker company in Thailand. FairDee (FD) is a Thai insurtech company that helps insurance agents in selling insurance policies and earning commissions. 
Today, FD's value proposition is to provide general insurance agents with a platform to access motor insurance quotations from 20+ insurers and also allow the agents to report the sale via FD to the insurers. FD is responsible for reporting the sale with insurers, dealing with the payment flow and also policy delivery.
Insurance agents can either chat with staff members for assistance during the buying process or use the online platform provided by the insurtech company. The insurance purchasing process involves obtaining a quote, selecting a plan, submitting required documents, reporting a sale of a policy by giving customer details, making a payment, issuing a policy, and completing the transaction when the policy is physically delivered. Agents can also request renewals for existing policies bought from the company before. In the Thai market, some manual processes may be involved, such as sending payment proof, paying premiums in installments (almost equivalent to a loan), requesting a physical car inspection, manually delivering the policy via postal service, endorsing an existing policy, or change of agent ( COA - switching from one broker to your company).
Analyze the following structured data mentioned within the triple quotes created from a conversation between a staff member (Agent Success Team) and a broker agent.
Fill all the relevant information for following keys in the following json format do not assume anything.
list of keys to be present in output: 'owner_salutation', 'owner_first_name', 'owner_last_name', 'vehicle_number', 'chassis_number', 'engine_number', 'registration_province', 'national_id', 'phone_number, 'policy_start_date', 'province', 'district', 'sub_district', 'zip_code', 'model_name', 'make_name', 'cc', 'registration_year', 'sub_model' and 'sum_insurered'
{context}
Conversation Data: ```{question}:```"""

DOCUMENT_IDENTIFICATION_PROMPT = """You are an AI trained to analyze and categorize documents for an insurtech broker company in Thailand.
You need to also identify the document type. You are provided the extracted text from the document you just need to return the document_type of the extracted text.
The document can be out of following: car_registration, payment_proof, policy_quotation, insurance_policy, credit_card_form, national_id, cover_note, coa_application, car_inspection_form, car_inspection_image, loan_contract.
If you are not sure about what image is, do not assume anything, strictly return unknown.
Just return the document_type string.
{context}
Question: {question}:"""

DOCUMENT_PP_IDENTIFICATION_PROMPT = """You are an AI trained to analyze and categorize document for an insurtech broker company in Thailand.
You are provided the extracted text from the payment proof document.
Get all the relevant key value pairs from the document and return a structured JSON object with relevant information.
Payment_proof should have transaction_id, transaction_time (YYYY-MM-DDTHH:MM:SS; convert Thai to Georgian year, for example if thai year is 66 georgian year will be 2023, if thai year is 2565 georgian year will be 2022), amount (Decimal), sender_account_number, receiver_account_number.
Do not assume anything, strictly return unknown.
{context}
Question: {question}:"""

DOCUMENT_TYPE_INFO_PROMPT = """You are an AI trained to analyze and categorize document for an insurtech broker company in Thailand.
You are provided the extracted text from the document with the given document_type.
You need to find relevant information for an insurance platform and return a JSON with key value mapping.
Get all the relevant key value pairs from the document and return a structured JSON object with relevant information.
Do not assume anything, strictly return empty dictionary and no need to find info of unknown document_type.
Response should strictly only be JSON.
{context}
Question: {question}:"""
