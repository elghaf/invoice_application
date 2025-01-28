from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
from app.db.models import Invoice
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)

class InvoiceService:
    @staticmethod
    def generate_pdf(data: Invoice) -> bytes:
        try:
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            page_width, page_height = A4

            # Colors
            HEADER_BLUE = (0.29, 0.45, 0.68)
            WHITE = (1, 1, 1)
            BLACK = (0, 0, 0)

            # Get the absolute path to the logo file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(current_dir, "..", "static", "logo.png")

            # Top section layout
            top_margin = page_height - 120
            
            # Left side: Logo (smaller size to match design)
            if os.path.exists(logo_path):
                pdf.drawImage(logo_path, 50, top_margin, width=100, height=60)
            
            # Right side: DEVIS and Client Box
            # DEVIS text
            pdf.setFont("Helvetica-Bold", 48)
            devis_text = "DEVIS"
            devis_width = pdf.stringWidth(devis_text, "Helvetica-Bold", 48)
            devis_x = page_width - 200
            devis_y = top_margin + 40
            pdf.drawString(devis_x, devis_y, devis_text)

            # Client info box - moved down by adjusting the y position
            box_width = 200
            box_height = 80
            box_x = page_width - box_width - 50
            box_y = devis_y - 90  # Increased the offset from 60 to 90 to move box down

            # Draw client info box with border
            pdf.rect(box_x, box_y, box_width, box_height, stroke=1)

            # Client Info with centered alignment
            pdf.setFont("Helvetica-Bold", 10)
            client_info = [
                "STE ZELGHAT",
                "VILLA EN R+1",
                "BAB ATLAS",
                "05 61 92 96 28"
            ]

            # Center and draw each line of client info
            line_height = box_height / (len(client_info) + 1)
            for i, text in enumerate(client_info):
                text_width = pdf.stringWidth(text, "Helvetica-Bold", 10)
                x = box_x + (box_width - text_width) / 2
                y = box_y + box_height - ((i + 1) * line_height)
                pdf.drawString(x, y, text)

            # Info boxes (Date, N° Devis, PLANCHER)
            info_y = top_margin - 40
            for label, value in [
                ("Date du devis :", data.date.strftime("%d/%m/%Y")),
                ("N° Devis :", data.invoice_number),
                ("PLANCHER :", "PH RDC")
            ]:
                pdf.setFillColorRGB(*HEADER_BLUE)
                pdf.rect(50, info_y, 120, 20, fill=1)
                pdf.setFillColorRGB(*WHITE)
                pdf.drawString(55, info_y + 6, label)
                
                pdf.setFillColorRGB(*WHITE)
                pdf.rect(170, info_y, 80, 20, fill=1, stroke=1)
                pdf.setFillColorRGB(*BLACK)
                pdf.drawString(175, info_y + 6, str(value))
                info_y -= 25

            # Table headers
            table_y = info_y - 40
            headers = [
                ("Description", 250),
                ("Unité", 50),
                ("NBRE", 50),
                ("LNG/Qté", 60),
                ("P.U", 60),
                ("Total HT", 70)
            ]

            # Calculate total width
            total_width = sum(width for _, width in headers)
            
            # Draw header row
            current_x = 50
            pdf.setFillColorRGB(*HEADER_BLUE)
            pdf.rect(50, table_y, total_width, 20, fill=1)
            pdf.setFillColorRGB(*WHITE)
            pdf.setFont("Helvetica-Bold", 10)
            
            for title, width in headers:
                pdf.rect(current_x, table_y, width, 20, stroke=1)
                text_width = pdf.stringWidth(title, "Helvetica-Bold", 10)
                x = current_x + (width - text_width) / 2
                pdf.drawString(x, table_y + 6, title)
                current_x += width

            # Draw sections and items
            current_y = table_y - 20

            def draw_section_header(title):
                nonlocal current_y
                pdf.setFillColorRGB(*HEADER_BLUE)
                pdf.rect(50, current_y, total_width, 20, fill=1)
                pdf.setFillColorRGB(*WHITE)
                pdf.drawString(55, current_y + 6, title)
                current_y -= 20

            def draw_item_row(item, indent=False):
                nonlocal current_y
                pdf.setFillColorRGB(*BLACK)
                current_x = 50
                
                # Draw row background and borders
                pdf.setFillColorRGB(*WHITE)
                pdf.rect(50, current_y, total_width, 20, fill=1, stroke=1)
                
                # Draw cell values
                pdf.setFillColorRGB(*BLACK)
                cells = [
                    ("    " + item.description if indent else item.description, 250),
                    (item.unit, 50),
                    (str(item.quantity), 50),
                    (f"{item.length:.2f}", 60),
                    (f"{item.unit_price:.2f}", 60),
                    (f"{item.total_price:.2f}", 70)
                ]
                
                for value, width in cells:
                    pdf.rect(current_x, current_y, width, 20, stroke=1)
                    if isinstance(value, str) and value.startswith("    "):
                        pdf.drawString(current_x + 20, current_y + 6, value.strip())
                    else:
                        text_width = pdf.stringWidth(str(value), "Helvetica", 10)
                        x = current_x + (width - text_width) / 2
                        pdf.drawString(x, current_y + 6, str(value))
                    current_x += width
                
                current_y -= 20

            # Draw POUTRELLES section
            draw_section_header("POUTRELLES")
            poutrelles = [i for i in data.items if "PCP" in i.description]
            for item in poutrelles:
                draw_item_row(item)

            # Draw HOURDIS section
            draw_section_header("HOURDIS")
            hourdis = [i for i in data.items if "HOURDIS" in i.description]
            for item in hourdis:
                draw_item_row(item, indent=True)

            # Draw PANNEAU TREILLIS SOUDES section
            draw_section_header("PANNEAU TREILLIS SOUDES")
            treillis = [i for i in data.items if "TRS" in i.description]
            for item in treillis:
                draw_item_row(item, indent=True)

            # Totals section with updated design
            totals_y = current_y - 40
            
            # NB box on the left
            nb_box_width = 200
            nb_box_height = 60
            pdf.rect(50, totals_y - nb_box_height, nb_box_width, nb_box_height, stroke=1)
            
            # Totals boxes on the right
            totals_box_width = 200
            pdf.setFillColorRGB(*WHITE)
            
            # Draw totals with new design
            for i, (label, sublabel, value) in enumerate([
                ("Total", "H.T", f"{data.total_ht:.2f} DH"),
                ("TVA", "20 %", f"{data.tax:.2f} DH"),
                ("Total", "TTC", f"{data.total_ttc:.2f} DH")
            ]):
                y = totals_y - (i * 20)
                # Draw box
                pdf.rect(page_width - totals_box_width - 50, y, totals_box_width, 20, stroke=1)
                # Draw text
                pdf.setFillColorRGB(*BLACK)
                pdf.setFont("Helvetica-Bold", 10)
                text_width = pdf.stringWidth(f"{label}    {sublabel}", "Helvetica-Bold", 10)
                pdf.drawString(page_width - totals_box_width - 40, y + 6, f"{label}    {sublabel}")
                pdf.drawRightString(page_width - 60, y + 6, value)

            # Validity note
            pdf.setFont("Helvetica", 10)
            pdf.drawString(50, totals_y - nb_box_height - 20, "Validité du devis: 1 MOIS")

            # Footer
            pdf.setFillColorRGB(*BLACK)
            pdf.setFont("Helvetica", 8)
            
            if os.path.exists(logo_path):
                pdf.drawImage(logo_path, 50, 20, width=30, height=15)
            
            footer_text = "Douar Ait Laarassi Tidili, Cercle El Kelâa, Route de Safi, Km 14-40000 Marrakech"
            pdf.drawCentredString(page_width/2, 30, footer_text)
            footer_contact = "Tél: 05 24 01 55 54 Fax : 05 24 01 55 29 E-mail : compra45@gmail.com"
            pdf.drawCentredString(page_width/2, 20, footer_contact)

            pdf.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error in PDF generation: {str(e)}", exc_info=True)
            raise