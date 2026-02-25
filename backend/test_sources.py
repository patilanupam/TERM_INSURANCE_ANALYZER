import requests
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36'}
sites = [
    ('BankBazaar', 'https://www.bankbazaar.com/insurance/term-insurance.html'),
    ('Coverfox', 'https://www.coverfox.com/life-insurance/term-life-insurance/'),
    ('Paisabazaar', 'https://www.paisabazaar.com/term-insurance/'),
    ('IRDAI', 'https://www.irdai.gov.in/admincms/cms/frmGeneral_Layout.aspx?page=PageNo4017&flag=1'),
    ('Finbull', 'https://finbull.in/term-insurance/'),
    ('MyInsuranceClub', 'https://www.myinsuranceclub.com/life-insurance/term-insurance'),
]
for name, url in sites:
    try:
        r = requests.get(url, headers=headers, timeout=10)
        ct = r.headers.get('content-type', '')[:30]
        print(f"{name}: {r.status_code} | size={len(r.text)} | {ct}")
    except Exception as e:
        print(f"{name}: ERROR - {str(e)[:60]}")
