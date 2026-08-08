import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# List of queries to verify each registered source
studies_to_verify = [
    {
        "source_id": "SRC-FREE-001",
        "title": "Relationships of stroke rate, distance per stroke, and velocity in competitive swimming",
        "authors": ["Craig, AB", "Pendergast, DR"],
        "year": 1979,
        "query": "Relationships of stroke rate, distance per stroke, and velocity in competitive swimming Craig Pendergast"
    },
    {
        "source_id": "SRC-FREE-002",
        "title": "A new method for analyzing arm stroke coordination in front crawl swimming",
        "authors": ["Chollet, D", "Chalies, S", "Chatard, JC"],
        "year": 2000,
        "query": "A new method for analyzing arm stroke coordination in front crawl swimming Chollet"
    },
    {
        "source_id": "SRC-FREE-003",
        "title": "Body roll in swimming: A review",
        "authors": ["Psycharakis, SG", "Sanders, RH"],
        "year": 2010,
        "query": "Body roll in swimming A review Psycharakis Sanders"
    },
    {
        "source_id": "SRC-FREE-004",
        "title": "Effect of Age, Sex, and Race Distance on Front Crawl Stroke Parameters in Subelite Adolescent Swimmers During Competition",
        "authors": ["Dormehl, SJ", "Osborough, CD"],
        "year": 2015,
        "query": "Effect of Age Sex and Race Distance on Front Crawl Stroke Parameters in Subelite Adolescent Swimmers Dormehl"
    },
    {
        "source_id": "SRC-BACK-001",
        "title": "Kinematic characterization of backstroke swimming in young competitive swimmers",
        "authors": ["Cortesi, M", "Gatta, G", "Michielon, G", "Di Michele, R"],
        "year": 2020,
        "query": "Kinematic characterization of backstroke swimming in young competitive swimmers Cortesi Gatta"
    },
    {
        "source_id": "SRC-BACK-002",
        "title": "Shoulder and hip roll in backstroke swimming",
        "authors": ["Psycharakis, SG", "Sanders, RH"],
        "year": 2008,
        "query": "Shoulder and hip roll in backstroke swimming Psycharakis Sanders"
    },
    {
        "source_id": "SRC-BREAST-001",
        "title": "Energy cost and stroke mechanics of competitive breaststroke swimming",
        "authors": ["Capelli, C", "Pendergast, DR", "Termin, B"],
        "year": 1998,
        "query": "Energy cost and stroke mechanics of competitive breaststroke swimming Capelli"
    },
    {
        "source_id": "SRC-BREAST-002",
        "title": "Inter-limb coordination and spatial-temporal parameters in breaststroke",
        "authors": ["Seifert, L", "Leblanc, H", "Chollet, D"],
        "year": 2011,
        "query": "Inter limb coordination and spatial temporal parameters in breaststroke Seifert Leblanc"
    },
    {
        "source_id": "SRC-FLY-001",
        "title": "Differences in spatial-temporal parameters and arm-leg coordination in butterfly stroke as a function of race pace, skill and gender",
        "authors": ["Seifert, L", "Boulesteix, L", "Chollet, D", "Vilas-Boas, JP"],
        "year": 2008,
        "query": "Differences in spatial temporal parameters and arm leg coordination in butterfly stroke Seifert"
    },
    {
        "source_id": "SRC-MASTERS-001",
        "title": "The determinants of performance in master swimmers: a cross-sectional study on the age-related changes in propelling efficiency, hydrodynamic position and energy cost of front crawl",
        "authors": ["Zamparo, P", "Dall'ora, A", "Toneatto, A", "Cortesi, M"],
        "year": 2012,
        "query": "determinants of performance in master swimmers age related changes propelling efficiency Zamparo"
    },
    {
        "source_id": "SRC-YOUTH-001",
        "title": "Kinematic changes during a 400-m front crawl in young swimmers",
        "authors": ["Barbosa, TM", "Silva, AJ", "Reis, AM", "Vilas-Boas, JP"],
        "year": 2010,
        "query": "Kinematic changes during a 400 m front crawl in young swimmers Barbosa"
    },
    {
        "source_id": "SRC-GONJO-2018",
        "title": "Kinematic and kinetic differences between front crawl and backstroke swimming",
        "authors": ["Gonjo, T", "Sanders, R"],
        "year": 2018,
        "query": "Gonjo Sanders swimming kinematic kinetic front crawl backstroke"
    }
]

audit_results = []

for item in studies_to_verify:
    sid = item["source_id"]
    q = urllib.parse.quote(item["query"])
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={q}&retmode=json&retmax=5"
    
    req = urllib.request.Request(search_url, headers={'User-Agent': 'SwimAnalyzerAI/1.0'})
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            pmids = data.get("esearchresult", {}).get("idlist", [])
            
            if pmids:
                fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={','.join(pmids)}&retmode=xml"
                freq = urllib.request.Request(fetch_url, headers={'User-Agent': 'SwimAnalyzerAI/1.0'})
                with urllib.request.urlopen(freq, context=ctx) as fresp:
                    xml_data = fresp.read()
                    root = ET.fromstring(xml_data)
                    found_match = False
                    
                    for art in root.findall('.//PubmedArticle'):
                        pmid = art.findtext('.//PMID')
                        title = art.findtext('.//ArticleTitle') or ''
                        journal = art.findtext('.//Journal/Title') or ''
                        year = art.findtext('.//JournalIssue/PubDate/Year') or art.findtext('.//JournalIssue/PubDate/MedlineDate') or ''
                        doi = None
                        pmc_id = None
                        for el in art.findall('.//ArticleId'):
                            if el.attrib.get('IdType') == 'doi':
                                doi = el.text
                            elif el.attrib.get('IdType') == 'pmc':
                                pmc_id = el.text

                        authors = []
                        for author in art.findall('.//Author'):
                            last = author.findtext('LastName') or ''
                            initials = author.findtext('Initials') or ''
                            if last:
                                authors.append(f"{last}, {initials}".strip())

                        # Check title similarity
                        t_lower = title.lower()
                        item_t_lower = item["title"].lower()
                        
                        if item["authors"][0].split(',')[0].lower() in [a.split(',')[0].lower() for a in authors] or \
                           any(w in t_lower for w in item_t_lower.split()[:4]):
                            audit_results.append({
                                "source_id": sid,
                                "searched_title": item["title"],
                                "verified_pmid": pmid,
                                "verified_doi": doi,
                                "verified_pmcid": pmc_id,
                                "verified_title": title,
                                "verified_authors": authors[:4],
                                "verified_year": year,
                                "verified_journal": journal,
                                "matched": True
                            })
                            found_match = True
                            break
                    if not found_match:
                        audit_results.append({
                            "source_id": sid,
                            "searched_title": item["title"],
                            "matched": False,
                            "pmids_found": pmids
                        })
            else:
                audit_results.append({
                    "source_id": sid,
                    "searched_title": item["title"],
                    "matched": False,
                    "reason": "No search results"
                })
    except Exception as e:
        print(f"Error auditing {sid}: {e}")

print(json.dumps(audit_results, indent=2))
