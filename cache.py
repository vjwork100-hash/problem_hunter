import json
import os
from typing import Dict, Any, Optional

CACHE_DIR = "cache"

class Cache:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        self.posts_cache_file = os.path.join(self.cache_dir, "posts_cache.json")
        self.analysis_cache_file = os.path.join(self.cache_dir, "analysis_cache.json")
        
        self.posts_cache = self._load_cache(self.posts_cache_file)
        self.analysis_cache = self._load_cache(self.analysis_cache_file)

    def _load_cache(self, filepath: str) -> Dict[str, Any]:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self, filepath: str, data: Dict[str, Any]):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        return self.posts_cache.get(post_id)

    def save_post(self, post_id: str, post_data: Dict[str, Any]):
        self.posts_cache[post_id] = post_data
        self._save_cache(self.posts_cache_file, self.posts_cache)

    def get_analysis(self, post_id: str) -> Optional[Dict[str, Any]]:
        return self.analysis_cache.get(post_id)

    def save_analysis(self, post_id: str, analysis_data: Dict[str, Any]):
        self.analysis_cache[post_id] = analysis_data
        self._save_cache(self.analysis_cache_file, self.analysis_cache)
        
    def clear_cache(self):
        if os.path.exists(self.posts_cache_file):
            os.remove(self.posts_cache_file)
        if os.path.exists(self.analysis_cache_file):
            os.remove(self.analysis_cache_file)
        self.posts_cache = {}
        self.analysis_cache = {}
