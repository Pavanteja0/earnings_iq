import fitz  # PyMuPDF
from pathlib import Path

def generate_sample_pdf(file_path: Path, pages_content: list):
    """Generates a PDF file with multiple pages of text using PyMuPDF."""
    doc = fitz.open()
    for idx, content in enumerate(pages_content):
        # Create a letter-size page
        page = doc.new_page(width=612, height=792)
        
        # Insert a header
        page.insert_text((50, 40), f"Acme Corporation Q3 Fiscal 2026 Materials", fontsize=9, color=(0.5, 0.5, 0.5))
        
        # Insert main content
        y_offset = 80
        for line in content.split("\n"):
            if not line.strip():
                y_offset += 15
                continue
            
            # Formatting headings vs text
            if line.startswith("ITEM") or line.startswith("SLIDE") or line.startswith("PART"):
                fontsize = 14
                fontcolor = (0.1, 0.2, 0.5)
                y_offset += 10
            elif line.startswith("###") or line.startswith("####"):
                line = line.replace("#", "").strip()
                fontsize = 12
                fontcolor = (0.2, 0.3, 0.6)
                y_offset += 5
            else:
                fontsize = 10
                fontcolor = (0.1, 0.1, 0.1)
                
            page.insert_text((50, y_offset), line.strip(), fontsize=fontsize, color=fontcolor)
            y_offset += 18
            
            # Create new page if we run out of vertical space
            if y_offset > 720:
                page = doc.new_page(width=612, height=792)
                page.insert_text((50, 40), f"Acme Corporation Q3 Fiscal 2026 Materials (cont.)", fontsize=9, color=(0.5, 0.5, 0.5))
                y_offset = 80
                
        # Insert page footer
        page.insert_text((280, 750), f"Page {idx + 1}", fontsize=8, color=(0.6, 0.6, 0.6))
        
    doc.save(file_path)
    doc.close()
    print(f"Generated PDF: {file_path}")

