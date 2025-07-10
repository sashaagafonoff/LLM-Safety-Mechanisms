import feedparser
import requests
from datetime import datetime, timedelta
import json
from pathlib import Path
import hashlib

class SourceMonitor:
    def __init__(self):
        self.sources = {
            'openai': {
                'blog_rss': 'https://openai.com/blog/rss.xml',
                'research_url': 'https://openai.com/research',
                'docs_url': 'https://platform.openai.com/docs',
                'keywords': ['safety', 'alignment', 'moderation', 'red team', 'responsible']
            },
            'anthropic': {
                'blog_url': 'https://www.anthropic.com/news',
                'research_url': 'https://www.anthropic.com/research',
                'keywords': ['constitutional', 'safety', 'alignment', 'responsible scaling']
            },
            'google': {
                'blog_url': 'https://blog.google/technology/ai/',
                'deepmind_url': 'https://deepmind.google/discover/blog/',
                'keywords': ['safety', 'responsible', 'alignment', 'red team']
            },
            'meta': {
                'blog_url': 'https://ai.meta.com/blog/',
                'research_url': 'https://ai.meta.com/research/',
                'keywords': ['llama', 'safety', 'responsible', 'red team']
            }
        }
        
        self.cache_dir = Path('cache/sources')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def check_rss_feeds(self):
        """Monitor RSS feeds for safety-related posts"""
        new_posts = []
        
        for provider, config in self.sources.items():
            if 'blog_rss' in config:
                feed = feedparser.parse(config['blog_rss'])
                
                for entry in feed.entries[:10]:  # Check recent 10
                    # Check if contains safety keywords
                    content = f"{entry.title} {entry.get('summary', '')}".lower()
                    if any(keyword in content for keyword in config['keywords']):
                        post_id = hashlib.md5(entry.link.encode()).hexdigest()
                        cache_file = self.cache_dir / f"{provider}_{post_id}.json"
                        
                        if not cache_file.exists():
                            new_posts.append({
                                'provider': provider,
                                'title': entry.title,
                                'url': entry.link,
                                'published': entry.get('published', ''),
                                'summary': entry.get('summary', ''),
                                'type': 'blog'
                            })
                            
                            # Cache it
                            with open(cache_file, 'w') as f:
                                json.dump(entry, f)
        
        return new_posts
    
    def scrape_research_papers(self):
        """Check for new papers mentioning safety"""
        # Search ArXiv for provider + safety papers
        arxiv_base = "http://export.arxiv.org/api/query?"
        
        new_papers = []
        for provider in ['OpenAI', 'Anthropic', 'Google', 'Meta']:
            query = f'search_query=all:{provider}+AND+(safety+OR+alignment)&max_results=5&sortBy=submittedDate&sortOrder=descending'
            
            response = requests.get(arxiv_base + query)
            if response.status_code == 200:
                # Parse ArXiv XML response (simplified)
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    title = entry.find('{http://www.w3.org/2005/Atom}title').text
                    url = entry.find('{http://www.w3.org/2005/Atom}id').text
                    
                    paper_id = url.split('/')[-1]
                    cache_file = self.cache_dir / f"arxiv_{paper_id}.json"
                    
                    if not cache_file.exists():
                        new_papers.append({
                            'provider': provider.lower(),
                            'title': title.replace('\n', ' '),
                            'url': url,
                            'type': 'research',
                            'pdf_url': url.replace('abs', 'pdf') + '.pdf'
                        })
                        
                        with open(cache_file, 'w') as f:
                            json.dump({'title': title, 'url': url}, f)
        
        return new_papers
    
    def check_github_releases(self):
        """Monitor GitHub for model cards and system cards"""
        repos = {
            'openai': ['openai/openai-python', 'openai/gpt-3'],
            'anthropic': ['anthropics/anthropic-sdk-python'],
            'meta': ['facebookresearch/llama', 'meta-llama/llama3'],
            'google': ['google/generative-ai-python']
        }
        
        new_releases = []
        headers = {'Accept': 'application/vnd.github.v3+json'}
        
        for provider, repo_list in repos.items():
            for repo in repo_list:
                url = f"https://api.github.com/repos/{repo}/releases"
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    releases = response.json()
                    for release in releases[:3]:  # Recent 3
                        if any(keyword in release.get('body', '').lower() 
                              for keyword in ['safety', 'card', 'responsible']):
                            
                            release_id = f"{repo}_{release['id']}"
                            cache_file = self.cache_dir / f"github_{release_id}.json"
                            
                            if not cache_file.exists():
                                new_releases.append({
                                    'provider': provider,
                                    'title': release['name'],
                                    'url': release['html_url'],
                                    'type': 'github_release'
                                })
                                
                                with open(cache_file, 'w') as f:
                                    json.dump(release, f)
        
        return new_releases

def monitor_all_sources():
    """Run all monitors and return new sources"""
    monitor = SourceMonitor()
    
    all_new = []
    
    print("🔍 Checking RSS feeds...")
    all_new.extend(monitor.check_rss_feeds())
    
    print("🔍 Checking ArXiv...")
    all_new.extend(monitor.scrape_research_papers())
    
    print("🔍 Checking GitHub...")
    all_new.extend(monitor.check_github_releases())
    
    if all_new:
        print(f"\n✅ Found {len(all_new)} new sources:")
        for source in all_new:
            print(f"  - [{source['provider']}] {source['title']}")
            print(f"    {source['url']}")
    
    return all_new

if __name__ == "__main__":
    monitor_all_sources()