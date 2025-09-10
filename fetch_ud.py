import requests
import json
import os
import datetime
import time
import random
from typing import Dict, List, Set, Optional


class UrbanDictionaryFetcher:
    def __init__(self):
        self.api_url = "https://api.urbandictionary.com/v0/random"
        self.data_dir = "data"
        self.dict_dir = "dictionary"
        self.seen_defids: Set[int] = set()
        self.max_retries = 3
        self.retry_delay = 1 
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.dict_dir, exist_ok=True)
        
        self._load_existing_defids()
    
    def _load_existing_defids(self) -> None:
        if os.path.exists(self.data_dir):
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.data_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for entry in data:
                                if 'defid' in entry:
                                    self.seen_defids.add(entry['defid'])
                    except (json.JSONDecodeError, FileNotFoundError):
                        continue
    
    def _make_request(self) -> Optional[Dict]:
        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.api_url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return None
    
    def _extract_entry_data(self, raw_entry: Dict) -> Optional[Dict]:
        try:
            return {
                'defid': raw_entry['defid'],
                'word': raw_entry['word'].strip(),
                'definition': raw_entry['definition'].strip(),
                'example': raw_entry['example'].strip(),
                'written_on': raw_entry['written_on']
            }
        except KeyError:
            return None
    
    def _validate_json(self, data) -> bool:
        try:
            json.dumps(data)
            return True
        except (TypeError, ValueError):
            return False
    
    def _save_to_daily_dump(self, entries: List[Dict]) -> None:
        if not entries:
            return
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(self.data_dir, f"{today}.json")
        
        existing_data = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_data = []
        
        existing_data.extend(entries)
        
        if self._validate_json(existing_data):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    def _save_to_alphabetical_dict(self, entries: List[Dict]) -> None:
        if not entries:
            return
        
        letter_groups = {}
        for entry in entries:
            word = entry['word'].upper()
            if word:
                first_letter = word[0] if word[0].isalpha() else 'OTHER'
                if first_letter not in letter_groups:
                    letter_groups[first_letter] = []
                letter_groups[first_letter].append(entry)
        
        for letter, letter_entries in letter_groups.items():
            filepath = os.path.join(self.dict_dir, f"{letter}.json")
            
            existing_dict = {}
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        existing_dict = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_dict = {}
            
            for entry in letter_entries:
                word = entry['word']
                entry_data = {
                    'defid': entry['defid'],
                    'definition': entry['definition'],
                    'example': entry['example'],
                    'written_on': entry['written_on']
                }
                
                if word not in existing_dict:
                    existing_dict[word] = []
                existing_dict[word].append(entry_data)
            
            if self._validate_json(existing_dict):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(existing_dict, f, indent=2, ensure_ascii=False)
    
    def fetch_and_store(self, num_batches: int = 50) -> int:
        new_entries = []
        
        for i in range(num_batches):
            response_data = self._make_request()
            if not response_data or 'list' not in response_data:
                continue
            
            for raw_entry in response_data['list']:
                entry_data = self._extract_entry_data(raw_entry)
                if not entry_data:
                    continue
                
                defid = entry_data['defid']
                if defid in self.seen_defids:
                    continue
                
                new_entries.append(entry_data)
                self.seen_defids.add(defid)
            
            time.sleep(1 + random.uniform(0, 0.5))
        
        if new_entries:
            self._save_to_daily_dump(new_entries)
            self._save_to_alphabetical_dict(new_entries)
        
        return len(new_entries)


def main():
    fetcher = UrbanDictionaryFetcher()
    new_entries_count = fetcher.fetch_and_store(num_batches=50)
    print(f"Added {new_entries_count} new entries during this run")


if __name__ == "__main__":
    main()