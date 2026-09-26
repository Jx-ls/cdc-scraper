import logging
from utils import safe_text
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup as bs
from endpoints import TPSTUDENT_URL, NOTICEBOARD_URL, NOTICES_URL, ATTACHMENT_URL, NOTICE_CONTENT_URL


LAST_NOTICES_CHECK_COUNT = 30


def fetch(headers, session, ssoToken):
    print('[FETCHING NOTICES]', flush=True)
    try:
        r = session.post(TPSTUDENT_URL, data=dict(ssoToken=ssoToken, menu_id=11, module_id=26), headers=headers)
        r = session.get(NOTICEBOARD_URL, headers=headers)
        r = session.get(NOTICES_URL, headers=headers)
    except Exception as e:
        logging.error(f" Failed to navigate to Noticeboard ~ {str(e)}")
        return []

    try:
        soup = bs(r.text, features="xml")
        xml = soup.prettify().encode('utf-8')
        root = ET.fromstring(xml)
    except Exception as e:
        logging.error(f" Failed to extract data from Noticeboard ~ {str(e)}")
        return []

    notices = []
    for i, row in enumerate(root.findall('row')):

        id_ = safe_text(row.find('cell[1]'))
        year = safe_text(root.findall('row')[0].find('cell[8]')).split('"')[1].strip()

        notice = {
            "UID": f"{id_}_{year}",
            "Company": safe_text(row.find("cell[4]")),
            "Time": safe_text(row.find("cell[7]")),
            "Type": safe_text(row.find("cell[2]")),
            "Subject": safe_text(row.find("cell[3]"))
        }

        # Handling Body
        try:
            body_data = parse_body_data(session, year, id_)
            notice['BodyData'] = body_data
        except Exception as e:
            logging.error(f" Failed to parse notice body ~ {str(e)}")
            break

        # Handling attachment
        if (notice["Subject"] == "Result"):
            try:
                attachment = parse_attachment(session, year, id_)
                if attachment:
                    notice['Attachment'] = attachment
            except Exception as e:
                logging.error(f" Failed to parse attachment ~ {str(e)}")
                break

            notices.append(notice)
    return notices


def parse_body_data(session, year, id_):
    content = session.get(NOTICE_CONTENT_URL.format(year, id_))
    content_html = bs(content.text, 'html.parser')
    body_data = bs.find_all(content_html, 'div', {'id': 'printableArea'})[0]

    return body_data

import os

def parse_attachment(session, year, id_, save_folder="attachments"):
    # Ensure the save directory exists
    os.makedirs(save_folder, exist_ok=True)
    
    stream = session.get(ATTACHMENT_URL.format(year, id_), stream=True)
    
    # Attempt to get the original filename from the Content-Disposition header
    # Fallback to a generated name using the ID if the header is missing
    filename = f"notice_{year}_{id_}.pdf" # Default fallback
            
    filepath = os.path.join(save_folder, filename)
    
    # Write the stream to a local file in chunks
    with open(filepath, 'wb') as f:
        for chunk in stream.iter_content(chunk_size=4096):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                
    return filepath # Return the path instead of raw bytes
