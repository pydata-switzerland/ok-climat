import requests
import json
import argparse
from pathlib import Path
import time

def chunk_text(text, chunk_size=2000, overlap=200):
    """
    Split text into overlapping chunks to avoid losing context.
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Size of each chunk in characters
        overlap (int): Overlap between chunks in characters
    
    Returns:
        list: List of text chunks
    """
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
    return chunks


def process_chunk_with_ollama(chunk, chunk_num, total_chunks, url_pdf, canton, subsidy_type):
    """
    Send a single chunk to Ollama and get response.
    """
    # Simplify: just use the subsidy type as-is, don't expand it
    prompt = f"""You are extracting information from a PDF document about energy subsidies.
Document source: {url_pdf}
Canton: {canton}
Looking for subsidy type: {subsidy_type}

Read this excerpt and extract ONLY complete sections (headers + full content) that directly mention:
- "{subsidy_type}" or related terms (Photovoltaic, PV, solar panels for electricity)
- "Thermische Solaranlagen" or thermal solar systems
- Section headers that clearly relate to solar energy subsidies

Extract the EXACT text, including headers and all conditions/requirements. Do NOT summarize.
If no matching section exists, respond: "NO_MATCH"

Document excerpt (chunk {chunk_num} of {total_chunks}):
---
{chunk}
---"""

    try:
        time_start = time.time()
        print(f"  Processing chunk {chunk_num}/{total_chunks}...", end=" ", flush=True)
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'phi',
                'prompt': prompt,
                'stream': False
            },
            timeout=600
        )
        
        if response.status_code != 200:
            print(f"✗ Error {response.status_code}")
            return None
        
        result = response.json()['response'].strip()
        time_stop = time.time()
        print(f"✓ Done in {int(time_stop - time_start)} s") 
        return result if result != "NO_MATCH" else None
        
    except requests.exceptions.Timeout:
        print("✗ Timeout")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def summarize_text_with_mistral(text_file_path):
    """
    Read a text file, chunk it, and process each chunk with Ollama.
    """
    try:
        file_path = Path(text_file_path)
        if not file_path.exists():
            print(f"✗ File not found: {text_file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        print(f"✓ Loaded file: {file_path.name}")
        print(f"  File size: {len(text_content)} characters\n")

        # Extract metadata - keep subsidy_type simple
        language = "unknown"
        canton = "unknown"
        subsidy_type = "unknown"
        url_pdf = "unknown"
        
        for line in text_content.split('\n')[:20]:
            if "Language:" in line:
                language = line.split("Language:")[1].strip().split('\n')[0]
            if "PDF URL:" in line:
                url_pdf = line.split("PDF URL:")[1].strip().split('\n')[0]
            if "Canton:" in line:
                canton = line.split("Canton:")[1].strip().split('\n')[0]
            if "Subsidy Type:" in line:
                subsidy_type = line.split("Subsidy Type:")[1].strip().split('\n')[0]
        
        print(f"✓ Extracted metadata:")
        print(f"  Language: {language}")
        print(f"  Canton: {canton}")
        print(f"  Subsidy Type: {subsidy_type}\n")

        if "TEXT CONTENT" in text_content:
            text_content = text_content.split("TEXT CONTENT", 1)[1]
            text_content = text_content.split("=" * 10, 1)[1].strip()

        print(f"Chunking text into 2000-character pieces...")
        chunks = chunk_text(text_content, chunk_size=2000, overlap=200)
        print(f"✓ Created {len(chunks)} chunks\n")
        
        print("Processing chunks with Ollama:")
        print(f"(Timeout: 600 seconds per chunk)\n")
        
        all_results = []
        for i, chunk in enumerate(chunks, 1):
            result = process_chunk_with_ollama(
                chunk, i, len(chunks), url_pdf, canton, subsidy_type
            )
            if result:
                all_results.append(result)
        
        print("\n" + "=" * 60)
        print("EXTRACTED SECTIONS")
        print("=" * 60 + "\n")
        
        if not all_results:
            print("⚠️ No relevant sections found.")
            return None
        
        # Save all_results to JSON file
        output_file = file_path.stem + "_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved results to: {output_file}\n")
        
        aggregated = ""
        for i, result in enumerate(all_results, 1):
            aggregated += f"{result}\n\n"
        
        print(aggregated)
        print("=" * 60)
        
        return aggregated
        
    except requests.exceptions.ConnectionError:
        print("✗ Connection refused. Is Ollama running? (ollama serve)")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Summarize a text file using Ollama by chunking and processing sequentially"
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the text file to summarize (e.g., ./texts/ktzh_foerderprogramm_2026.txt)"
    )
    
    args = parser.parse_args()
    
    summarize_text_with_mistral(args.file_path)



