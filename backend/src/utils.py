import logging
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import re
import json
from dotenv import load_dotenv, find_dotenv
import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer, util
import random
import pronouncing
import csv
from g2p_en import G2p
import nltk
nltk.download('averaged_perceptron_tagger_eng')
g2p = G2p()

os.environ["TORCHDYNAMO_DISABLE"] = "1"

logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())

HF_TOKEN = os.environ.get("HF_API_KEY")

device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info({"event": "device.detected", "device": device})

model_id = "google/gemma-2-2b-it"
logger.info({"event": "model.loading.start", "model_id": model_id})
tokenizer = AutoTokenizer.from_pretrained(model_id, token=HF_TOKEN)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    token=HF_TOKEN,
    torch_dtype=torch.float16,
    device_map="auto"
)
logger.info({"event": "model.loading.done", "model_id": model_id})

# Detect device again for sentence transformers
device = 'cuda' if torch.cuda.is_available() else 'cpu'

logger.info({"event": "embedder.loading.start", "name": "all-MiniLM-L12-v2", "device": device})
model_vdb = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2', device=device)
logger.info({"event": "embedder.loading.done"})

# Load FAISS index
logger.info({"event": "faiss.index.load.start", "path": "VDB/category_index.faiss"})
index = faiss.read_index("VDB/category_index.faiss")
logger.info({"event": "faiss.index.load.done"})

# Load metadata
logger.info({"event": "metadata.load.start", "path": "VDB/metadata.pkl"})
with open("VDB/metadata.pkl", "rb") as f:
    metadata = pickle.load(f)
logger.info({"event": "metadata.load.done", "records": len(metadata)})



logger.info({"event": "embedder.loading.start", "name": "all-MiniLM-L12-v2", "device": device})
model_vdb_final = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2', device=device)
logger.info({"event": "embedder.loading.done"})

# Load FAISS index
logger.info({"event": "faiss.index.load.start", "path": "Final_VDB/category_index.faiss"})
index_final = faiss.read_index("Final_VDB/category_index.faiss")
logger.info({"event": "faiss.index.load.done"})

# Load metadata
logger.info({"event": "metadata.load.start", "path": "Final_VDB/metadata.pkl"})
with open("Final_VDB/metadata.pkl", "rb") as f:
    metadata_final = pickle.load(f)
logger.info({"event": "metadata.load.done", "records": len(metadata_final)})



with open("names.txt", "r") as file:
    retrived_domain_names_list = [line.strip() for line in file]
domain_name_set = set(retrived_domain_names_list)
logger.info({"event": "names.loaded", "count": len(domain_name_set)})

# ==== Load root words dictionary (only once) ====
def load_domain_dict(root_words_csv="Root_Words.csv"):
    logger.info({"event": "root_words.load.start", "path": root_words_csv})
    domain_dict = {}
    with open(root_words_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            domain_dict[row['name'].lower()] = row['Split_Words']
    logger.info({"event": "root_words.load.done", "count": len(domain_dict)})
    return domain_dict

domain_dict = load_domain_dict("Root_Words.csv")

def RAG(query, top_k=20):
    logger.info({"event": "rag.search.start", "query": query, "top_k": top_k})
    query_vec = model_vdb_final.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    distances, indices = index_final.search(query_vec, top_k)

    results_final = []
    for i, idx in enumerate(indices[0]):
        category = metadata_final[idx]['Category']
        domains = metadata_final[idx]['Domain Names']
        source= metadata_final[idx]['Source']
        similarity = round(distances[0][i], 4)
        results_final.append({
            "category": category,
            "domains": domains,
            "source": source,
            "similarity": similarity
        })

    # Log ALL retrieved categories, sources, and similarities
    logger.info({
        "event": "rag.retrieved_matches",
        "query": query,
        "matches": [
            {
                "category": r["category"],
                "source": r["source"],
                "names" : r["domains"],
                "similarity": r["similarity"]
            }
            for r in results_final
        ]
    })

    domain_set = set()
    for res in results_final:
        if res['similarity'] > 0.5:
            domain_set.update(res['domains'])

    unique_domains = list(domain_set)
    logger.info({"event": "rag.search.done", "unique_domains": len(unique_domains)})

    if len(unique_domains) < 10:
        return "No Domain name Suggestions, Please prepare domain names using your intuition"
    else:
        sampled_domains = unique_domains[:20]
        return ", ".join(sampled_domains)

def gemma(user_description: str, sample_domains: str) -> str:
    logger.info({"event": "llm.generate.start", "model": model_id, "desc_len": len(user_description)})
    input_text = f"""
        You are an expert domain name generator. Your task is to create domain name suggestions that closely match the user's input and follow the style and pattern of the sample domain names provided.

        User Input Description:
        "{user_description}"

        Sample Domain Names:
        {sample_domains}

        Instructions:
        Generate 10 to 15 domain names that fit the user's input description.
        The names should be short, easy to understand, creative, memorable, and relevant to the input.
        Use similar word structures and language style as the samples.
        Avoid overly long or complicated names; keep them concise and simple.
        Do not repeat exact sample names.
        Provide only the domain name suggestions without any domain extensions (like .com, .net, .lk).
        Provide the domain names in a numbered list .

        Suggested Domain Names:
"""
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=100)
    output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = [{"generated_text": output}]
    logger.info({"event": "llm.generate.done"})
    return response

