# LinkedIn Scraper Documentation

## Overview
This project is a LinkedIn profile scraper implemented as a FastAPI web application that allows searching and extracting information about LinkedIn profiles based on various criteria. It uses Google search to find LinkedIn profiles and then extracts detailed information using LinkedIn's API.

## Core Components

### 1. Main Application (`main.py`)
The main FastAPI application that provides the API endpoints and core functionality.

```python
app = FastAPI()
api = Linkedin("username", "password")  # LinkedIn API client instance
```

### 2. API Endpoints

#### Get Candidate Endpoint
```python
@app.post("/get-candidate")
async def get_candidate_data(linkedin_scraper_input: DataScraperInput)
```

Accepts POST requests with following input structure:
```python
class DataScraperInput(BaseModel):
    parent_company: Optional[str] = None
    position: str
    city: str 
    state: str
    country: str
    skills: List[str]
    flag: FlagEnum
```

### 3. Core Functions

#### Profile Search
```python
async def get_candidate(position: str, city: str, state: str, country: str, skills: list[str])
```
- Constructs Google search query to find LinkedIn profiles
- Uses AsyncWebCrawler to fetch search results
- Extracts LinkedIn profile URLs
- Returns list of candidate profiles

#### Targeted Company Search
```python
async def get_candidate_from_targeted_company(parent_company: str, position: str, city: str, state: str, country: str, skills: list[str])
```
- Similar to get_candidate but focuses on employees from specific companies
- Filters candidates based on company and position
- Returns list of companies and relevant profiles

### 4. Data Extraction Functions

#### Extract Candidate Data
```python
def extract_candidate_data(data: List[str]) -> List[Dict]
```
Extracts detailed profile information including:
- Personal information (name, headline, bio)
- Skills
- Education history
- Work experience
- Certifications
- Languages and other achievements

#### Extract Company Employee Data
```python
def extract_company_employee_past_organization(parent_company: str, position: str, data: List[str]) -> List[Dict]
```
- Focuses on extracting information about employees' previous organizations
- Particularly useful for tracking career movements

## Data Structures

### 1. Profile Data
```python
{
    "first_name": str,
    "last_name": str,
    "headline": str,
    "bio": str,
    "location": str,
    "skills": List[str],
    "education": List[Dict],
    "experience": List[Dict],
    "linkedin_url": str,
    "current_company": Dict,
    "certificates": List[Dict],
    "is_student": bool,
    "email": Optional[str],
    "phone": Optional[str]
}
```

### 2. Experience Data
```python
{
    "company": str,
    "title": str,
    "location": str,
    "start_date": str,
    "end_date": str,
    "is_current": bool,
    "company_logo": str,
    "total_months": int
}
```

## Installation and Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Installation Steps
1. Clone the repository:
```bash
git clone https://github.com/yourusername/linkedin-scraper.git
cd linkedin-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure LinkedIn credentials:
   - Update the LinkedIn credentials in `main.py`
   - Or set environment variables:
```bash
set LINKEDIN_USERNAME=your_email
set LINKEDIN_PASSWORD=your_password
```

## Usage

### 1. Starting the Server
```bash
python main.py
```
This starts the FastAPI server using uvicorn.

### 2. Making Requests
Example request:
```python
payload = {
    "parent_company": "Google",
    "position": "Data Scientist",
    "city": "San Francisco",
    "state": "CA",
    "country": "USA",
    "skills": ["Python", "Machine Learning"],
    "flag": "TARGET"
}
response = requests.post("http://localhost:8000/get-candidate", json=payload)
```

## Error Handling
- The application includes comprehensive error handling for:
  - API request failures
  - Profile parsing errors
  - Network issues
  - Invalid input data

## Dependencies
- FastAPI
- Uvicorn
- Requests
- BeautifulSoup4
- crawl4ai
- Python-LinkedIn API

## Security Considerations
- Handles LinkedIn authentication using cookie-based sessions
- Implements rate limiting to avoid API restrictions
- Securely manages credentials and session data

## Performance
- Uses asynchronous operations for improved performance
- Implements pagination handling for large result sets
- Caches LinkedIn session cookies to minimize authentication requests

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.