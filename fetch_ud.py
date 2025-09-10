#!/usr/bin/env python3
"""
Urban Dictionary Archive Fetcher

Fetches random entries from Urban Dictionary API and stores them in:
1. Daily dumps: /data/YYYY-MM-DD.json
2. Alphabetical dictionary: /dictionary/{LETTER}.json
"""

import requests
import json
import os
import datetime
import time
from typing import Dict, List, Set, Optional


class UrbanDictionaryFetcher:
    def __init__(self):
        self.api_url = "https://api.urbandictionary.com/v0/random"
        self.data_dir = "data"
        self.dict_dir = "dictionary"
        self.seen_defids: Set[int] = set()
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.dict_dir, exist_ok=True)
        
        # Load existing defids to avoid duplicates
        self._load_existing_defids()
    
    def _load_existing_defids(self) -> None:
        """Load existing defids from all daily dump files to avoid duplicates."""
        print("Loading existing defids for deduplication...")
        
        # Load from daily dumps
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
        
        print(f"Loaded {len(self.seen_defids)} existing defids")
    
    def _make_request(self) -> Optional[Dict]:
        """Make API request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.api_url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"API request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print("Max retries reached, skipping this request")
                    return None
    
    def _extract_entry_data(self, raw_entry: Dict) -> Optional[Dict]:
        """Extract required fields from API response entry."""
        try:
            return {
                'defid': raw_entry['defid'],
                'word': raw_entry['word'].strip(),
                'definition': raw_entry['definition'].strip(),
                'example': raw_entry['example'].strip(),
                'written_on': raw_entry['written_on']
            }
        except KeyError as e:
            print(f"Missing required field {e} in entry, skipping")
            return None
    
    def _validate_json(self, data) -> bool:
        """Validate that data can be serialized to JSON."""
        try:
            json.dumps(data)
            return True
        except (TypeError, ValueError) as e:
            print(f"JSON validation failed: {e}")
            return False
    
    def _save_to_daily_dump(self, entries: List[Dict]) -> None:
        """Save entries to daily dump file."""
        if not entries:
            return
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(self.data_dir, f"{today}.json")
        
        # Load existing data if file exists
        existing_data = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_data = []
        
        # Append new entries
        existing_data.extend(entries)
        
        # Validate and save
        if self._validate_json(existing_data):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(entries)} entries to {filepath}")
        else:
            print(f"Failed to save to {filepath}: JSON validation failed")
    
    def _save_to_alphabetical_dict(self, entries: List[Dict]) -> None:
        """Save entries to alphabetical dictionary files."""
        if not entries:
            return
        
        # Group entries by first letter
        letter_groups = {}
        for entry in entries:
            word = entry['word'].upper()
            if word:
                first_letter = word[0] if word[0].isalpha() else 'OTHER'
                if first_letter not in letter_groups:
                    letter_groups[first_letter] = []
                letter_groups[first_letter].append(entry)
        
        # Save each letter group
        for letter, letter_entries in letter_groups.items():
            filepath = os.path.join(self.dict_dir, f"{letter}.json")
            
            # Load existing dictionary
            existing_dict = {}
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        existing_dict = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_dict = {}
            
            # Add new entries
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
            
            # Validate and save
            if self._validate_json(existing_dict):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(existing_dict, f, indent=2, ensure_ascii=False)
                print(f"Updated {filepath} with {len(letter_entries)} entries")
            else:
                print(f"Failed to save to {filepath}: JSON validation failed")
    
    def fetch_and_store(self, num_requests: int = 10) -> None:
        """Fetch entries from API and store them."""
        print(f"Starting fetch process with {num_requests} requests...")
        
        new_entries = []
        duplicates_skipped = 0
        
        for i in range(num_requests):
            print(f"Request {i + 1}/{num_requests}")
            
            # Make API request
            response_data = self._make_request()
            if not response_data or 'list' not in response_data:
                continue
            
            # Process each entry in the response
            for raw_entry in response_data['list']:
                entry_data = self._extract_entry_data(raw_entry)
                if not entry_data:
                    continue
                
                # Check for duplicates
                defid = entry_data['defid']
                if defid in self.seen_defids:
                    duplicates_skipped += 1
                    continue
                
                # Add to new entries and mark as seen
                new_entries.append(entry_data)
                self.seen_defids.add(defid)
            
            # Small delay between requests to be respectful
            time.sleep(0.5)
        
        print(f"Fetched {len(new_entries)} new entries, skipped {duplicates_skipped} duplicates")
        
        # Save to both storage locations
        if new_entries:
            self._save_to_daily_dump(new_entries)
            self._save_to_alphabetical_dict(new_entries)
        else:
            print("No new entries to save")


def main():
    """Main function to run the fetcher."""
    fetcher = UrbanDictionaryFetcher()
    
    # Fetch and store entries
    # Adjust num_requests based on how frequently this runs
    # For every 15 minutes, 5-10 requests should be sufficient
    fetcher.fetch_and_store(num_requests=5)
    
    print("Fetch process completed")


if __name__ == "__main__":
    main()