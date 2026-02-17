from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import DailyRate
from datetime import date
from decimal import Decimal, InvalidOperation
import re
import urllib.request
import urllib.error
import logging
import os

# Optional deps
try:
    import requests  # type: ignore
    from bs4 import BeautifulSoup  # type: ignore
    HAS_SOUP = True
except Exception:
    HAS_SOUP = False

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch gold and silver rates from FENEGOSIDA'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true', dest='dry_run', help='Print detected rates without saving'
        )

    def handle(self, *args, **options):
        try:
            # Primary source: FENEGOSIDA official website. Override via GOLD_RATE_URL if needed.
            url = os.environ.get(
                'GOLD_RATE_URL',
                'https://fenegosida.org/'
            )
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            # Respect proxy and custom CA bundles for corporate networks
            proxy_https = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            proxy_http = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            proxies = {}
            if proxy_https:
                proxies['https'] = proxy_https
            if proxy_http:
                proxies['http'] = proxy_http
            ca_bundle = os.environ.get('REQUESTS_CA_BUNDLE') or os.environ.get('SSL_CERT_FILE')

            req = urllib.request.Request(url, headers=headers)
            
            page_text = None
            soup = None

            if HAS_SOUP:
                try:
                    verify_arg = ca_bundle if ca_bundle else True
                    resp = requests.get(url, headers=headers, timeout=10, proxies=proxies or None, verify=verify_arg)
                    resp.raise_for_status()
                    page_text = resp.text
                    soup = BeautifulSoup(page_text, 'html.parser')
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Requests failed: {e}. Falling back to urllib...")
                    pass
            
            if page_text is None:
                try:
                    # urllib respects *_PROXY env vars automatically. If explicit proxies provided, use an opener.
                    if proxies:
                        proxy_handler = urllib.request.ProxyHandler(proxies)
                        opener = urllib.request.build_opener(proxy_handler)
                        with opener.open(req, timeout=10) as response:
                            page_text = response.read().decode('utf-8', errors='ignore')
                    else:
                        with urllib.request.urlopen(req, timeout=10) as response:
                            page_text = response.read().decode('utf-8', errors='ignore')
                except urllib.error.HTTPError as e:
                    logger.error(f"HTTP Error {e.code}: {e.reason} - Network error")
                    self.stdout.write(self.style.ERROR(f"Error fetching rates: Network error - {e}"))
                    return
                except urllib.error.URLError as e:
                    logger.error(f"URL Error: {e.reason}")
                    self.stdout.write(self.style.ERROR(f"Error fetching rates: Network error - {e}"))
                    return
            
            # Normalize whitespace and Devanagari digits
            page_text = page_text.replace('\xa0', ' ')
            page_text = re.sub(r"\s+", " ", page_text)

            def normalize_digits(s: str) -> str:
                devanagari = '०१२३४५६७८९'
                ascii = '0123456789'
                mapping = {devanagari[i]: ascii[i] for i in range(10)}
                return ''.join(mapping.get(ch, ch) for ch in s)

            def convert_bs_date_to_iso(date_str: str) -> str:
                """Convert '11 Poush 2082' to '2082-09-11' (BS month index)."""
                month_map = {
                    'baisakh': '01', 'baishakh': '01',
                    'jestha': '02', 'jeth': '02',
                    'ashadh': '03', 'asar': '03',
                    'shrawan': '04', 'sawan': '04',
                    'bhadra': '05', 'bhadau': '05',
                    'ashwin': '06', 'asoj': '06',
                    'kartik': '07', 'kartick': '07',
                    'mangsir': '08', 'mangshir': '08',
                    'poush': '09', 'paush': '09',
                    'magh': '10',
                    'falgun': '11', 'phalgun': '11',
                    'chaitra': '12', 'chait': '12',
                }
                # Normalize digits and collapse whitespace
                cleaned = normalize_digits(date_str).strip()
                m = re.match(r"(\d{1,2})\s+([A-Za-z\u0900-\u097F]+)\s+(20\d{2})", cleaned, re.IGNORECASE)
                if not m:
                    return cleaned
                day, month_raw, year = m.groups()
                month_key = month_raw.lower()
                month_num = month_map.get(month_key)
                if not month_num:
                    return cleaned
                # Ensure day is two digits
                day = day.zfill(2)
                return f"{year}-{month_num}-{day}"

            # Extract Nepali date (e.g., '11 Poush 2082' or '११ पौष २०८२')
            bs_date = None
            visible_content = page_text[:5000]

            # First try BeautifulSoup to read the rate-date/post element if present
            if soup is not None:
                rate_date_el = soup.select_one('.rate-date') or soup.select_one('.rate-date.post') or soup.select_one('.post .rate-date')
                if rate_date_el:
                    txt = rate_date_el.get_text(separator=' ', strip=True)
                    txt = txt.replace('Date :', '').replace('Date:', '').strip()
                    if txt and not re.search(r"N/?A|None|null", txt, re.IGNORECASE):
                        bs_date = normalize_digits(txt)
                        bs_date = bs_date.strip()
            
            # Try multiple patterns for BS date
            # Pattern 1: English format with various month spellings
            m_date = re.search(
                r"(\d{1,2}\s+(?:Baisakh|Baishakh|Jestha|Jeth|Ashadh|Asar|Shrawan|Sawan|Bhadra|Bhadau|Ashwin|Asoj|Kartik|Kartick|Mangsir|Mangshir|Poush|Paush|Magh|Falgun|Phalgun|Chaitra|Chait)\s+20\d{2})",
                visible_content,
                re.IGNORECASE
            )
            if m_date:
                bs_date = normalize_digits(m_date.group(1))
            
            # Pattern 2: Devanagari date pattern (XX month 208X)
            if not bs_date:
                m_date2 = re.search(r"([०-९]{1,2}\s+[\u0900-\u097F]+\s+२०[७८९][०-९])", visible_content)
                if m_date2:
                    bs_date = normalize_digits(m_date2.group(1))
            
            # Pattern 3: Date near rate info (DD Month 20XX)
            if not bs_date:
                m_date3 = re.search(r"(?:Today|Date|Rate).{0,50}?(\d{1,2}\s+[A-Za-z]{4,10}\s+20\d{2})", visible_content, re.IGNORECASE)
                if m_date3:
                    candidate = m_date3.group(1)
                    if not re.search(r"N/?A|None|null", candidate, re.IGNORECASE):
                        bs_date = normalize_digits(candidate)

            # Pattern 4: Numeric date like 12/26/2025 or 26-12-2025
            if not bs_date:
                m_date4 = re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]20\d{2}\b", visible_content)
                if m_date4:
                    bs_date = normalize_digits(m_date4.group(0))

            # Pattern 5: Any isolated BS year 208x with up to 12 chars of context
            if not bs_date:
                m_year = re.search(r"20(?:7|8|9)\d", visible_content)
                if m_year:
                    start = max(0, m_year.start() - 12)
                    end = min(len(visible_content), m_year.end() + 12)
                    candidate = visible_content[start:end].strip()
                    if not re.search(r"N/?A|None|null", candidate, re.IGNORECASE):
                        bs_date = normalize_digits(candidate)

            if bs_date:
                bs_date = bs_date.strip()
                bs_date = convert_bs_date_to_iso(bs_date)
            
            # Extract per TOLA rates only
            gold_tola_str = None
            silver_tola_str = None

            def find_amount(patterns):
                for pat in patterns:
                    last_match = None
                    for m in re.finditer(pat, page_text, re.IGNORECASE | re.DOTALL):
                        last_match = m
                    if last_match:
                        return normalize_digits(last_match.group(1)).replace(',', '')
                return None

            # FENEGOSIDA format: "FINE GOLD (9999)per 1 tolaरु 301900"
            gold_tola_str = find_amount([
                r"FINE\s*GOLD\s*\(9999\)[^\n\r]*?per\s*1\s*tola[^\n\r]*?(?:रु|Rs\.?|NRs\.?)\s*([0-9][0-9,\.]+)",
                r"Hallmark\s*Gold[^\n\r]*?(?:NRs\.?|Nrs\.?|Rs\.?|रु)\s*([0-9][0-9,\.]+)",
                r"Fine\s*Gold[^\n\r]*?(?:NRs\.?|Nrs\.?|Rs\.?|रु)\s*([0-9][0-9,\.]+)",
                r"Gold\s*\(9999\)[^\n\r]*?(?:NRs\.?|Nrs\.?|Rs\.?|रु)\s*([0-9][0-9,\.]+)",
                r"Gold[^\n\r]*?Tola[^\n\r]*?(?:NRs\.?|Nrs\.?|Rs\.?|रु)\s*([0-9][0-9,\.]+)",
            ])

            # FENEGOSIDA format: "SILVERper 1 tolaरु 4885"
            silver_tola_str = find_amount([
                r"SILVER[^\n\r]*?per\s*1\s*tola[^\n\r]*?(?:रु|Rs\.?|NRs\.?)\s*([0-9][0-9,\.]+)",
                r"Silver[^\n\r]*?Tola[^\n\r]*?(?:NRs\.?|Nrs\.?|Rs\.?|रु)\s*([0-9][0-9,\.]+)",
                r"Silver[^\n\r]*?(?:NRs\.?|Nrs\.?|Rs\.?|रु)\s*([0-9][0-9,\.]+)",
            ])

            # Fallback to original FENEGOSIDA patterns if needed
            if not gold_tola_str or not silver_tola_str:
                m_gold = re.search(
                    r"FINE\s*GOLD\s*\(9999\).{0,200}?per\s*1\s*tola[^0-9]*([0-9,]+)",
                    page_text,
                    re.IGNORECASE | re.DOTALL
                )
                if m_gold and not gold_tola_str:
                    gold_tola_str = normalize_digits(m_gold.group(1)).replace(',', '')
                if m_gold:
                    silver_search_start = m_gold.end()
                    page_text_after_gold = page_text[silver_search_start:]
                    m_silver = re.search(
                        r"SILVER.{0,200}?per\s*1\s*tola[^0-9]*([0-9,]+)",
                        page_text_after_gold,
                        re.IGNORECASE | re.DOTALL
                    )
                    if m_silver and not silver_tola_str:
                        silver_tola_str = normalize_digits(m_silver.group(1)).replace(',', '')
            
            # Proceed only if both rates found
            if gold_tola_str and silver_tola_str:
                try:
                    # Convert per tola strings to Decimal
                    gold_tola = Decimal(gold_tola_str).quantize(Decimal('1.00'))
                    silver_tola = Decimal(silver_tola_str).quantize(Decimal('1.00'))
                except (InvalidOperation, ValueError) as e:
                    self.stdout.write(
                        self.style.ERROR(f'Could not convert tola rates to Decimal: Gold={gold_tola_str}, Silver={silver_tola_str} ({e})')
                    )
                    return

                # Compute per 10g from per tola (1 tola = 11.664g)
                factor_10g = (Decimal('10') / Decimal('11.664'))
                gold_10g = (gold_tola * factor_10g).quantize(Decimal('1.00'))
                silver_10g = (silver_tola * factor_10g).quantize(Decimal('1.00'))

                if options.get('dry_run'):
                    self.stdout.write(self.style.SUCCESS(
                        f'DRY RUN → Gold (tola) रु{gold_tola}, Silver (tola) रु{silver_tola}; BS Date: {bs_date or "N/A"}'
                    ))
                    return

                today = date.today()
                # Use bs_date as unique identifier since there's no date field
                rate, created = DailyRate.objects.update_or_create(
                    bs_date=bs_date or today.isoformat(),
                    defaults={
                        'gold_rate': gold_tola,
                        'silver_rate': silver_tola,
                        'gold_rate_10g': gold_10g,
                        'silver_rate_10g': silver_10g,
                    }
                )

                action = "Created" if created else "Updated"
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{action} rates for {today} (BS {bs_date or "N/A"}): Gold (tola) रु{gold_tola}, Silver (tola) रु{silver_tola}'
                    )
                )
            else:
                # If today's rates not found, try to use yesterday's rates as fallback
                from datetime import timedelta
                yesterday = date.today() - timedelta(days=1)
                yesterday_rate = DailyRate.objects.order_by('-created_at').first()
                
                if yesterday_rate:
                    today = date.today()
                    rate, created = DailyRate.objects.update_or_create(
                        bs_date=bs_date or today.isoformat(),
                        defaults={
                            'gold_rate': yesterday_rate.gold_rate,
                            'silver_rate': yesterday_rate.silver_rate,
                            'gold_rate_10g': yesterday_rate.gold_rate_10g,
                            'silver_rate_10g': yesterday_rate.silver_rate_10g,
                        }
                    )
                    
                    action = "Created" if created else "Updated"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'{action} today\'s rates using yesterday\'s data: Gold (tola) रु{yesterday_rate.gold_rate}, Silver (tola) रु{yesterday_rate.silver_rate}'
                        )
                    )
                else:
                    # In dry-run, show a snippet of the page to aid debugging patterns
                    if options.get('dry_run'):
                        snippet = page_text[:800]
                        self.stdout.write(self.style.WARNING(
                            f'Could not extract rates. Gold tola: {gold_tola_str}, Silver tola: {silver_tola_str}\nSnippet:\n{snippet}'
                        ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'Could not extract rates and no yesterday\'s rate found. Gold tola: {gold_tola_str}, Silver tola: {silver_tola_str}'
                        ))
            
        except urllib.error.URLError as e:
            self.stdout.write(
                self.style.ERROR(f'Error fetching rates: Network error - {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error fetching rates: {str(e)}')
            )


    