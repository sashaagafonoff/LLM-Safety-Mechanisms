import os
import requests
import logging
import json
import mimetypes
import argparse
from pathlib import Path
from urllib.parse import urlparse
from markitdown import MarkItDown
from bs4 import BeautifulSoup

# Setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("UniversalIngest")
md = MarkItDown()

# Configuration
EVIDENCE_PATH = Path("data/evidence.json")
OUTPUT_DIR = Path("data/flat_text")

def load_sources(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and "sources" in data:
            return data["sources"]
        elif isinstance(data, list):
            return data
        else:
            return []
    except Exception as e:
        logger.error(f"Error loading evidence: {e}")
        return []

def sanitize_filename(name):
    return "".join([c for c in name if c.isalnum() or c in ('-', '_')]).rstrip()

def fix_github_url(url):
    """Converts GitHub blob URLs to raw content URLs to avoid fetching HTML wrappers."""
    if "github.com" in url and "/blob/" in url:
        logger.info("   -> Detected GitHub Blob URL. Converting to Raw...")
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url

def extract_text_from_html(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f, 'html.parser')
            for script in soup(["script", "style", "nav", "footer", "header", "aside", "form", "button"]):
                script.extract()    
            text = soup.get_text(separator='\n')
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
    except Exception as e:
        logger.error(f"HTML parsing failed: {e}")
        return None

def determine_extension_from_header(content_type, url):
    """Maps HTTP Content-Type to file extensions."""
    if not content_type:
        path = urlparse(url).path
        return os.path.splitext(path)[1].lower() or ".html"
    
    content_type = content_type.split(';')[0].strip().lower()
    
    if content_type == 'application/pdf':
        return ".pdf"
    elif 'html' in content_type:
        return ".html"
    elif 'json' in content_type:
        return ".json"
    elif 'text/plain' in content_type or 'markdown' in content_type:
        if ".md" in url: return ".md"
        return ".txt"
    
    ext = mimetypes.guess_extension(content_type)
    return ext if ext else ".html"

def ingest_all(target_id=None):
    sources = load_sources(EVIDENCE_PATH)
    if not sources:
        logger.warning("No sources found to process.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # --- THE ROBUST HEADER SET (Restored) ---
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1'
    }
    
    found_target = False
    
    for i, source in enumerate(sources):
        if not isinstance(source, dict): continue
        if source.get("status") == "inactive": continue

        # Identify ID
        title = source.get("title", "untitled")
        doc_id = source.get("id")
        if not doc_id and source.get("models"):
             doc_id = source["models"][0].get("modelId")
        if not doc_id:
             doc_id = sanitize_filename(title)

        # TARGET CHECK
        if target_id:
            # Case-insensitive check for convenience
            if doc_id.lower() != target_id.lower():
                continue
            else:
                found_target = True

        # Identify & Fix URL
        original_uri = source.get("url", source.get("uri"))
        if not original_uri or original_uri == "<missing>":
            logger.warning(f"Skipping {doc_id}: Missing URL")
            continue

        uri = fix_github_url(original_uri)
        
        try:
            logger.info(f"Processing: {doc_id}...")

            # 1. Fetch
            response = requests.get(uri, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # 2. Detect Type
            content_type = response.headers.get('Content-Type', '')
            ext = determine_extension_from_header(content_type, uri)
            logger.info(f"   -> Detected Type: {content_type} (Extension: {ext})")

            # 3. Save Temp
            temp_filename = f"temp_{sanitize_filename(doc_id)}{ext}"
            with open(temp_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 4. Convert
            processed_content = ""
            if ext == ".pdf":
                result = md.convert(temp_filename)
                processed_content = result.text_content
            elif ext == ".html":
                processed_content = extract_text_from_html(temp_filename)
            else:
                result = md.convert(temp_filename)
                processed_content = result.text_content

            if not processed_content:
                processed_content = "[NO CONTENT EXTRACTED]"

            # 5. Save Artifact
            output_filename = f"{sanitize_filename(doc_id)}.txt"
            output_path = OUTPUT_DIR / output_filename
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"SOURCE_ID: {doc_id}\n")
                f.write(f"SOURCE_TITLE: {title}\n")
                f.write(f"SOURCE_URI: {original_uri}\n")
                f.write("-" * 20 + "\n")
                f.write(processed_content)
                
            logger.info(f"   -> ✅ Saved to {output_filename}")
            
            if os.path.exists(temp_filename): os.remove(temp_filename)

        except Exception as e:
            logger.error(f"❌ Failed processing {doc_id}: {str(e)}")
            if os.path.exists(f"temp_{sanitize_filename(doc_id)}{ext}"):
                 os.remove(f"temp_{sanitize_filename(doc_id)}{ext}")

    if target_id and not found_target:
        logger.warning(f"Target ID '{target_id}' not found in evidence sources.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest safety documentation.")
    parser.add_argument("--id", help="Target a specific document ID to ingest.", default=None)
    args = parser.parse_args()
    
    ingest_all(target_id=args.id)