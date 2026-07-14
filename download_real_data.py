import requests
from pathlib import Path

def download_file(url: str, dest_path: Path):
    """Downloads a file from a URL to a destination path, handling SEC EDGAR user-agent requirements."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br"
    }
    print(f"Downloading {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(response.content)
        print(f"Successfully saved to {dest_path} ({len(response.content)} bytes)")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def main():
    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 1. Real 10-Q Filing: Amazon Q3 2024 10-Q PDF (from official AMZN Investor Relations portal)
    amzn_10q_url = "https://s2.q4cdn.com/299057126/files/doc_financials/2024/q3/AMZN-Q3-2024-10-Q.pdf"
    amzn_dest = data_dir / "real_amzn_10q.pdf"
    download_file(amzn_10q_url, amzn_dest)
    
    # 2. Real Investor Presentation: Tesla Q2 2024 Investor Update Slide Deck
    tsla_deck_url = "https://digitalassets.tesla.com/tesla-contents/image/upload/IR/TSLA-Q2-2024-Update.pdf"
    tsla_dest = data_dir / "real_tsla_deck.pdf"
    download_file(tsla_deck_url, tsla_dest)

if __name__ == "__main__":
    main()