# def summarize_text_with_LLM(text_file_path):
#     """
#     Read a text file and ask LLM to summarize it.
    
#     Args:
#         text_file_path (str): Path to the text file to summarize
    
#     Returns:
#         str: LLM's summary, or None if failed
#     """
    
#     try:
#         # Read input text file
#         file_path = Path(text_file_path)
        
#         # Check if file exists
#         if not file_path.exists():
#             print(f"✗ File not found: {text_file_path}")
#             return None
        
#         # Read the text content (encoding utf-8 to handle special characters such as umlauts in german)
#         with open(file_path, 'r', encoding='utf-8') as f:
#             text_content = f.read()
        
#         # Basic info about the file
#         print(f"✓ Loaded file: {file_path.name}")
#         print(f"  File size: {len(text_content)} characters\n")

#         # Extract meta data from the text content
#         language = "unknown"
#         canton = "unknown"
#         subsidy_type = "unknown"
#         url_pdf = "unknown"
        
#         # Parse metadata from the header
#         for line in text_content.split('\n')[:20]:  # Check first 20 lines
#             if "Language:" in line:
#                 language = line.split("Language:")[1].strip().split('\n')[0]
#             if "URL PDF:" in line:
#                 url_pdf = line.split("URL PDF:")[1].strip().split('\n')[0]
#             if "Canton:" in line:
#                 canton = line.split("Canton:")[1].strip().split('\n')[0]
#             if "Subsidy Type:" in line:
#                 subsidy_type = line.split("Subsidy Type:")[1].strip().split('\n')[0]
#                 if "PV" in subsidy_type:
#                     subsidy_type = "'PV', which stands for Photovoltaic, a type of solar energy system. This subsidy type covers two subtypes: (1) solar panels for energy production and (2) solar panels for termal heating. The subsidy provides financial support for the installation of these solar panels, helping to reduce the initial cost and encourage the adoption of renewable energy solutions." 

#         print(f"✓ Extracted metadata:")
#         print(f"  Language: {language}")
#         print(f"  Canton: {canton}")
#         print(f"  Subsidy Type: {subsidy_type}\n")

#         # Cut away metadata and keep only the main text content for summarization
#         if "TEXT CONTENT" in text_content:
#             # Split on the "TEXT CONTENT" section header
#             text_content = text_content.split("TEXT CONTENT", 1)[1]
#             # Remove the line of equals signs that follows
#             text_content = text_content.split("=" * 10, 1)[1].strip()
#         else:
#             print("⚠️ Warning: No 'TEXT CONTENT' separator found. Using entire text content for summarization.")

#         # Create prompt for LLM
#         prompt = f"""Please read this document that is written in either german, french or italian. Originally, this was a .pdf file obtained from {url_pdf}, 
#         but has now been transformed into a .txt file with the help of pdfplumber.open(pdf_path) and text = "\n".join([page.extract_text() or "" for page in pdf.pages]). 
#         It might contain information on subsidies provided by canton {canton}. Your objective is to identify if information related to a specific subsidy type is present. 
#         This specific subsidy type is referred to as {subsidy_type}.  

# Document text:
# ---
# {text_content[:5000]}  
# ---

# Return the sections of text that contain the relevant information on any of the subtypes of the desired subsidy type."""
        
#         print("✓ Prompt created for LLM:")
#         print("-" * 60)
#         print(prompt)
#         print("-" * 60 + "\n")
        
