import env
import notice
import company

import requests
from datetime import datetime
import iitkgp_erp_login.erp as erp

headers = {
    "timeout": "20",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36",
}
session = requests.Session()

while True:
    now = datetime.now()
    print(
        f"================ <<: {now.strftime('%H:%M:%S %d-%m-%Y')} :>> ================",
        flush=True,
    )

    print("[ERP LOGIN]", flush=True)
    try:    
        _, ssoToken = erp.login(
            headers,
            session,
            ERPCREDS=env,
            LOGGING=True,
            SESSION_STORAGE_FILE=".session",
        )
    except erp.ErpLoginError as e:
        print(f"[ERP LOGIN FAILED] {e}", flush=True)
        if args.cron:
            break
        print("[RETRYING]", flush=True)
        continue

    company.fetch(session, headers, ssoToken)
    notices = notice.fetch(headers, session, ssoToken)
    break
