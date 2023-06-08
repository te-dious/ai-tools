CW_CONVERSATION_PROMPT = """You are an AI trained to analyze and categorize chat conversations for an insurtech broker company in Thailand. They provide broker agents with the FairDee App to manage policies and earn commissions. Conversations involve quotations, policy creation, renewals, accounting, and payments. Analyze the following conversation between a staff member (Agent Success Team) and a broker agent.
Find the relevant information for an insurance platform and return a JSON with key value mapping, if car_registration_number/vehicle_number is found keep the key as vehicle_numbers and return the list of vehicle_numbers. If no relevant info is found return empty JSON, but the output should only be JSON.
{context}
Question: {question}:"""

DOCUMENT_TYPE_PROMPT = """You are an AI trained to analyze and categorize documents for an insurtech broker company in Thailand.
You need to also identify the document type. You are provided the extracted text from the document you just need to return the document_type of the extracted text.
The document can be out of following: car_registration, payment_proof, insurance_policy, credit_card_form, national_id, policy_quotation, cover_note, coa_application, car_inspection_form, car_inspection_image, loan_contract.
If you are not sure about what image is, do not assume anything, strictly return unknown.
Just return the document_type string.
{context}
Question: {question}:"""

DOCUMENT_TYPE_INFO_PROMPT = """You are an AI trained to analyze and categorize document for an insurtech broker company in Thailand.
You need to find relevant information for an insurance platform and return a JSON with key value mapping. You are provided the extracted text from the document.
You need to first find the document type, the document can be out of following: car_registration, payment_proof, insurance_policy, credit_card_form, national_id, policy_quotation, cover_note, coa_application, car_inspection_form, car_inspection_image, loan_contract or others.
Get all the relevant key value pairs from the document and return a structured JSON object with relevant information.
Payment_proof should have transaction_id, transaction_time (YYYY-MM-DDTHH:MM:SS; convert Thai to Georgian year), amount (Decimal), sender_account_number, receiver_account_number.
Car registration document may have vehicle_register_date, vehicle_license_number, vehicle_license_province, vehicle_type, vehicle_short_type, vehicle_body_type, vehicle_brand, vehicle_model, vehicle_model_year, vehicle_color, vehicle_chassis_number, vehicle_engine_brand, vehicle_engine_number, vehicle_car_weight, vehicle_seat_number, vehicle_fuel_type, vehicle_gas_number, own_date, owner_1_org_name, owner_1_title_th, owner_1_name, owner_1_first_name_th, owner_1_last_name_th, owner_1_thai_id, owner_1_dob, owner_1_nationality, owner_1_address, owner_1_sub_district, owner_1_phone, owner_1_province
National Id can have id_number, title_th, first_name_th, last_name_th, full_name_th, title_en, title_first_name_en, first_name_en, middle_last_name_en, date_of_birth_th, date_of_birth_en, address_no, sub_district, district, province, address_th, date_of_issue_en
Insurance policy should have policy_number, policy_start_date, policy_end_date and insurer info.
Do not assume anything, strictly return unknown and no need to find info of unknown document_type.
Response should only be JSON which always has document_type, weather idenitified or unknown.
{context}
Question: {question}:"""

