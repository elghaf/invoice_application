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

            # Constants
            HEADER_BLUE = (0.29, 0.45, 0.68)
            BLUE_LIGHT = (0.8, 0.8, 1)
            WHITE = (1, 1, 1)
            BLACK = (0, 0, 0)
            MARGIN = 30
            LINE_HEIGHT = 20
            BOX_PADDING = 10

            # Helper function to draw centered text
            def draw_centered_text(pdf, text, x, y, width, font="Helvetica", size=10):
                text_width = pdf.stringWidth(text, font, size)
                pdf.drawString(x + (width - text_width) / 2, y, text)

            # Helper function to draw a bordered box
            def draw_box(pdf, x, y, width, height, fill_color=None, stroke_color=BLACK):
                if fill_color:
                    pdf.setFillColorRGB(*fill_color)
                    pdf.rect(x, y, width, height, fill=1, stroke=0)
                pdf.setFillColorRGB(*stroke_color)
                pdf.rect(x, y, width, height, stroke=1)

            # Get the absolute path to the logo file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(current_dir, "..", "static", "logo.png")

            # Top section layout
            top_margin = page_height - 100

            # Left side: Logo - moved far left and up
            if os.path.exists(logo_path):
                pdf.drawImage(logo_path, MARGIN, top_margin + 30, width=100, height=60)

            # Right side: DEVIS and Client Box - moved far right and up
            pdf.setFont("Helvetica-Bold", 48)
            devis_text = "DEVIS"
            devis_width = pdf.stringWidth(devis_text, "Helvetica-Bold", 48)
            devis_x = page_width - devis_width - MARGIN - 10
            devis_y = top_margin + 50
            pdf.drawString(devis_x, devis_y, devis_text)

            # Client info box - moved right under DEVIS
            box_width = 200
            box_height = 80
            box_x = page_width - box_width - MARGIN + 10
            box_y = devis_y - 90

            # Draw client box
            pdf.rect(box_x, box_y, box_width, box_height, stroke=1)

            # Client Info
            pdf.setFont("Helvetica", 10)
            client_info = [
                data.client_name,
                data.project,
                data.address,
                data.client_phone
            ]

            # Center and draw each line of client info
            line_height = box_height / (len(client_info) + 1)
            for i, text in enumerate(client_info):
                text_width = pdf.stringWidth(str(text), "Helvetica", 10)
                x = box_x + (box_width - text_width) / 2
                y = box_y + box_height - ((i + 1) * line_height)
                pdf.drawString(x, y, str(text))

            # Info boxes (Date, N° Devis, PLANCHER) - adjusted starting position
            info_y = top_margin 
            box_label_width = 120
            box_value_width = 80

            for label, value in [
                ("Date du devis :", data.date.strftime("%d/%m/%Y")),
                ("N° Devis :", data.invoice_number),
                ("PLANCHER :", data.frame_number or "PH RDC")
            ]:
                draw_box(pdf, MARGIN, info_y, box_label_width, LINE_HEIGHT, fill_color=HEADER_BLUE)
                pdf.setFillColorRGB(*WHITE)
                pdf.drawString(MARGIN + BOX_PADDING, info_y + 6, label)

                draw_box(pdf, MARGIN + box_label_width, info_y, box_value_width, LINE_HEIGHT, fill_color=WHITE)
                pdf.setFillColorRGB(*BLACK)
                draw_centered_text(pdf, str(value), MARGIN + box_label_width, info_y + 6, box_value_width)

                info_y -= 25

            # Table headers
            table_y = info_y - 30
            headers = [
                ("Description", 150),
                ("Unité", 50),
                ("NBRE", 50),
                ("LNG/Qté", 60),
                ("P.U", 60),
                ("Total HT", 170)
            ]

            total_width = sum(width for _, width in headers)
            table_x = (page_width - total_width) / 2  # Center table
            draw_box(pdf, table_x, table_y, total_width, LINE_HEIGHT, fill_color=HEADER_BLUE)
            pdf.setFillColorRGB(*WHITE)

            current_x = table_x
            for title, width in headers:
                draw_box(pdf, current_x, table_y, width, LINE_HEIGHT)
                draw_centered_text(pdf, title, current_x, table_y + 6, width)
                current_x += width


            # Draw sections and items
            current_y = table_y - LINE_HEIGHT

            def draw_section_header(title):
                nonlocal current_y
                draw_box(pdf, table_x, current_y, total_width, LINE_HEIGHT, fill_color=BLUE_LIGHT)
                pdf.setFillColorRGB(*BLACK)
                pdf.drawString(table_x + BOX_PADDING, current_y + 6, title)
                current_y -= LINE_HEIGHT

            def draw_section_header2(title):
                nonlocal current_y
                draw_box(pdf, table_x, current_y, total_width, LINE_HEIGHT, fill_color=WHITE)
                
                # Set the font to a bold variant
                pdf.setFont("Helvetica-Bold", 12)  # Adjust the font name and size as needed
                
                # Set the fill color to black
                pdf.setFillColorRGB(0, 0, 0)  # RGB values for black
                
                # Draw the string
                pdf.drawString(table_x + BOX_PADDING, current_y + 6, title)
                
                current_y -= LINE_HEIGHT

            def draw_item_row(item, indent=False):
                nonlocal current_y
                pdf.setFillColorRGB(*BLACK)
                current_x = table_x

                draw_box(pdf, current_x, current_y, total_width, LINE_HEIGHT, fill_color=WHITE)

                cells = [
                    ("    " + item.description if indent else item.description, 150),
                    (item.unit, 50),
                    (str(item.quantity), 50),
                    (f"{item.length:.2f}", 60),
                    (f"{item.unit_price:.2f}", 60),
                    (f"{item.total_price:.2f}", 170)
                ]

                for value, width in cells:
                    draw_box(pdf, current_x, current_y, width, LINE_HEIGHT)
                    if isinstance(value, str) and value.startswith("    "):
                        pdf.drawString(current_x + 20, current_y + 6, value.strip())
                    else:
                        draw_centered_text(pdf, str(value), current_x, current_y + 6, width)
                    current_x += width

                current_y -= LINE_HEIGHT

            # Draw sections
            sections = [
                ("POUTRELLES", "PCP"),
                ("HOURDIS", "HOURDIS"),
                ("PANNEAU TREILLIS SOUDES", "PTS")
            ]

            for section_title, keyword in sections:
                draw_section_header(section_title)
                items = [i for i in data.items if keyword in i.description]
                for item in items:
                    draw_item_row(item, indent=(keyword != "lfflflflf"))

            # NB box with just "NB:" text
            nb_box_width = 200
            nb_box_height = 80
            pdf.setFillColorRGB(*BLACK)
            pdf.rect(20, current_y - nb_box_height, nb_box_width, nb_box_height, stroke=1)
            pdf.setFont("Helvetica-Bold", 12)  # Made slightly larger for better visibility
            pdf.drawString(60, current_y - nb_box_height + 60, "NB:")

            # Totals section
            current_y -= 20
            totals_table_width = 300
            row_height = 20

            for i, (label1, label2, value) in enumerate([
                ("Total", "H.T", f"{data.total_ht:.2f} DH"),
                ("TVA", "20 %", f"{data.tax:.2f} DH"),
                ("Total", "TTC", f"{data.total_ttc:.2f} DH")
            ]):
                y = current_y - (i * row_height)
                totals_x = (page_width - totals_table_width) - 27  # Center totals table
                draw_box(pdf, totals_x, y, totals_table_width / 2, row_height)
                draw_box(pdf, totals_x + totals_table_width / 2, y, totals_table_width / 2, row_height)
                pdf.drawString(totals_x + 10, y + 6, f"{label1}    {label2}")
                pdf.drawRightString(totals_x + totals_table_width - 10, y + 6, value)

            # Footer
            pdf.setFont("Helvetica", 8)
            if os.path.exists(logo_path):
                pdf.drawImage(logo_path, MARGIN, 20, width=30, height=15)

            footer_text = "Douar Ait Laarassi Tidili, Cercle El Kelâa, Route de Safi, Km 14-40000 Marrakech"
            pdf.drawCentredString(page_width / 2, 30, footer_text)
            footer_contact = "Tél: 05 24 01 55 54 Fax : 05 24 01 55 29 E-mail : compra45@gmail.com"
            pdf.drawCentredString(page_width / 2, 20, footer_contact)

            pdf.save()
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error in PDF generation: {str(e)}", exc_info=True)
            raise