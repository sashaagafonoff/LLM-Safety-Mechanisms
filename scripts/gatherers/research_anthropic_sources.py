# research_anthropic_sources.py
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import List, Dict, Any

def research_anthropic_sources():
    """Research and test various Anthropic public sources for model information"""
    
    sources = [
        {
            "name": "Anthropic Models Overview",
            "url": "https://docs.anthropic.com/claude/docs/models-overview",
            "type": "documentation"
        },
        {
            "name": "Anthropic API Reference", 
            "url": "https://docs.anthropic.com/claude/reference/getting-started",
            "type": "api_docs"
        },
        {
            "name": "Anthropic Main Site",
            "url": "https://www.anthropic.com/claude",
            "type": "marketing"
        },
        {
            "name": "Anthropic GitHub",
            "url": "https://github.com/anthropics",
            "type": "github"
        }
    ]
    
    results = {}
    
    for source in sources:
        print(f"\n🔍 Researching: {source['name']}")
        print(f"URL: {source['url']}")
        
        try:
            response = requests.get(source['url'], timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                results[source['name']] = analyze_content(response.text, source['type'])
            else:
                results[source['name']] = {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"Error: {e}")
            results[source['name']] = {"error": str(e)}
    
    return results

def analyze_content(html_content: str, source_type: str) -> Dict[str, Any]:
    """Analyze HTML content for model information"""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Look for common patterns
    model_mentions = []
    
    # Search for Claude model names
    claude_pattern = r'claude-[0-9](?:\.[0-9])?-(?:opus|sonnet|haiku|instant)?'
    matches = re.findall(claude_pattern, html_content, re.IGNORECASE)
    model_mentions.extend(matches)
    
    # Look for tables that might contain model info
    tables = soup.find_all('table')
    table_data = []
    for table in tables[:3]:  # Only check first 3 tables
        headers = [th.get_text().strip() for th in table.find_all(['th', 'td'])]
        if any('model' in h.lower() or 'claude' in h.lower() for h in headers):
            table_data.append({
                "headers": headers[:10],  # Limit output
                "row_count": len(table.find_all('tr'))
            })
    
    # Look for structured data (JSON-LD, etc.)
    scripts = soup.find_all('script', type='application/ld+json')
    structured_data = []
    for script in scripts:
        try:
            data = json.loads(script.string)
            structured_data.append(str(data)[:200] + "..." if len(str(data)) > 200 else str(data))
        except:
            pass
    
    # Look for divs/sections that might contain model info
    model_sections = []
    for div in soup.find_all(['div', 'section'])[:20]:  # Limit search
        text = div.get_text().lower()
        if 'claude' in text and ('model' in text or 'version' in text):
            model_sections.append(div.get_text().strip()[:200] + "...")
    
    return {
        "model_mentions": list(set(model_mentions)),  # Remove duplicates
        "tables_found": table_data,
        "structured_data": structured_data,
        "model_sections": model_sections[:5],  # Limit output
        "total_length": len(html_content),
        "title": soup.title.string if soup.title else "No title"
    }

def extract_model_data_prototype():
    """Prototype function to extract actual model data from the most promising source"""
    
    print("\n🚀 PROTOTYPE: Attempting to extract model data from Anthropic docs")
    
    try:
        # Focus on the models overview page
        url = "https://docs.anthropic.com/claude/docs/models-overview"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to fetch {url}: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        models = []
        
        # Look for tables with model information
        tables = soup.find_all('table')
        
        for table in tables:
            headers = [th.get_text().strip().lower() for th in table.find_all(['th'])]
            
            # Check if this looks like a models table
            if any(keyword in ' '.join(headers) for keyword in ['model', 'claude', 'name']):
                print(f"Found potential model table with headers: {headers}")
                
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = [td.get_text().strip() for td in row.find_all(['td', 'th'])]
                    
                    if cells and any('claude' in cell.lower() for cell in cells):
                        # Try to extract model info
                        model_info = extract_model_from_row(cells, headers)
                        if model_info:
                            models.append(model_info)
        
        return models
        
    except Exception as e:
        print(f"Prototype extraction failed: {e}")
        return []

def extract_model_from_row(cells: List[str], headers: List[str]) -> Dict[str, Any]:
    """Extract model information from a table row"""
    
    model_info = {
        "provider": "anthropic",
        "last_updated": datetime.now().isoformat(),
        "status": "active"
    }
    
    # Map common header patterns to our schema
    header_mapping = {
        "model": "name",
        "name": "name", 
        "context": "context_window",
        "context window": "context_window",
        "tokens": "context_window",
        "description": "description",
        "use case": "capabilities"
    }
    
    for i, cell in enumerate(cells):
        if i < len(headers):
            header = headers[i].lower()
            
            # Find matching field
            for pattern, field in header_mapping.items():
                if pattern in header:
                    if field == "context_window":
                        # Extract numeric value
                        numbers = re.findall(r'[\d,]+', cell)
                        if numbers:
                            model_info[field] = int(numbers[0].replace(',', ''))
                    else:
                        model_info[field] = cell
                    break
    
    # Only return if we found a model name
    return model_info if "name" in model_info else None

if __name__ == "__main__":
    print("🔬 ANTHROPIC MODEL RESEARCH")
    print("=" * 50)
    
    # Phase 1: Research sources
    research_results = research_anthropic_sources()
    
    print("\n📊 RESEARCH SUMMARY")
    print("=" * 30)
    
    for source, data in research_results.items():
        print(f"\n{source}:")
        if "error" in data:
            print(f"  ❌ {data['error']}")
        else:
            print(f"  ✅ Title: {data.get('title', 'N/A')}")
            print(f"  📄 Content length: {data.get('total_length', 0):,} chars")
            print(f"  🤖 Model mentions: {data.get('model_mentions', [])}")
            print(f"  📋 Tables found: {len(data.get('tables_found', []))}")
            if data.get('tables_found'):
                for table in data['tables_found']:
                    print(f"    - {table['row_count']} rows, headers: {table['headers'][:3]}...")
    
    # Phase 2: Prototype extraction
    print("\n" + "=" * 50)
    models = extract_model_data_prototype()
    
    if models:
        print(f"\n✅ EXTRACTED {len(models)} MODELS:")
        for model in models:
            print(f"  📱 {model}")
    else:
        print("\n❌ No models extracted - need to refine extraction logic")
    
    print(f"\n📝 Research completed at {datetime.now()}")