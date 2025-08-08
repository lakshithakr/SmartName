from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import re
import json
from dotenv import load_dotenv,find_dotenv
import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import random

load_dotenv(find_dotenv())

HF_TOKEN = os.environ.get("HF_API_KEY")

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

model_id = "google/gemma-2-2b-it"
tokenizer = AutoTokenizer.from_pretrained(model_id,token=HF_TOKEN)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    #torch_dtype=torch.bfloat16,
    token=HF_TOKEN,
    torch_dtype=torch.float16,
    device_map="auto"  # Uses your GPU automatically
)

# Detect device
device = 'cuda' if torch.cuda.is_available() else 'cpu'
#print(f"Using device: {device}")

# Load model
model_vdb = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2', device=device)

# Load FAISS index
index = faiss.read_index("VDB/category_index.faiss")

# Move index to GPU if available
# if device == 'cuda':
#     res = faiss.StandardGpuResources()
#     index = faiss.index_cpu_to_gpu(res, 0, index)
#     print("FAISS index moved to GPU")

# Load metadata
with open("VDB/metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

with open("names.txt", "r") as file:
    retrived_domain_names_list = [line.strip() for line in file]
domain_name_set = set(retrived_domain_names_list)

def RAG(query, top_k=20):
    # Encode and normalize query
    query_vec = model_vdb.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    
    # Perform cosine similarity search
    distances, indices = index.search(query_vec, top_k)

    # Compile results
    results = []
    for i, idx in enumerate(indices[0]):
        category = metadata[idx]['Category']
        domains = metadata[idx]['Domain Names']
        similarity = round(distances[0][i], 4)
        results.append({
            "category": category,
            "domains": domains,
            "similarity": similarity
        })

    domain_set = set()
    for res in results:
        if res['similarity'] > 0.5:
            domain_set.update(res['domains'])

    unique_domains = list(domain_set)

    if  len(unique_domains)<10:
        return "No Domain name Suggestions, Please prepare domain names using your intution"
    else:
        # sampled_domains = random.sample(unique_domains, min(20, len(unique_domains)))
        sampled_domains = unique_domains[:20]
        return ", ".join(sampled_domains)

def gemma(user_description: str, sample_domains: str) -> str:
    input_text=f"""
        You are an expert domain name generator. Your task is to create domain name suggestions that closely match the user's input and follow the style and pattern of the sample domain names provided.

        User Input Description:
        "{user_description}"

        Sample Domain Names:
        {sample_domains}

        Instructions:
        - Generate 10 to 15 domain names that fit the user's input description.
        - The names should be short, easy to understand, creative, memorable, and relevant to the input.
        - Use similar word structures and language style as the samples.
        - Avoid overly long or complicated names; keep them concise and simple.
        - Do not repeat exact sample names.
        - Provide only the domain name suggestions without any domain extensions (like .com, .net, .lk).
        - Provide the domain names in a numbered list .

        Suggested Domain Names:
"""
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

    outputs = model.generate(**inputs, max_new_tokens=100)
    output=tokenizer.decode(outputs[0], skip_special_tokens=True)
    #print(response.json())
    response = [{"generated_text": output}]
    return response

def gemma_post_processing(output):
    text = output[0]['generated_text']
    suggested_text = text.split("Suggested Domain Names:")[-1]
    domain_names = re.findall(r'\d+\.\s*([A-Za-z0-9]+)', suggested_text)
    domain_names = list(dict.fromkeys(domain_names))
    return domain_names

def gemma_decsription(domain_name: str, prompt: str):
    template = f"""
        You are a branding and domain expert. Generate a Python dictionary in the following format. The meaning and structure of the domain name, An explanation of its root words or parts and how they were combined, Why it is a suitable and relevant choice for the prompt, it should describe how domain name suitable for the user requirements:
        Domain name: {domain_name}
        Prompt: {prompt}
        {{
            "domainName": "{domain_name}",
            "domainDescription": "...",  # a creative description using the prompt (2-3 sentences)
            "relatedFields": [ ... ]     # 4 to 6 relevant fields
        }}

        output:
    """
    inputs = tokenizer(template , return_tensors="pt").to(model.device)

    outputs = model.generate(**inputs, max_new_tokens=250)
    output=tokenizer.decode(outputs[0], skip_special_tokens=True)
    #print(response.json())
    response = [{"generated_text": output}]
    return response[0]['generated_text'],domain_name

def gemma_preprocess(llm_output,domain_name):
    try:
        # Try to find a code block with ```json or ```python
        code_block_match = re.search(r'```(?:json|python)?\s*(\{[\s\S]*?\})\s*```', llm_output, re.IGNORECASE)

        if code_block_match:
            json_string = code_block_match.group(1)
        else:
            # Fallback: try to find the last JSON-like block in the output
            all_matches = re.findall(r'\{[\s\S]*?\}', llm_output)
            if not all_matches:
                raise ValueError("No JSON object found.")
            json_string = all_matches[-1]  # Use the last one assuming it's the actual output

        # Try to parse the JSON
        parsed_json = json.loads(json_string)
        return parsed_json

    except Exception:
        return {
            "domainName": f"{domain_name}.lk",
            "domainDescription": "Failed to parse response from LLM.",
            "relatedFields": []
        }

def is_domain_names_available(generated_name_list):
    available_name_list = []
    for name in generated_name_list:
        temp = name.lower().split(".")[0]
        if temp not in domain_name_set:
            available_name_list.append(name)
    return available_name_list