def main():
    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 1. Generate 10-Q PDF
    pdf_10q_content = [
        # Page 1
        "PART I. FINANCIAL INFORMATION\n\n"
        "ITEM 1. FINANCIAL STATEMENTS\n\n"
        "ACME CORPORATION\n"
        "CONSOLIDATED STATEMENTS OF OPERATIONS (UNAUDITED)\n"
        "For the Three Months Ended June 30, 2026 and 2025\n\n"
        "Revenue: Q3 2026 was $12,448 million compared to $11,316 million in Q3 2025 (+10.0% growth YoY).\n"
        "Cost of revenue: Q3 2026 was $6,946 million compared to $6,394 million in Q3 2025.\n"
        "Gross Profit: Q3 2026 was $5,502 million compared to $4,922 million in Q3 2025.\n"
        "Net income: Q3 2026 was $1,822 million compared to $1,641 million in Q3 2025 (+11.0% growth YoY).\n"
        "Diluted earnings per share (EPS): Q3 2026 was $0.88 compared to $0.78 in Q3 2025 (+12.8% growth YoY).\n"
        "Weighted average shares outstanding (diluted): 2,070 million in Q3 2026.",
        
        # Page 2
        "ITEM 2. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS\n\n"
        "Operating Margins Discussion:\n"
        "Gross profit margin for Q3 2026 expanded to 44.2% compared to 43.5% in the prior year quarter, representing an expansion of 70 basis points (YoY). This margin performance reflects strong software pricing power offset by higher initial server setup costs.\n"
        "Operating income was $2,303 million (18.5% operating margin) compared to $2,014 million (17.8% operating margin) in Q3 2025, which represents 70 basis points YoY operating margin expansion.\n\n"
        "Segment Revenue Performance:\n"
        "- Cloud Division Services: Q3 2026 revenue was $5,120 million (representing 41.1% of total revenue), an increase of 15.5% YoY compared to $4,433 million in Q3 2025.\n"
        "- Enterprise Hardware: Q3 2026 revenue was $4,848 million (39.0% of total), an increase of 4.2% YoY compared to $4,653 million in Q3 2025.\n"
        "- Consumer Devices: Q3 2026 revenue was $2,480 million (19.9% of total), an increase of 11.2% YoY compared to $2,230 million in Q3 2025.",
        
        # Page 3
        "ITEM 3. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK\n\n"
        "Balance Sheet & Liquidity:\n"
        "As of June 30, 2026, Cash and cash equivalents were $8,450 million compared to $7,900 million as of December 31, 2025. Total long-term debt was stable at $3,200 million.\n"
        "Operating cash flows for the nine months ended June 30, 2026 grew to $2,150 million, up from $1,920 million in the prior year period.\n"
        "We believe our liquidity profile and strong cash reserves are sufficient to cover anticipated Capital Expenditures associated with cloud capacity expansions."
    ]
    generate_sample_pdf(data_dir / "sample_acme_10q.pdf", pdf_10q_content)
    
    # 2. Generate Investor Presentation PDF
    deck_content = [
        # Slide 1
        "SLIDE 1: ACME CORPORATION Q3 2026 PERFORMANCE\n\n"
        "Acme Corp. Q3 Fiscal 2026 Financial Results\n"
        "Accelerating Cloud & Enterprise Strategy\n"
        "July 14, 2026\n\n"
        "Key Themes:\n"
        "- Double-digit top-line revenue expansion (+10% YoY)\n"
        "- Software and SaaS transitions accelerating\n"
        "- Continuing platform scale investments",
        
        # Slide 2
        "SLIDE 2: CLOUD & ENTERPRISE GROWTH DYNAMICS\n\n"
        "SaaS segment momentum continues:\n"
        "- Cloud Division Services reached $5.12B, up 15.5% YoY.\n"
        "- Represents 41.1% of total corporate revenues (up from 39.2% in Q3 2025).\n"
        "- Active enterprise subscriber count grew by 18% YoY.\n"
        "Capital Infrastructure Buildout:\n"
        "- Dedicated AI and GPU server deployments scheduled for Q4 2026 and FY 2027 to scale cloud capability.",
        
        # Slide 3
        "SLIDE 3: FISCAL OUTLOOK & Q4 GUIDANCE\n\n"
        "Guidance Outlook for Q4 Fiscal 2026:\n"
        "- Q4 Revenue guided to a range of $12.80 billion to $13.10 billion (+5.0% YoY at midpoint).\n"
        "- Operating margin target of 19.0% to 19.5%.\n"
        "- CapEx estimated at $1.2B to support Cloud capacity expansion.\n\n"
        "Growth Pillars:\n"
        "- Converting legacy on-premise hardware clients to high-value cloud contracts."
    ]
    generate_sample_pdf(data_dir / "sample_acme_deck.pdf", deck_content)
    
    # 3. Generate Call Transcript TXT
    transcript_text = (
        "Acme Corporation Q3 2026 Earnings Call Transcript\n"
        "Date: July 14, 2026\n\n"
        "--- MANAGEMENT REMARKS ---\n"
        "CEO (John Smith): Good afternoon, everyone. Q3 was an outstanding quarter for Acme. "
        "Our total revenue expanded 10% YoY to $12.45B, driven by our Cloud Division Services, which grew 15.5% YoY "
        "and now makes up over 41% of our business. We are successfully executing our multi-year strategic shift "
        "from legacy hardware sales to high-margin recurring cloud contracts.\n"
        "CFO (Sarah Jenkins): Thank you, John. Operating income reached $2,303 million, representing an operating "
        "margin of 18.5%. Our balance sheet remains robust, with cash reserves growing to $8.45 billion. "
        "We are guiding Q4 revenues to $12.8B to $13.1B, representing a solid growth outlook.\n\n"
        "--- ANALYST Q&A SESSION ---\n"
        "Toni Sacconaghi (Sanford Bernstein): Thank you for taking my question. Can you walk us through the gross margin "
        "dynamics? While Gross Profit Margin expanded YoY, it looks like it compressed by about 120 bps sequentially "
        "compared to Q2. What's driving that pressure in the Cloud division?\n"
        "CFO (Sarah Jenkins): [Pause of 3 seconds] Yes, Toni... as we expand, we are front-loading some CapEx and "
        "accelerating depreciation schedules on our older server generations. There is some near-term sequential "
        "pressure, but we expect gross margins to stabilize as capacity utilization matures.\n"
        "Katy Huberty (Morgan Stanley): Regarding your Q4 revenue guidance of $12.8B-$13.1B, that represents "
        "about 5% growth at the midpoint, which is a deceleration from the 10% we saw this quarter. Are you seeing "
        "customer pushback, or are there specific headwinds we should model?\n"
        "CEO (John Smith): Thanks, Katy. We are being prudent. In Europe, we have seen some enterprise customers "
        "elongating their procurement cycles, especially for hardware segments. Cloud remains strong, but our "
        "legacy hardware business faces some macroeconomic elongation headwinds in Europe, which prompts our "
        "conservative guidance stance."
    )
    
    with open(data_dir / "sample_acme_transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript_text)
    print(f"Generated Call Transcript: {data_dir / 'sample_acme_transcript.txt'}")

if __name__ == "__main__":
    main()
