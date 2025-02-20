import asyncio
from datetime import datetime
from enum import Enum

import uvicorn
from typing import List, Dict, Optional
from urllib.parse import urlparse, urlencode, urlunparse, parse_qs

from aiohttp.web_response import BaseClass
from fastapi import FastAPI
from crawl4ai import AsyncWebCrawler
from openai import BaseModel
from starlette.responses import JSONResponse

from linkedin_api import Linkedin


api = Linkedin("aidada9925@gmail.com", "Sz57iUqgUn68/#z")
app = FastAPI()

def all_elements_included(array, elements):
    return all(element in array for element in elements)

def extract_pagination_urls(data: List[Dict], existing_urls: List[str]) -> List[str]:
    pagination_urls = []

    for item in data:
        if not item.get('href') or not item.get('text'):
            continue

        parsed_url = urlparse(item['href'])

        # Check if it's a Google domain
        if not parsed_url.netloc.endswith('google.com'):
            continue

        # Check if the text is a number or 'Next'
        if item['text'].isdigit() and item['href'] not in existing_urls:
            # For numbered pages, store the URL with the page number as key
            pagination_urls.append(item['href'])

    # Merge and return unique URLs
    return list(set(existing_urls + pagination_urls))

def extract_candidate_data(data: List[str]) -> List[Dict]:
    candidate_list = []

    for linked_profile_url in data:
        profile = None
        try:
            parsed_url = urlparse(linked_profile_url)
            public_username = parsed_url.path.strip("/").split("/")[-1]
            profile = api.get_profile(public_username)

            if profile:
                candidate_skills = [skill.get("name", "") for skill in profile.get("skills", [])]
                education_list = []
                for education in profile.get("education", []):
                    end_date = education.get("timePeriod", {}).get("endDate", {}).get("year")
                    education_list.append({
                        "school": education.get("schoolName", ""),
                        "degree": education.get("degreeName", ""),
                        "start_date": education.get("timePeriod", {}).get("startDate", {}).get("year"),
                        "end_date": end_date,
                    })

                experience_list = []
                current_company = None
                for experience in profile.get("experience", []):
                    start_date = experience.get("timePeriod", {}).get("startDate", {})
                    end_date = experience.get("timePeriod", {}).get("endDate", {}) or None

                    start_year = start_date.get("year")
                    start_month = start_date.get("month")
                    end_year = end_date.get("year")
                    end_month = end_date.get("month")

                    start = datetime(start_year, start_month, 1)
                    if end_year and end_month:
                        end = datetime(end_year, end_month, 1)
                        total_months = (end.year - start.year) * 12 + end.month - start.month
                    else:
                        end = None
                        total_months = None

                    experience_obj = {
                        "company": experience.get("companyName", ""),
                        "title": experience.get("title", ""),
                        "location": experience.get("locationName", ""),
                        "start_date": str(start),
                        "end_date": str(end),
                        "is_current": True if not end_date else False,
                        "company_logo": experience.get("companyLogoUrl", ""),
                        "total_months": total_months
                    }
                    if end_date is None:
                        current_company = experience_obj

                    experience_list.append(experience_obj)

                certificate_list = []
                for certificate in profile.get("certifications", []):
                    end_date = certificate.get("timePeriod", {}).get("endDate", {}).get("year")
                    certificate_list.append({
                        "name": certificate.get("name", ""),
                        "platform": certificate.get("authority", ""),
                        "start_date": certificate.get("timePeriod", {}).get("startDate", {}).get("year"),
                        "end_date": end_date,
                        "is_active" : True if not end_date else False,
                        "certificate_url": certificate.get("url", "")
                    })


                for lag in profile.get("languages", []):
                    print(lag)

                for honor in profile.get("honors", []):
                    print(honor)


                for project in profile.get("projects", []):
                    print(project)

                for volunteer in profile.get("volunteer", []):
                    print(volunteer)

                candidate_list.append({
                    "first_name": profile.get("firstName", ""),
                    "last_name": profile.get("lastName", ""),
                    "headline": profile.get("headline", ""),
                    "bio" : profile.get("summary", ""),
                    "location": profile.get("geoLocationName", "") + ", " + profile.get("locationName", ""),
                    "skills": candidate_skills,
                    "education": education_list,
                    "experience": experience_list,
                    "linkedin_url" : linked_profile_url,
                    "current_company": current_company,
                    "certificates": certificate_list,
                    "is_student": profile.get("student", False),
                    "email" : None,
                    "phone" : None
                })
        except Exception as e:
            print("Error While Fetching Candidate Data: ", e, linked_profile_url)

    return candidate_list

async def call_crawl4ai(url):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url
        )
    return result

async def get_candidate(position:str, city:str, state:str, country:str, skills:list[str]):
    try:
        candidate_list = []
        query = f'site:linkedin.com/in/ "{position}" "{city}, {state}, {country}" "{",".join(skills)}"'
        query_params = {
            "q": query,
        }

        url_parts = list(urlparse("https://www.google.com/search"))
        url_parts[4] = urlencode(query_params)
        url = urlunparse(url_parts)

        query_result = await call_crawl4ai(url)

        linkedin_candidates_url = [link.get("href") for link in query_result.links["external"] if
                               "linkedin.com" in link.get("base_domain")]
        pagination_urls = extract_pagination_urls(query_result.links["internal"], [])

        first_page_candidates = extract_candidate_data(linkedin_candidates_url)

        candidate_list.extend(first_page_candidates)

        for url in pagination_urls:
            result = await call_crawl4ai(url)
            linkedin_candidates_url = [link.get("href") for link in result.links["external"] if
                                   "linkedin.com" in link.get("base_domain")]
            pagination_urls = extract_pagination_urls(result.links["internal"], pagination_urls)
            next_page_candidates = extract_candidate_data(linkedin_candidates_url)
            candidate_list.extend(next_page_candidates)

        return candidate_list
    except Exception as e:
        print("Error While Fetching Candidate Data: ", e)