def gemma_post_processing(output):
    logger.info({"event": "llm.postprocess.start"})
    text = output[0]['generated_text']
    suggested_text = text.split("Suggested Domain Names:")[-1]
    domain_names = re.findall(r'\d+\.\s*([A-Za-z0-9]+)', suggested_text)
    domain_names = list(dict.fromkeys(domain_names))
    logger.info({"event": "llm.postprocess.done", "count": len(domain_names)})
    return domain_names

def gemma_decsription(domain_name: str, prompt: str):
    logger.info({"event": "llm.desc.start", "domain": domain_name})
    template = f"""
        You are a branding and domain expert.Generate a Python dictionary in the following format.The meaning and structure of the domain name,An explanation of its root words or parts and how they were combined,Why it is a suitable and relevant choice for the prompt, it should describe how domain name suitable for the user requirements:
        Domain name: {domain_name}
        Prompt: {prompt}
        {{
            "domainName": "{domain_name}",
            "domainDescription": "...",  # a creative description using the prompt
            "relatedFields": [ ... ]     # 4 to 6 relevant fields
        }}

        output:
    """
    inputs = tokenizer(template, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=250)
    output = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = [{"generated_text": output}]
    logger.info({"event": "llm.desc.done"})
    return response[0]['generated_text'], domain_name

def gemma_preprocess(llm_output, domain_name):
    logger.info({"event": "llm.preprocess.start"})
    try:
        code_block_match = re.search(r'```(?:json|python)?\s*(\{[\s\S]*?\})\s*```', llm_output, re.IGNORECASE)
        if code_block_match:
            json_string = code_block_match.group(1)
        else:
            all_matches = re.findall(r'\{[\s\S]*?\}', llm_output)
            if not all_matches:
                raise ValueError("No JSON object found.")
            json_string = all_matches[-1]

        parsed_json = json.loads(json_string)
        logger.info({"event": "llm.preprocess.done", "ok": True})
        return parsed_json

    except Exception as e:
        logger.warning({"event": "llm.preprocess.failed", "error": str(e)})
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
    logger.info({"event": "availability.filtered", "input": len(generated_name_list), "available": len(available_name_list)})
    return available_name_list

def sort_domains_by_pronounceability(domains):
    def domain_score(name):
        words = re.sub('([a-z])([A-Z])', r'\1 \2', name).split()
        if not words:
            return 0.0

        def pronounceability_score(word):
            phones = pronouncing.phones_for_word(word.lower())
            if not phones:
                return 0.0
            phonemes = phones[0].split()
            num_vowels = sum(1 for p in phonemes if any(v in p for v in "AEIOU"))
            vowel_ratio = num_vowels / len(phonemes)
            vowel_score = 1 - abs(vowel_ratio - 0.4)
            score = (vowel_score + (1 / len(phonemes))) / 2
            return round(score, 3)

        return round(sum(pronounceability_score(w) for w in words) / len(words), 3)

    ranked = sorted(domains, key=domain_score, reverse=True)
    logger.info({"event": "pronounceability.sorted", "count": len(ranked)})
    return ranked

def extend_domains(domains):
    prefixes = ["Smart", "Pure", "Pro", "Star", "Bold"]
    suffixes = ["Spark", "Right", "Spire", "Verse"]

    extended = []
    for domain in domains:
        domain_cap = domain.capitalize()
        extended.append(domain_cap)
        for pre in prefixes:
            extended.append(pre + domain_cap)
        for suf in suffixes:
            extended.append(domain_cap + suf)
    result = extended[:15]
    logger.info({"event": "domains.extended", "input": len(domains), "output": len(result)})
    return result

