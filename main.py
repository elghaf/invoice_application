from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from fastapi.staticfiles import StaticFiles

# Initialize FastAPI
app = FastAPI()

# Set up templates folder for serving the HTML
templates = Jinja2Templates(directory="templates")

# After creating the FastAPI app
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define data models for invoice generation
class InvoiceItem(BaseModel):
    description: str
    unit: str
    quantity: int
    unit_price: float

class InvoiceData(BaseModel):
    client_name: str
    invoice_number: str
    date: str
    project: str
    client_phone: str
    items: List[InvoiceItem]
    total_ht: float
    tax: float
    total_ttc: float
    frame_number: str = ""

# Serve the HTML form at the root endpoint
@app.get("/", response_class=HTMLResponse)
async def serve_html(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Endpoint to generate PDF invoices
@app.post("/generate-invoice")
async def generate_invoice(data: InvoiceData):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    def draw_table_header(y_pos):
        # Draw header row with columns
        headers = ["Description", "Unité", "NBRE", "LNG/Qté", "P.U", "Total HT"]
        col_widths = [250, 35, 35, 50, 50, 80]  # Reduced widths
        x = 50
        
        # Draw header cells
        for header, width in zip(headers, col_widths):
            pdf.setFillColorRGB(0.2, 0.4, 0.6)
            pdf.rect(x, y_pos, width, 20, fill=1, stroke=1)
            pdf.setFillColorRGB(1, 1, 1)
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(x + 5, y_pos + 7, header)
            x += width
        
        return y_pos - 20

    def draw_section_header(y_pos, title):
        pdf.setFillColorRGB(0.2, 0.4, 0.6)
        pdf.rect(50, y_pos, page_width-100, 20, fill=1, stroke=1)
        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(60, y_pos + 6, title)
        return y_pos - 20

    def draw_items(items, y_pos, indent=False):
        start_y = y_pos
        col_widths = [250, 35, 35, 50, 50, 80]  # Match header widths
        
        for item in items:
            x = 50
            # Draw row background
            for width in col_widths:
                pdf.rect(x, y_pos, width, 20, stroke=1, fill=0)
                x += width
            
            # Draw content
            x = 50
            pdf.setFillColorRGB(0, 0, 0)
            pdf.setFont("Helvetica", 9)
            
            # Add indent for description if needed
            desc_x = x + (20 if indent else 5)  # Reduced indent
            pdf.drawString(desc_x, y_pos + 7, item.description)
            
            values = [
                item.unit,
                str(item.quantity),
                f"{item.unit_price:.2f}",
                f"{item.unit_price:.2f}",
                f"{(item.quantity * item.unit_price):.2f}"
            ]
            
            x += col_widths[0]  # Move past description column
            for value, width in zip(values, col_widths[1:]):
                pdf.drawString(x + 5, y_pos + 7, value)
                x += width
            
            y_pos -= 20
        
        return y_pos

    def draw_vertical_lines(start_y, end_y):
        x = 50
        col_widths = [180, 50, 50, 70, 70, 100]
        for width in col_widths:
            pdf.line(x, start_y, x, end_y)
            x += width
        pdf.line(x, start_y, x, end_y)

    # Add logo with smaller dimensions
    pdf.drawImage("static/logo.png", 50, page_height - 65, width=100, height=40)  # Reduced size
    
    # Header Section with smaller font
    pdf.setFont("Helvetica-Bold", 24)  # Reduced from 28
    pdf.drawString(page_width - 150, page_height - 55, "DEVIS")

    # Document Info Boxes (left side) - moved up and made smaller
    y = page_height - 120  # Moved up from -130
    box_width = 220  # Reduced from 250
    box_height = 22  # Reduced from 25
    box_spacing = 24  # Reduced from 27

    # Function to draw info box with border
    def draw_info_box(label, value, y_pos):
        # Draw blue background
        pdf.setFillColorRGB(0.2, 0.4, 0.6)
        pdf.rect(50, y_pos, box_width, box_height, fill=1, stroke=1)
        
        # Add white text with smaller font
        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont("Helvetica-Bold", 9)  # Reduced from 10
        pdf.drawString(60, y_pos + 7, label)  # Adjusted y offset
        pdf.setFont("Helvetica", 9)
        pdf.drawString(160, y_pos + 7, value)

    # Draw document info boxes with consistent spacing
    draw_info_box("Date du devis:", data.date, y)
    draw_info_box("N° Devis:", data.invoice_number, y - box_spacing)
    draw_info_box("PLANCHER:", "PH RDC", y - (box_spacing * 2))

    # Client Info Box (right-aligned with border) - made smaller
    info_box_width = 220  # Reduced from 250
    info_box_height = 90  # Reduced from 100
    info_box_x = page_width - info_box_width - 50
    info_box_y = page_height - 90  # Moved up from -100
    
    # Draw client info box with border and slight gray background
    pdf.setFillColorRGB(0.98, 0.98, 0.98)
    pdf.rect(info_box_x, info_box_y - info_box_height, info_box_width, info_box_height, stroke=1, fill=1)
    
    # Client Info Content with reduced spacing
    y = info_box_y - 18  # Adjusted from -20
    line_spacing = 22  # Reduced from 25
    
    # Function to add info line with better alignment and smaller font
    def add_info_line(label, value, y_pos):
        pdf.setFillColorRGB(0, 0, 0)
        pdf.setFont("Helvetica-Bold", 9)  # Reduced from 10
        pdf.drawString(info_box_x + 10, y_pos, label)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(info_box_x + 100, y_pos, value)  # Adjusted from 120
    
    # Add client information with consistent spacing
    add_info_line("Nom:", data.client_name, y)
    add_info_line("Type d'ouvrage:", data.project, y - line_spacing)
    add_info_line("Lieu:", "BAB ATLAS", y - (line_spacing * 2))
    add_info_line("Telephone:", data.client_phone, y - (line_spacing * 3))

    # Update y position for the rest of the document
    y = page_height - 120 - (box_spacing * 3)  # Align with the bottom of info boxes

    # Adjust spacing before tables
    y -= 10  # Reduced from 15
    
    # Group items by section
    poutrelles_items = [i for i in data.items if "PCP" in i.description]
    hourdis_items = [i for i in data.items if "HOURDIS" in i.description]
    panneaux_items = [i for i in data.items if "TRS" in i.description]
    
    # Draw sections
    sections = [
        (poutrelles_items, "POUTRELLES", False),
        (hourdis_items, "HOURDIS", True),
        (panneaux_items, "PANNEAU TREILLIS SOUDES", True)
    ]

    # Draw table header once
    y = draw_table_header(y)

    # Draw all sections
    for items, title, indent in sections:
        # Draw section title
        pdf.setFillColorRGB(0, 0, 0)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(55, y + 7, title)
        
        # Draw items with or without indent
        y = draw_items(items, y - 20, indent)

    # Footer Totals with compressed styling
    y = max(50, y - 20)
    
    # Add N° Cadre box on the left side
    pdf.setFillColorRGB(1, 1, 1)  # White background
    pdf.rect(50, y - 50, 150, 70, stroke=1)  # Draw box for N° Cadre
    pdf.setFillColorRGB(0, 0, 0)  # Black text
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(60, y - 20, "N° Cadre:")
    
    # Totals box on the right side
    pdf.setFillColorRGB(0.2, 0.4, 0.6)
    pdf.rect(page_width - 300, y - 50, 250, 70, fill=1)
    
    pdf.setFillColorRGB(1, 1, 1)
    y_offset = 0
    for label, value in [
        ("Total H.T", f"{data.total_ht:.2f} DH"),
        ("TVA 20%", f"{data.tax:.2f} DH"),
        ("Total TTC", f"{data.total_ttc:.2f} DH")
    ]:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(page_width - 280, y - y_offset, label)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(page_width - 150, y - y_offset, value)
        y_offset += 20

    # Add validity notice after the boxes
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(50, y - 80, "Validité du devis: 1 MOIS")

    # Add company details in the footer
    # Left side contact info
    pdf.setFont("Helvetica", 8)
    pdf.drawString(50, 20, "L'OPTIMALE")
    pdf.drawString(50, 12, "06 66 24 50 15")

    # Center address block
    center_text = "Douar Ait Laarassi Tidili, Cercle El Kelâa, Route de Safi, Km 14-40000 Marrakech"
    center_contact = "Tél: 05 24 01 55 54 Fax : 05 24 01 55 29 E-mail : compra45@gmail.com"
    
    # Calculate center position
    center_x = page_width / 2
    pdf.drawCentredString(center_x, 20, center_text)
    pdf.drawCentredString(center_x, 12, center_contact)

    # Right side page number
    pdf.drawString(page_width - 60, 12, "1")

    pdf.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=devis.pdf"}
    )