def extract_company_employee_past_organization(parent_company: str, position:str, data: List[str]) -> List[Dict]:
    companies_list = []

    for linked_profile_url in data:
        profile = None
        try:
            parsed_url = urlparse(linked_profile_url)
            public_username = parsed_url.path.strip("/").split("/")[-1]
            profile = api.get_profile(public_username)

            if profile:
                experiences = profile.get("experience", [])
                for index, experience in enumerate(experiences):
                    start_date = experience.get("timePeriod", {}).get("startDate", {})
                    end_date = experience.get("timePeriod", {}).get("endDate", {}) or None

                    start_year = start_date.get("year")
                    start_month = start_date.get("month")

                    if end_date is None:
                        company_name = experience.get("companyName", "")
                        title = experience.get("title", "")

                        if company_name.lower() == parent_company.lower() and title.lower() == position.lower():
                            print("Employee in Parent Company")
                            end = datetime.now()
                            total_months = (end.year - start_year) * 12 + end.month - start_month

                            if total_months < 4:
                                previous_org_index = index - 1 if index > 0 else None

                                if previous_org_index >= 0 and previous_org_index:
                                    previous_org = experiences[previous_org_index]

                                    start_date = previous_org.get("timePeriod", {}).get("startDate", {})
                                    end_date = previous_org.get("timePeriod", {}).get("endDate", {}) or None

                                    start_year = start_date.get("year")
                                    start_month = start_date.get("month")
                                    end_year = end_date.get("year")
                                    end_month = end_date.get("month")

                                    total_months = (end_year - start_year) * 12 + end_month - start_month

                                    companies_list.append({
                                        "company": previous_org.get("companyName", ""),
                                        "title": previous_org.get("title", ""),
                                        "location": previous_org.get("locationName", ""),
                                        "start_date": str(datetime(start_year, start_month, 1)),
                                        "end_date": str(datetime(end.year, end.month, 1)),
                                        "is_current": False,
                                        "company_logo": previous_org.get("companyLogoUrl", ""),
                                        "total_months": total_months
                                    })
        except Exception as e:
            print("Error While Fetching Candidate Data: ", e, linked_profile_url)

    return companies_list


async def get_candidate_from_targeted_company(parent_company:str, position:str, city:str, state:str, country:str, skills:list[str]):
    companies = []
    query = f'site:linkedin.com/in/ "{position}" "{city}, {state}, {country}" "{",".join(skills)}"'
    query_params = {
        "q": query,
    }

    url_parts = list(urlparse("https://www.google.com/search"))
    url_parts[4] = urlencode(query_params)
    url = urlunparse(url_parts)

    query_result = await call_crawl4ai(url)

    linkedin_candidates_url = [link.get("href") for link in query_result.links["external"] if
                               "linkedin.com" in link.get("base_domain")]
    pagination_urls = extract_pagination_urls(query_result.links["internal"], [])

    first_page_companies = extract_company_employee_past_organization(parent_company=parent_company, position=position, data=linkedin_candidates_url)

    companies.extend(first_page_companies)

    for url in pagination_urls:
        result = await call_crawl4ai(url)
        linkedin_candidates_url = [link.get("href") for link in result.links["external"] if
                                   "linkedin.com" in link.get("base_domain")]
        pagination_urls = extract_pagination_urls(result.links["internal"], pagination_urls)
        next_page_companies = extract_company_employee_past_organization(parent_company=parent_company, position=position, data=linkedin_candidates_url)
        companies.extend(next_page_companies)



class FlagEnum(str, Enum):
    TARGET = "TARGET",
    NOT_TARGET = "NOT_TARGET"
    ALL = "ALL"

class DataScraperInput(BaseModel):
    parent_company : Optional[str] = None
    position: str
    city: str
    state: str
    country: str
    skills: List[str]
    flag: FlagEnum


@app.post("/get-candidate")
async def get_candidate_data(linkedin_scraper_input: DataScraperInput):
    try:
        if linkedin_scraper_input.flag == FlagEnum.TARGET:
            data = await get_candidate_from_targeted_company(parent_company=linkedin_scraper_input.parent_company, position=linkedin_scraper_input.position, city=linkedin_scraper_input.city, state=linkedin_scraper_input.state, country=linkedin_scraper_input.country, skills=linkedin_scraper_input.skills)
            return JSONResponse(status_code=200, content=data)
        elif linkedin_scraper_input.flag == FlagEnum.NOT_TARGET:
            pass
        else:
            data = await get_candidate(position=linkedin_scraper_input.position, city=linkedin_scraper_input.city, state=linkedin_scraper_input.state, country=linkedin_scraper_input.country, skills=linkedin_scraper_input.skills)
            return JSONResponse(status_code=200, content=data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

if __name__ == "__main__":
    uvicorn.run(app)