# invoice_pdf.py

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.pdfgen import canvas
from datetime import datetime
from urllib.parse import quote

try:
    from reportlab.graphics.barcode import (
        code128, code39, code93, code2of5, usps, usps4s, eanbc,
        i2of5, code93ext, qr, pdf417, widgets, ecc200datamatrix, azteccode, common
    )
    from reportlab.graphics import renderPDF, renderPM
except ImportError:
    pass

# Use standard ReportLab styles, modified as needed
styles = getSampleStyleSheet()
styles["Normal"].fontSize = 10
styles["Normal"].leading = 12
styles.add(ParagraphStyle("InvoiceTitle", parent=styles["Title"], fontSize=16, leading=18, spaceAfter=6))
styles.add(ParagraphStyle("Header", parent=styles["Heading3"], fontSize=12, leading=14, spaceAfter=4))


def make_qr_code(data: str, size_mm=50):
    qr_code = qr.QrCodeWidget(data)
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    # Scale drawing to desired size
    drawing = Drawing(size_mm * mm, size_mm * mm, transform=[size_mm * mm / width, 0, 0, size_mm * mm / height, 0, 0])
    drawing.add(qr_code)
    return drawing


def _draw_header_footer(canv, doc):
    shop = getattr(doc, 'shop', {}) or {}
    canv.saveState()

    width, height = A4
    left, right = doc.leftMargin, doc.rightMargin
    top, bottom = doc.topMargin, doc.bottomMargin

    y = height - top + 15 * mm
    x = left

    # Shop name and details
    canv.setFont("Helvetica-Bold", 14)
    canv.drawString(x, y, shop.get("name", "Shop Name"))
    y -= 12
    canv.setFont("Helvetica", 10)

    for line in (shop.get("address1", ""), shop.get("address2", "")):
        if line.strip():
            canv.drawString(x, y, line.strip())
            y -= 12

    if shop.get("gstin"):
        canv.drawString(x, y, f"GSTIN: {shop['gstin']}")
        y -= 12

    info_parts = []
    if shop.get("email"):
        info_parts.append(f"Email: {shop['email']}")
    if shop.get("phone"):
        info_parts.append(f"Phone: {shop['phone']}")

    if info_parts:
        canv.drawString(x, y, " | ".join(info_parts))
        y -= 12

    canv.setLineWidth(0.7)
    canv.line(left, y, width - right, y)

    # Footer
    canv.setFont("Helvetica", 9)
    canv.drawRightString(width - right, bottom - 20, f"Page {canv.getPageNumber()}")

    canv.restoreState()


def build_invoice_pdf(
    filepath,
    items,
    customer_name,
    customer_phone,
    shop_info=None,
    invoice_number=None,
    tax_rate=18.0
):
    shop = shop_info or {}

    # Properly normalize items into a list of dicts
    normalized_items = [
        {
            "name": item.get("name", ""),
            "qty": int(item.get("qty", 0)),
            "price": float(item.get("unit_price", 0.0)),
            "line_total": int(item.get("qty", 0)) * float(item.get("unit_price", 0.0))
        }
        for item in items
    ]

    subtotal = sum(item["line_total"] for item in normalized_items)
    tax_amount = subtotal * tax_rate / 100
    total = subtotal + tax_amount

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=30 * mm,
        bottomMargin=18 * mm
    )
    doc.shop = shop  # attach shop info for header/footer

    story = []
    story.append(Spacer(1, 15))
    # Invoice title
    story.append(Paragraph("Invoice", styles["InvoiceTitle"]))
    # story.append(Spacer(1, 15))

    # Meta information table (date, invoice number, customer)
    meta_data = [
        ("Date:", datetime.now().strftime("%d-%m-%Y %H:%M")),
        ("Invoice No:", str(invoice_number) if invoice_number else "-"),
        ("Customer:", customer_name or "-"),
        ("Phone:", customer_phone or "-"),
    ]

    meta_table_data = [[Paragraph(str(k), styles["Normal"]), Paragraph(str(v), styles["Normal"])] for k,v in meta_data]

    meta_table = Table(meta_table_data, colWidths=[50 * mm, 90 * mm])
    meta_table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Items Table Header
    item_table_data = [
        [
            Paragraph("Item", styles["Header"]),
            Paragraph("Qty", styles["Header"]),
            Paragraph("Unit Price", styles["Header"]),
            Paragraph("Total", styles["Header"])
        ]
    ]

    # Add each item row
    for item in normalized_items:
        item_table_data.append([
            Paragraph(item["name"], styles["Normal"]),
            str(item["qty"]),
            f"Rs. {item['price']:.2f}",
            f"Rs. {item['line_total']:.2f}",
        ])

    item_table = Table(item_table_data, colWidths=[90 * mm, 25 * mm, 40 * mm, 40 * mm])
    item_table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    story.append(item_table)
    story.append(Spacer(1, 12))

    # Totals Table
    totals_data = [
        ("Subtotal", f"Rs. {subtotal:.2f}"),
        (f"Tax ({tax_rate}%)", f"Rs. {tax_amount:.2f}"),
        ("Total", f"Rs. {total:.2f}")
    ]

    totals_table = Table(totals_data, colWidths=[115 * mm, 80 * mm])
    totals_table.setStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.green),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
    ])

    story.append(totals_table)
    story.append(Spacer(1, 25))

    # QR code for UPI payments
    upi_id = (shop.get("upi_id") or "999999999999@upi").strip()
    upi_name = (shop.get("upi_name") or shop.get("name") or "Shop").strip()
    amount_str = f"{total:.2f}"

    txn_note = quote(f"Invoice {invoice_number}" if invoice_number else "Payment")
    upi_url = f"upi://pay?pa={upi_id}&pn={quote(upi_name)}&am={amount_str}&cu=INR&tn={txn_note}"

    story.append(Paragraph("Scan to pay using UPI:", styles["Normal"]))
    story.append(Spacer(1, 6))
    story.append(make_qr_code(upi_url, size_mm=50))
    story.append(Spacer(1, 20))

    story.append(Paragraph("Thank you for your purchase!", styles["Normal"]))

    doc.build(story, onFirstPage=_draw_invoice_header_footer, onLaterPages=_draw_invoice_header_footer)

    return filepath


def _draw_invoice_header_footer(canvas, doc):
    shop = getattr(doc, 'shop', {}) or {}
    canvas.saveState()

    width, height = doc.pagesize
    left, right = doc.leftMargin, doc.rightMargin
    top, bottom = doc.topMargin, doc.bottomMargin

    y = height - top + 15 * mm
    x = left

    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(x, y, shop.get("name", "Shop Name"))
    y -= 12

    canvas.setFont("Helvetica", 10)
    for line in (shop.get("address1", ""), shop.get("address2", "")):
        if line.strip():
            canvas.drawString(x, y, line.strip())
            y -= 12

    if shop.get("gstin"):
        canvas.drawString(x, y, f"GSTIN: {shop['gstin']}")
        y -= 12

    info = []
    if shop.get("email"):
        info.append(f"Email: {shop['email']}")
    if shop.get("phone"):
        info.append(f"Phone: {shop['phone']}")
    if info:
        canvas.drawString(x, y, " | ".join(info))
        y -= 12

    canvas.setLineWidth(0.7)
    canvas.line(left, y, width - right, y)

    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(width - right, bottom, f"Page {canvas.getPageNumber()}")

    canvas.restoreState()
