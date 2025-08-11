# scripts/gatherers/research_openai_sources.py
import requests
import json
from datetime import datetime
from typing import List, Dict, Any

def research_openai_sources():
    """Research OpenAI's public model information sources"""
    
    sources = [
        {
            "name": "OpenAI Models API (public)",
            "url": "https://api.openai.com/v1/models",
            "type": "api",
            "auth_required": False
        },
        {
            "name": "OpenAI Platform Documentation",
            "url": "https://platform.openai.com/docs/models",
            "type": "documentation"
        },
        {
            "name": "OpenAI Pricing Page", 
            "url": "https://openai.com/api/pricing/",
            "type": "pricing"
        }
    ]
    
    results = {}
    
    for source in sources:
        print(f"\n🔍 Researching: {source['name']}")
        print(f"URL: {source['url']}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(source['url'], headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                if source['type'] == 'api':
                    results[source['name']] = analyze_api_response(response.text)
                else:
                    results[source['name']] = analyze_web_content(response.text, source['type'])
            else:
                results[source['name']] = {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"Error: {e}")
            results[source['name']] = {"error": str(e)}
    
    return results

def analyze_api_response(response_text: str) -> Dict[str, Any]:
    """Analyze API response for model data"""
    try:
        data = json.loads(response_text)
        
        if 'data' in data and isinstance(data['data'], list):
            models = data['data']
            
            # Extract model information
            model_info = []
            for model in models[:10]:  # Limit to first 10 for research
                info = {
                    'id': model.get('id'),
                    'object': model.get('object'),
                    'created': model.get('created'),
                    'owned_by': model.get('owned_by')
                }
                model_info.append(info)
            
            return {
                "total_models": len(models),
                "sample_models": model_info,
                "model_names": [m.get('id') for m in models if m.get('id')][:20]
            }
        else:
            return {"error": "Unexpected API response format", "response": response_text[:500]}
            
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response", "response": response_text[:500]}

def analyze_web_content(html_content: str, source_type: str) -> Dict[str, Any]:
    """Analyze web content for model information"""
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Look for GPT model mentions
    gpt_pattern = r'gpt-[0-9](?:\.[0-9])?(?:-turbo)?(?:-instruct)?'
    matches = re.findall(gpt_pattern, html_content, re.IGNORECASE)
    
    # Look for other OpenAI models
    other_models = re.findall(r'(dall-e-[0-9]|whisper-[0-9]|tts-[0-9]|text-embedding-[a-z0-9-]+)', html_content, re.IGNORECASE)
    
    return {
        "gpt_models": list(set(matches)),
        "other_models": list(set(other_models)),
        "total_length": len(html_content),
        "title": soup.title.string if soup.title else "No title"
    }

if __name__ == "__main__":
    print("🔬 OPENAI MODEL RESEARCH")
    print("=" * 50)
    
    research_results = research_openai_sources()
    
    print("\n📊 RESEARCH SUMMARY")
    print("=" * 30)
    
    for source, data in research_results.items():
        print(f"\n{source}:")
        if "error" in data:
            print(f"  ❌ {data['error']}")
        else:
            print(f"  ✅ Success!")
            if "total_models" in data:
                print(f"  📊 Total models: {data['total_models']}")
                print(f"  🤖 Sample names: {data.get('model_names', [])[:5]}")
            elif "gpt_models" in data:
                print(f"  🤖 GPT models found: {data['gpt_models']}")
                print(f"  🔧 Other models: {data['other_models'][:3]}")
    
    print(f"\n📝 Research completed at {datetime.now()}")