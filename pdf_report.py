from fpdf import FPDF
from datetime import datetime

class PDFCierre(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, 'Reporte de Cierre de Caja', border=False, align='C', new_x="LMARGIN", new_y="NEXT")
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 10, f'Fecha de generación: {datetime.now().strftime("%d/%m/%Y %H:%M")}', border=False, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

def generar_pdf(ingresos_por_metodo, total_ingresos, total_egresos, saldo_final, nombre_archivo):
    pdf = PDFCierre()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, "INGRESOS POR MÉTODO DE PAGO", new_x="LMARGIN", new_y="NEXT")
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(100, 10, "Método de Pago", border=1, fill=True)
    pdf.cell(50, 10, "Monto", border=1, fill=True, new_x="LMARGIN", new_y="NEXT", align='R')
    pdf.set_font("helvetica", size=12)
    for metodo, monto in ingresos_por_metodo.items():
        pdf.cell(100, 10, metodo, border=1)
        pdf.cell(50, 10, f"${monto:,.2f}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, "RESUMEN DE CAJA", new_x="LMARGIN", new_y="NEXT")
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(100, 10, "TOTAL INGRESOS", border=1, fill=True)
    pdf.cell(50, 10, f"${total_ingresos:,.2f}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')
    pdf.cell(100, 10, "TOTAL EGRESOS (Pagos/Gastos)", border=1, fill=True)
    pdf.cell(50, 10, f"${total_egresos:,.2f}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')
    pdf.set_fill_color(200, 255, 200)
    pdf.cell(100, 10, "SALDO FINAL EN CAJA", border=1, fill=True)
    pdf.cell(50, 10, f"${saldo_final:,.2f}", border=1, new_x="LMARGIN", new_y="NEXT", align='R')
    pdf.output(nombre_archivo)

class PDFProveedor(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, 'Resumen de Cuenta - Proveedor', border=False, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

def generar_pdf_proveedor(nombre_prov, saldo_actual_str, historial, nombre_archivo):
    pdf = PDFProveedor()
    pdf.add_page()
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f"Proveedor: {nombre_prov}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 12)
    pdf.cell(0, 10, f"Deuda Total Pendiente: {saldo_actual_str}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(25, 10, "Fecha", border=1, fill=True)
    pdf.cell(20, 10, "Tipo", border=1, fill=True)
    pdf.cell(25, 10, "Monto", border=1, fill=True)
    pdf.cell(90, 10, "Descripcion/Fact", border=1, fill=True)
    pdf.cell(30, 10, "Saldo Dia", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font('helvetica', '', 9)
    for h in historial:
        desc_fact = h['descripcion']
        if h['factura'] != "-":
            desc_fact += f" (Fact: {h['factura']})"
        desc_fact = desc_fact[:50] + "..." if len(desc_fact) > 50 else desc_fact
        
        m_str = f"${h['monto']:.2f}"
        if h['tipo'] == 'PAGO': m_str = f"- {m_str}"
            
        pdf.cell(25, 8, h['fecha'].split(' ')[0], border=1)
        pdf.cell(20, 8, h['tipo'], border=1)
        pdf.cell(25, 8, m_str, border=1)
        pdf.cell(90, 8, desc_fact, border=1)
        pdf.cell(30, 8, f"${h['saldo_momento']:.2f}", border=1, new_x="LMARGIN", new_y="NEXT")
        
    pdf.output(nombre_archivo)
