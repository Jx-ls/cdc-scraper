import os
import json
import logging
from env import ROLL_NUMBER
from utils import safe_text
from datetime import datetime
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup as bs
from endpoints import TPSTUDENT_URL, COMPANIES_URL


COMPANIES_FILE = f"{os.path.dirname(__file__)}/companies.json"


def fetch(session, headers, ssoToken):
    print('[FETCHING COMPANY UPDATES]', flush=True)

    session.post(
        TPSTUDENT_URL,
        data=dict(ssoToken=ssoToken, menu_id=11, module_id=26),
        headers=headers,
    )
    r = session.get(COMPANIES_URL, headers=headers)

    soup = bs(r.text, features="xml")
    xml_string = soup.prettify()
    xml_encoded = xml_string.encode("utf-8")
    root = ET.fromstring(xml_encoded)

    fetched_companies = []
    for row in root.findall("row"):
        jd_args = safe_text(row.find("cell[4]")).split("'")[5].split('"')
        jnf_id, com_id, year = jd_args[1], jd_args[3], jd_args[5]

        additional_jd = f"https://erp.iitkgp.ac.in/TrainingPlacementSSO/JnfMoreDet.jsp?mode=jnfMoreDet&rollno={ROLL_NUMBER}&year={year}&com_id={com_id}&jnf_id={jnf_id}"
        ctc, jd = get_info(session, headers, additional_jd)

        company_details = f"https://erp.iitkgp.ac.in/TrainingPlacementSSO/TPComView.jsp?yop={year}&com_id={com_id}&user_type=SU"
        company_additional_details = f"https://erp.iitkgp.ac.in/TrainingPlacementSSO/AdmFilePDF.htm?type=COM&year={year}&com_id={com_id}"

        company_info = {
            "Name": safe_text(row.find("cell[1]")).split(">")[1].split("<")[0].strip(),
            "Job_Description": jd,
            "CTC": ctc
        }
        fetched_companies.append(company_info)

    store_list(fetched_companies)
    return fetched_companies



def store_list(companies):
    with open(COMPANIES_FILE, "w") as json_file:
        json.dump(companies, json_file, indent=2)

def get_info(session, headers, jd_url):
    jd_response = session.get(jd_url, headers=headers)
    html_content = jd_response.text.strip()
    soup = bs(html_content, "html.parser")

    row = soup.find_all("tr")[-1]
    column = row.find_all("td")[-1]
    ctc = column.text

    jd_heading = soup.find("h4", string="Job Description")
    jd = jd_heading.find_next_sibling("div").get_text(" ", strip=True)
    jd = " ".join(jd.split())
    
    return ctc, jd
