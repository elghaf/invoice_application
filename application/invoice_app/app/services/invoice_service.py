from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
from app.db.models import Invoice
import logging

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

            # Add logo in top left corner (adjusted size and position)
            pdf.drawImage("app/static/logo.png", 50, page_height - 70, width=90, height=35)
            
            # Add "DEVIS" text in top right (adjusted position)
            pdf.setFont("Helvetica-Bold", 24)
            pdf.drawString(page_width - 120, page_height - 50, "DEVIS")

            # Info boxes (left side) - moved up
            info_y = page_height - 100
            box_width = 180  # Reduced width
            box_height = 20

            def draw_info_box(label, value, y_pos):
                # Blue background for label
                pdf.setFillColorRGB(*HEADER_BLUE)
                pdf.rect(50, y_pos, box_width, box_height, fill=1)
                
                # White text for label
                pdf.setFillColorRGB(*WHITE)
                pdf.setFont("Helvetica", 9)
                pdf.drawString(55, y_pos + 6, label)
                
                # White background for value
                pdf.setFillColorRGB(*WHITE)
                pdf.rect(130, y_pos, 100, box_height, fill=1, stroke=1)
                
                # Black text for value
                pdf.setFillColorRGB(*BLACK)
                pdf.drawString(135, y_pos + 6, str(value))

            # Draw info boxes with less spacing
            draw_info_box("Date du devis:", data.date.strftime("%Y-%m-%d"), info_y)
            draw_info_box("N° Devis:", data.invoice_number, info_y - 20)
            draw_info_box("PLANCHER:", "PH RDC", info_y - 40)

            # Client Info Box (right side) - Updated for better symmetry
            client_box_y = page_height - 100
            client_box_width = 220
            client_box_height = 90
            client_box_x = page_width - client_box_width - 50

            # Draw the outer box with light gray background
            pdf.setFillColorRGB(0.98, 0.98, 0.98)
            pdf.rect(client_box_x, client_box_y - client_box_height, 
                    client_box_width, client_box_height, stroke=1, fill=1)
            
            # Client Info with better spacing and alignment
            client_info = [
                ("Nom:", data.client_name),
                ("Type d'ouvrage:", data.project),
                ("Lieu:", "BAB ATLAS"),
                ("Telephone:", data.client_phone)
            ]

            # Draw client info with improved spacing and alignment
            label_x = client_box_x + 10
            value_x = client_box_x + 90  # Fixed position for values
            line_height = 20

            for i, (label, value) in enumerate(client_info):
                y = client_box_y - 25 - (i * line_height)
                # Draw label
                pdf.setFillColorRGB(*BLACK)
                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawString(label_x, y, label)
                # Draw value
                pdf.setFont("Helvetica", 9)
                pdf.drawString(value_x, y, str(value))

            # Table headers with exact column titles and widths
            headers = [
                ("Description", 250),
                ("Unité", 50),
                ("NBRE", 50),
                ("LNG/Qté", 60),
                ("P.U", 60),
                ("Total HT", 70)
            ]

            # Calculate total width once
            total_width = sum(width for _, width in headers)

            # Table headers and content with exact styling
            def draw_section_header(title, y_pos):
                pdf.setFillColorRGB(*HEADER_BLUE)
                pdf.rect(50, y_pos, total_width, 20, fill=1)
                pdf.setFillColorRGB(*WHITE)
                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawString(55, y_pos + 6, title)
                return y_pos - 20

            def draw_table_header(y_pos):
                x = 50
                
                # Draw blue background for header
                pdf.setFillColorRGB(*HEADER_BLUE)
                pdf.rect(x, y_pos, total_width, 20, fill=1)
                
                # Draw header text in white
                pdf.setFillColorRGB(*WHITE)
                pdf.setFont("Helvetica-Bold", 9)
                
                # Draw each column header
                current_x = x
                for title, width in headers:
                    pdf.rect(current_x, y_pos, width, 20, stroke=1)  # Add border
                    # Center the text in each column
                    text_width = pdf.stringWidth(title, "Helvetica-Bold", 9)
                    text_x = current_x + (width - text_width) / 2
                    pdf.drawString(text_x, y_pos + 6, title)
                    current_x += width
                
                return y_pos - 20

            # Draw the table header
            current_y = info_y - 80  # Adjusted position
            current_y = draw_table_header(current_y)

            # Table headers and content with exact styling
            def draw_table_row(items, y_pos, indent=False):
                x = 50
                # Draw white background
                pdf.setFillColorRGB(*WHITE)
                pdf.rect(x, y_pos, total_width, 20, fill=1, stroke=1)
                
                # Draw cell borders and content
                pdf.setFillColorRGB(*BLACK)
                pdf.setFont("Helvetica", 9)
                
                for value, (_, width) in zip(items, headers):
                    pdf.rect(x, y_pos, width, 20, stroke=1)
                    text_x = x + (15 if indent and x == 50 else 5)
                    pdf.drawString(text_x, y_pos + 6, str(value))
                    x += width
                return y_pos - 20

            # Draw main table header
            current_y = current_y
            current_y = draw_section_header("Description", current_y)

            # POUTRELLES section
            current_y = draw_section_header("POUTRELLES", current_y)
            
            poutrelles_items = [i for i in data.items if "PCP" in i.description]
            for item in poutrelles_items:
                row = [
                    item.description,
                    "ML",
                    str(item.quantity),
                    f"{item.unit_price:.2f}",
                    f"{item.unit_price:.2f}",
                    f"{(item.quantity * item.unit_price):.2f}"
                ]
                current_y = draw_table_row(row, current_y)

            # HOURDIS section
            current_y = draw_section_header("HOURDIS", current_y)
            
            hourdis_items = [i for i in data.items if "HOURDIS" in i.description]
            for item in hourdis_items:
                row = [
                    "    " + item.description,  # Added indentation
                    "U",
                    "1",
                    f"{item.unit_price:.2f}",
                    f"{item.unit_price:.2f}",
                    f"{item.unit_price:.2f}"
                ]
                current_y = draw_table_row(row, current_y, indent=True)

            # PANNEAU TREILLIS SOUDES section
            current_y = draw_section_header("PANNEAU TREILLIS SOUDES", current_y)
            
            panneaux_items = [i for i in data.items if "TRS" in i.description]
            for item in panneaux_items:
                row = [
                    "    " + item.description,  # Added indentation
                    "U",
                    "1",
                    f"{item.unit_price:.2f}",
                    f"{item.unit_price:.2f}",
                    f"{item.unit_price:.2f}"
                ]
                current_y = draw_table_row(row, current_y, indent=True)

            # Move totals closer to table
            footer_y = current_y - 40  # Adjusted position
            
            # N° Cadre box (left)
            pdf.rect(50, footer_y - 30, 120, 30, stroke=1)
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(60, footer_y - 15, "N° Cadre:")

            # Totals box (right)
            totals_box_width = 180
            pdf.setFillColorRGB(*HEADER_BLUE)
            pdf.rect(page_width - totals_box_width - 50, footer_y - 30, totals_box_width, 30, fill=1)
            
            # Add totals with proper alignment
            pdf.setFillColorRGB(*WHITE)
            y_offset = 0
            for label, value in [
                ("Total H.T", f"{data.total_ht:.2f} DH"),
                ("TVA 20%", f"{data.tax:.2f} DH"),
                ("Total TTC", f"{data.total_ttc:.2f} DH")
            ]:
                pdf.drawString(page_width - totals_box_width - 40, footer_y - 10 - y_offset, label)
                pdf.drawString(page_width - 120, footer_y - 10 - y_offset, value)
                y_offset += 10

            # Footer with company details
            pdf.setFillColorRGB(*BLACK)
            pdf.setFont("Helvetica", 8)
            
            # Add small logo in footer
            pdf.drawImage("app/static/logo.png", 50, 20, width=30, height=15)
            
            footer_text = "Douar Ait Laarassi Tidili, Cercle El Kelâa, Route de Safi, Km 14-40000 Marrakech"
            pdf.drawCentredString(page_width/2, 30, footer_text)
            footer_contact = "Tél: 05 24 01 55 54 Fax : 05 24 01 55 29 E-mail : compra45@gmail.com"
            pdf.drawCentredString(page_width/2, 20, footer_contact)

            # Page number
            pdf.drawString(page_width - 30, 20, "1")

            pdf.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error in PDF generation: {str(e)}", exc_info=True)
            raise