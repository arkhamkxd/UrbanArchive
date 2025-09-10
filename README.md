# UrbanArchive

**Urban Dictionary Archive** – A continuously scraped dataset of slang definitions from Urban Dictionary, automatically updated every 15 minutes via GitHub Actions.

## 📁 Data Structure

This repository maintains two complementary data storage formats:

### 1. Daily Dumps (`/data/YYYY-MM-DD.json`)
Daily chronological archives containing all entries fetched on a specific date. Each file contains an array of definition objects.

### 2. Alphabetical Dictionary (`/dictionary/A.json` ... `/dictionary/Z.json`)
Alphabetically organized files where entries are grouped by the first letter of the word. Each file is structured as a JSON object with words as keys and arrays of definitions as values.

## 📋 Entry Format

Each definition entry contains the following fields:

```json
{
  "defid": 12345678,
  "word": "rizz",
  "definition": "Slang for charisma; ability to attract.",
  "example": "He's got mad rizz.",
  "written_on": "2025-09-09T21:31:00.000Z"
}
```

### Field Descriptions
- `defid`: Unique identifier for the definition (used for deduplication)
- `word`: The slang term being defined
- `definition`: The definition of the word
- `example`: Usage example of the word
- `written_on`: Timestamp when the definition was originally submitted

## 🔍 Querying the Data

### By Date
To find all entries from a specific date:
```bash
# View entries from January 15, 2024
cat data/2024-01-15.json
```

### By Alphabetical Order
To find all words starting with a specific letter:
```bash
# View all words starting with 'R'
cat dictionary/R.json
```

### Example: Finding "rizz" definitions
```bash
# Look in the R.json file
jq '.rizz' dictionary/R.json
```

## 🔄 Data Collection Process

- **Source**: Urban Dictionary Random API (`https://api.urbandictionary.com/v0/random`)
- **Frequency**: Every 15 minutes via GitHub Actions
- **Deduplication**: Entries are deduplicated by `defid` to ensure data cleanliness
- **Error Handling**: API failures are handled gracefully with retry logic
- **Storage**: Dual storage system for both chronological and alphabetical access

## 🚀 Running Locally

1. Clone the repository:
```bash
git clone https://github.com/yourusername/UrbanArchive.git
cd UrbanArchive
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the fetcher:
```bash
python fetch_ud.py
```

## 📊 Data Statistics

The repository automatically maintains:
- **Deduplication**: No duplicate entries based on `defid`
- **Continuous Growth**: New entries added every 15 minutes
- **Dual Access**: Both chronological (daily) and alphabetical organization
- **JSON Validation**: All data is validated before storage

## 🤝 Contributing

This is an automated data collection project. The main ways to contribute are:
- Improving the fetching script (`fetch_ud.py`)
- Enhancing data processing or storage formats
- Adding data analysis tools or utilities
- Reporting issues with the automation

## 📄 License

This project is open source. The collected data comes from Urban Dictionary's public API.

## ⚠️ Disclaimer

This archive contains user-generated content from Urban Dictionary. The definitions and examples may contain explicit language, offensive terms, or inappropriate content. This repository is for research and archival purposes only.