def get_domain_scores(domains):
    results = []

    def pronounceability_score(word: str) -> float:
        """Return a pronounceability score between 0.0 and 1.0 for a word."""
        phones = pronouncing.phones_for_word(word.lower())
        if phones:
            phonemes = phones[0].split()
        else:
            phonemes = [p for p in g2p(word) if p.isalpha()]

        if not phonemes:
            return 0.0

        # Count vowels
        num_vowels = sum(1 for p in phonemes if any(v in p for v in "AEIOU"))
        vowel_ratio = num_vowels / len(phonemes)

        # Ideal vowel ratio ~0.4
        vowel_score = 1 - abs(vowel_ratio - 0.4)

        # Shorter words get a small boost
        length_boost = 1 / len(phonemes)

        score = (vowel_score + length_boost) / 2
        return round(score, 3)

    for name in domains:
        avg_score = pronounceability_score(name)
        results.append((name, avg_score))

    # Sort by score, highest first
    sorted_domains = sorted(results, key=lambda x: x[1], reverse=True)
    ranked = [domain for domain, score in sorted_domains]

    logger.info({"event": "domains.scored", "count": len(ranked)})
    return ranked

def generate_domain_suggestions(query, top_k=20):
    logger.info({"event": "suggestions.generate.start", "query": query})
    query_vec = model_vdb.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    distances, indices = index.search(query_vec, top_k)

    # domain_set = set()
    # for i, idx in enumerate(indices[0]):
    #     similarity = round(distances[0][i], 4)
    #     if similarity > 0.5:
    #         domain_set.update(metadata[idx]['Domain Names'])

    domain_list = []
    for i, idx in enumerate(indices[0]):
        similarity = round(distances[0][i], 4)
        if similarity > 0.5:
            for d in metadata[idx]['Domain Names']:
                if d not in domain_list:  # avoid duplicates
                    domain_list.append(d)

    unique_domains = domain_list.copy()
    if len(unique_domains) < 5:
        logger.info({"event": "suggestions.generate.done", "status": "too_few_domains"})
        return []

    sampled_domains = unique_domains[:10]
    logger.info({"event": "vdb_suggestions", "names":sampled_domains})
    first_words, second_words = [], []
    for name in sampled_domains:
        rootwords = domain_dict.get(name.lower())
        if rootwords:
            words = rootwords.split()
            if len(words) >= 1:
                first_words.append(words[0])
            if len(words) >= 2:
                second_words.append(words[1])

    first_words = list(set(first_words))[:10]
    second_words = list(set(second_words))[:10]
    combined_names = [f + s for f in first_words for s in second_words]
    combined_names = list(set(combined_names))

    query_embedding = model_vdb.encode(query, convert_to_tensor=True)
    domain_embeddings = model_vdb.encode(combined_names, convert_to_tensor=True)
    cosine_scores = util.pytorch_cos_sim(query_embedding, domain_embeddings)[0]

    sorted_names = [name for name, _ in sorted(
        zip(combined_names, cosine_scores.tolist()),
        key=lambda x: x[1],
        reverse=True
    )]

    result = sorted_names[:28]
    logger.info({"event": "suggestions.generate.done", "count": len(result)})
    return result

def extend_domain_list_shorting(domain_list, max_part_len=6):
    extended_list = domain_list.copy()

    for name in domain_list:
        # Split name into parts based on CamelCase
        parts = re.findall(r'[A-Z]?[a-z]+', name)
        
        # Skip if the name cannot be split (unsplittable)
        if len(parts) <= 1:
            continue
        
        new_parts = []

        for part in parts:
            if len(part) > max_part_len:
                # Get first syllable (adjusted)
                word = part.lower()
                pattern = r'[^aeiouy]*[aeiouy]+(?:[^aeiouy]*$|[^aeiouy](?=[^aeiouy]))?'
                syllables = re.findall(pattern, word)
                
                if not syllables:
                    first = word
                elif len(syllables) == 1:
                    first = syllables[0]
                else:
                    first, next_syl = syllables[0], syllables[1]
                    vowels = "aeiouy"
                    if len(first) > 2:
                        if next_syl[0] in vowels or next_syl[0] == first[-1]:
                            first += next_syl[0]
                    else:
                        if first[-1] == next_syl[0]:
                            first += next_syl[0]
                        else:
                            for ch in next_syl:
                                first += ch
                                if ch in vowels:
                                    break
                new_parts.append(first)
            else:
                new_parts.append(part.lower())
        
        short_name = "".join(p.capitalize() for p in new_parts)
        if short_name != name and short_name not in extended_list:
            extended_list.append(short_name)

    return extended_list

def remove_case_duplicates(lst):
    seen = set()
    result = []
    for item in lst:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)  # keep original casing of first
    return result