#         # Send to LLM
#         print("Sending to LLM for summarization...")
#         print("(This may take 2-5 minutes on 2018 MacBook)\n")
        
#         response = requests.post(
#             'http://localhost:11434/api/generate',
#             json={
#                 'model': 'neural-chat', # mistral
#                 'prompt': prompt,
#                 'stream': False
#             },
#             timeout=180
#         )
        
#         if response.status_code != 200:
#             print(f"✗ Error: Ollama returned {response.status_code}")
#             return None
        
#         # Extract summary
#         summary = response.json()['response'].strip()
        
#         print("=" * 60)
#         print("SUMMARY FROM LLM")
#         print("=" * 60)
#         print(summary)
#         print("=" * 60)
        
#         return summary
        
#     except requests.exceptions.ConnectionError:
#         print("✗ Connection refused. Is Ollama running? (ollama serve)")
#         return None
#     except requests.exceptions.Timeout:
#         print("✗ Request timed out (LLM is slow on 2018 MacBook)")
#         return None
#     except Exception as e:
#         print(f"✗ Error: {e}")
#         import traceback
#         traceback.print_exc()
#         return None


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         description="Summarize a text file using LLM"
#     )
#     parser.add_argument(
#         "file_path",
#         type=str,
#         help="Path to the text file to summarize (e.g., ./texts/ktzh_foerderprogramm_2026.txt)"
#     )
    
#     args = parser.parse_args()
    
#     summarize_text_with_LLM(args.file_path)







# import requests
# import json

# def test_ollama():
#     try:
#         print("Testing Ollama...")
        
# 		# Check if Ollama is running and list models
#         response = requests.get('http://localhost:11434/api/tags')
        
#         if response.status_code != 200:
#             print(f"✗ Error: {response.status_code}")
#             return
        
#         models = response.json()['models']
#         print(f"✓ Ollama running! Models: {[m['name'] for m in models]}\n")
        
#         if not models:
#             print("✗ No models. Run: ollama pull mistral")
#             return
        
#         print("Testing Mistral (this may take 30-60 seconds)...")
        
# 		# This is the prompt we are sending to Mistral. We want it to extract the amount, per unit cost, and unit from the given string and return it as JSON.
#         prompt = 'Extract as JSON: "CHF 2400 + 1000 per kWth, minimum 2 kW"\nReturn: {"amount": X, "per_unit": Y, "unit": "Z"}'
        
# 		# This is where we are configuring and sending the request with basic options.
# 		# Send generation request to Mistral with a long timeout
#         # Json dict is the data you are sendinf to the API, in this case we specify the model, the prompt, and that we don't want streaming responses
#         response = requests.post(
#             'http://localhost:11434/api/generate',
#             json={'model': 'mistral', 'prompt': prompt, 'stream': False},
#             timeout=180
#         )
        
# 		# Check if the response is successful
#         if response.status_code != 200:
#             print(f"✗ Error: {response.status_code}")
#             return
        
# 		# Extract the text response from the API
#         result = response.json()['response'].strip()
#         print(f"✓ Response received:\n{result}\n")
        
#         # Try to parse JSON
#         try:
#             json_start = result.find('{')
#             json_end = result.rfind('}') + 1
#             if json_start >= 0 and json_end > 0:
#                 json_str = result[json_start:json_end]
#                 parsed = json.loads(json_str)
#                 print(f"✓ Valid JSON: {json.dumps(parsed, indent=2)}")
#             else:
#                 print("✗ No JSON found in response")
#         except json.JSONDecodeError:
#             print("✗ JSON parse failed (but that's OK for testing)")
        
#     except requests.exceptions.ConnectionError:
#         print("✗ Connection refused. Is Ollama running? (ollama serve)")
#     except requests.exceptions.Timeout:
#         print("✗ Timeout. Mistral is slow on 2018 MacBook, this is normal")
#     except Exception as e:
#         print(f"✗ Error: {e}")

# if __name__ == "__main__":
#     test_ollama()