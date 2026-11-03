import os
import ctypes
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from database import init_db
from services import (
    registrar_ingreso_caja, registrar_egreso_caja, obtener_resumen_caja_abierta, 
    cerrar_caja, obtener_historial_cierres, obtener_detalle_cierre, registrar_apertura_caja,
    agregar_proveedor, obtener_proveedores, obtener_proveedor, modificar_proveedor,
    registrar_pedido_proveedor, pagar_deuda_proveedor, obtener_historial_proveedor,
    obtener_vencimientos_calendario, obtener_alertas_vencimiento, obtener_estadisticas_generales, obtener_movimientos_caja_abierta, anular_movimiento_caja, hacer_backup_base_datos
)
from models import MetodoPago
from pdf_report import generar_pdf, generar_pdf_proveedor
from datetime import datetime, timedelta

try:
    myappid = 'mycompany.cajacontrol.gestion.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class InterfazCajaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Control de Caja y Proveedores")
        self.geometry("1200x720")
        
        try:
            ruta_icono = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.ico")
            self.iconbitmap(ruta_icono)
        except Exception:
            pass
            
        init_db()
        
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("Treeview", background="#F5F5F5", foreground="black", rowheight=25, fieldbackground="#F5F5F5", font=("Helvetica", 10))
        style.map('Treeview', background=[('selected', '#2C74B3')])
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"), background="#D9D9D9")
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tab_ventas = self.tabview.add("Caja y Movimientos")
        self.tab_proveedores = self.tabview.add("Proveedores")
        self.tab_stats = self.tabview.add("Estadisticas & Resumen")
        
        self.construir_tab_ventas()
        self.construir_tab_proveedores()
        self.construir_tab_stats()
        self.actualizar_estado_caja()
        
        self.after(1000, self.mostrar_alertas_vencimiento)

    def mostrar_alertas_vencimiento(self):
        alertas = obtener_alertas_vencimiento()
        if alertas:
            texto_alerta = "Atencion: Las siguientes facturas estan proximas a vencer o ya vencieron:\n\n"
            texto_alerta += "\n".join(alertas)
            texto_alerta += "\n\n(Solo se muestran facturas de proveedores con deuda pendiente)."
            messagebox.showwarning("Alertas de Vencimientos", texto_alerta)
        
    def construir_tab_ventas(self):
        self.frame_dashboard = ctk.CTkFrame(self.tab_ventas, fg_color="#F8F9FA", corner_radius=10)
        self.frame_dashboard.pack(fill="x", padx=10, pady=(5, 10))
        
        self.lbl_apertura_actual = ctk.CTkLabel(self.frame_dashboard, text="Fondo Fijo: $0.00", font=ctk.CTkFont(size=16, weight="bold"), text_color="#6c757d")
        self.lbl_apertura_actual.pack(side="left", expand=True, pady=15)
        self.lbl_ingreso_actual = ctk.CTkLabel(self.frame_dashboard, text="Ingresos: $0.00", font=ctk.CTkFont(size=16, weight="bold"), text_color="#28a745")
        self.lbl_ingreso_actual.pack(side="left", expand=True, pady=15)
        self.lbl_egreso_actual = ctk.CTkLabel(self.frame_dashboard, text="Egresos: $0.00", font=ctk.CTkFont(size=16, weight="bold"), text_color="#dc3545")
        self.lbl_egreso_actual.pack(side="left", expand=True, pady=15)
        self.lbl_saldo_actual = ctk.CTkLabel(self.frame_dashboard, text="Saldo Total: $0.00", font=ctk.CTkFont(size=20, weight="bold"), text_color="#007bff")
        self.lbl_saldo_actual.pack(side="left", expand=True, pady=15)

        contenedor_inferior = ctk.CTkFrame(self.tab_ventas, fg_color="transparent")
        contenedor_inferior.pack(fill="both", expand=True)

        panel_acciones = ctk.CTkFrame(contenedor_inferior, width=320)
        panel_acciones.pack(side="left", fill="y", padx=10, pady=5)
        
        ctk.CTkButton(panel_acciones, text="Abrir Caja (Fondo Inicial)", fg_color="#17a2b8", hover_color="#138496", command=self.accion_abrir_caja).pack(padx=20, pady=(10, 5), fill="x")
        ctk.CTkLabel(panel_acciones, text="Registrar INGRESO (Venta)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        self.entry_ing_monto = ctk.CTkEntry(panel_acciones, placeholder_text="Monto ($)")
        self.entry_ing_monto.pack(padx=20, pady=5, fill="x")
        self.combo_ing_metodo = ctk.CTkComboBox(panel_acciones, values=[m.value for m in MetodoPago])
        self.combo_ing_metodo.pack(padx=20, pady=5, fill="x")
        ctk.CTkButton(panel_acciones, text="Guardar Ingreso", fg_color="#28a745", hover_color="#218838", command=self.accion_guardar_ingreso).pack(padx=20, pady=(5, 15), fill="x")
        
        ctk.CTkLabel(panel_acciones, text="Registrar EGRESO (Gasto)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        self.entry_egr_monto = ctk.CTkEntry(panel_acciones, placeholder_text="Monto ($)")
        self.entry_egr_monto.pack(padx=20, pady=5, fill="x")
        self.entry_egr_desc = ctk.CTkComboBox(panel_acciones, values=["Insumos", "Sueldos", "Impuestos", "Mantenimiento", "Retiro Personal", "Servicios", "Otros"])
        self.entry_egr_desc.pack(padx=20, pady=5, fill="x")
        self.combo_egr_metodo = ctk.CTkComboBox(panel_acciones, values=[m.value for m in MetodoPago])
        self.combo_egr_metodo.pack(padx=20, pady=5, fill="x")
        ctk.CTkButton(panel_acciones, text="Guardar Egreso", fg_color="#dc3545", hover_color="#c82333", command=self.accion_guardar_egreso).pack(padx=20, pady=(5, 20), fill="x")
        
        ctk.CTkButton(panel_acciones, text="CERRAR CAJA ACTUAL", fg_color="#343a40", hover_color="#23272b", font=ctk.CTkFont(weight="bold"), command=self.accion_cerrar_caja).pack(padx=20, pady=10, fill="x")

        panel_centro = ctk.CTkFrame(contenedor_inferior, fg_color="transparent")
        panel_centro.pack(side="right", fill="both", expand=True, padx=10, pady=5)
        
        frame_mov_abiertos = ctk.CTkFrame(panel_centro)
        frame_mov_abiertos.pack(fill="both", expand=True, pady=(0, 5))
        
        top_mov_ab = ctk.CTkFrame(frame_mov_abiertos, fg_color="transparent")
        top_mov_ab.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(top_mov_ab, text="Movimientos del Turno Abierto (Selecciona para Anular)", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        ctk.CTkButton(top_mov_ab, text="Anular Seleccionado", fg_color="#dc3545", hover_color="#c82333", width=140, command=self.accion_anular_movimiento).pack(side="right")
        
        self.tabla_mov_abiertos = ttk.Treeview(frame_mov_abiertos, columns=("id", "fecha", "tipo", "monto", "metodo", "desc"), show='headings', height=5)
        for col, txt in zip(("id", "fecha", "tipo", "monto", "metodo", "desc"), ["ID", "Fecha/Hora", "Tipo", "Monto", "Metodo", "Descripcion"]):
            self.tabla_mov_abiertos.heading(col, text=txt)
        self.tabla_mov_abiertos.column("id", width=40, anchor='center')
        self.tabla_mov_abiertos.column("fecha", width=130, anchor='center')
        self.tabla_mov_abiertos.column("tipo", width=80, anchor='center')
        self.tabla_mov_abiertos.column("monto", width=90, anchor='e')
        self.tabla_mov_abiertos.column("metodo", width=110, anchor='center')
        self.tabla_mov_abiertos.column("desc", width=200, anchor='w')
        self.tabla_mov_abiertos.pack(fill='both', expand=True, padx=10, pady=5)

        panel_historial = ctk.CTkFrame(panel_centro)
        panel_historial.pack(fill="both", expand=True, pady=(5, 0))
        
        ctk.CTkLabel(panel_historial, text="Historial de Cierres de Caja (Doble clic para ver detalle)", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        frame_filtros = ctk.CTkFrame(panel_historial, fg_color="transparent")
        frame_filtros.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(frame_filtros, text="Desde (DD/MM/AAAA):", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        self.entry_filtro_desde = ctk.CTkEntry(frame_filtros, width=100, placeholder_text="Ej: 01/11/2026")
        self.entry_filtro_desde.pack(side="left", padx=5)
        
        ctk.CTkLabel(frame_filtros, text="Hasta:", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        self.entry_filtro_hasta = ctk.CTkEntry(frame_filtros, width=100, placeholder_text="Ej: 30/11/2026")
        self.entry_filtro_hasta.pack(side="left", padx=5)
        
        ctk.CTkButton(frame_filtros, text="Filtrar", width=80, command=self.actualizar_tabla_cierres).pack(side="left", padx=10)
        ctk.CTkButton(frame_filtros, text="Limpiar", width=70, fg_color="gray", command=self.limpiar_filtro_cierres).pack(side="left", padx=2)

        self.tabla_cierres = ttk.Treeview(panel_historial, columns=("id", "fecha", "ing", "egr", "saldo"), show='headings')
        self.tabla_cierres.heading("id", text="ID")
        self.tabla_cierres.heading("fecha", text="Fecha de Cierre")
        self.tabla_cierres.heading("ing", text="Total Ingresos")
        self.tabla_cierres.heading("egr", text="Total Egresos")
        self.tabla_cierres.heading("saldo", text="Saldo Final")
        self.tabla_cierres.column("id", width=40, anchor='center')
        self.tabla_cierres.column("fecha", width=150, anchor='center')
        self.tabla_cierres.column("ing", width=100, anchor='e')
        self.tabla_cierres.column("egr", width=100, anchor='e')
        self.tabla_cierres.column("saldo", width=120, anchor='e')
        self.tabla_cierres.bind("<Double-1>", self.accion_ver_detalle_cierre)
        self.tabla_cierres.pack(fill='both', expand=True, padx=10, pady=10)
        self.actualizar_tabla_cierres()

    def limpiar_filtro_cierres(self):
        self.entry_filtro_desde.delete(0, 'end')
        self.entry_filtro_hasta.delete(0, 'end')
        self.actualizar_tabla_cierres()

    def marcar_error(self, entry_widget):
        entry_widget.configure(border_color="red")
        self.after(2000, lambda: entry_widget.configure(border_color=["#979DA2", "#565B5E"]))

    def actualizar_estado_caja(self):
        _, tot_ing, tot_egr, saldo_ini, saldo = obtener_resumen_caja_abierta()
        self.lbl_apertura_actual.configure(text=f"Fondo Fijo: ${saldo_ini:,.2f}")
        self.lbl_ingreso_actual.configure(text=f"Ingresos: ${tot_ing:,.2f}")
        self.lbl_egreso_actual.configure(text=f"Egresos: ${tot_egr:,.2f}")
        self.lbl_saldo_actual.configure(text=f"Saldo Total: ${saldo:,.2f}")
        self.actualizar_tabla_movimientos_abiertos()

    def actualizar_tabla_movimientos_abiertos(self):
        if not hasattr(self, 'tabla_mov_abiertos'): return
        for fila in self.tabla_mov_abiertos.get_children():
            self.tabla_mov_abiertos.delete(fila)
        for m in obtener_movimientos_caja_abierta():
            m_str = f"${m['monto']:.2f}"
            if m['tipo'] == 'EGRESO': m_str = f"- {m_str}"
            self.tabla_mov_abiertos.insert("", "end", values=(m['id'], m['fecha'], m['tipo'], m_str, m['metodo'], m['descripcion']))

    def accion_anular_movimiento(self):
        sel = self.tabla_mov_abiertos.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Selecciona un movimiento abierto para anular.")
            return
        item = self.tabla_mov_abiertos.item(sel[0])['values']
        mov_id, tipo, monto = item[0], item[2], item[3]
        if tipo == 'APERTURA':
            messagebox.showerror("Error", "No se puede anular el fondo de apertura directamente.")
            return
        conf = messagebox.askyesno("Confirmar Anulacion", f"¿Estas seguro de anular el movimiento #{mov_id} ({tipo} por {monto})?")
        if conf:
            anular_movimiento_caja(mov_id)
            self.actualizar_estado_caja()
            self.actualizar_estadisticas()
            messagebox.showinfo("Exito", "Movimiento anulado correctamente.")
        
    def accion_abrir_caja(self):
        dialog = ctk.CTkInputDialog(text="Ingrese el fondo o saldo inicial:", title="Apertura de Caja")
        res = dialog.get_input()
        if res:
            try:
                monto = float(res.replace(',', '.'))
                registrar_apertura_caja(monto)
                self.actualizar_estado_caja()
                self.actualizar_estadisticas()
            except ValueError:
                messagebox.showerror("Error", "Monto invalido.")

    def accion_guardar_ingreso(self):
        try:
            monto_str = self.entry_ing_monto.get().replace(',', '.')
            if not monto_str: raise ValueError
            monto = float(monto_str)
            metodo_enum = next(m for m in MetodoPago if m.value == self.combo_ing_metodo.get())
            registrar_ingreso_caja(monto, metodo_enum, "Venta Mostrador")
            self.entry_ing_monto.delete(0, 'end')
            self.actualizar_estado_caja()
            self.actualizar_estadisticas()
        except ValueError:
            self.marcar_error(self.entry_ing_monto)

    def accion_guardar_egreso(self):
        try:
            monto_str = self.entry_egr_monto.get().replace(',', '.')
            if not monto_str: raise ValueError
            monto = float(monto_str)
            desc = self.entry_egr_desc.get().strip() or "Retiro/Gasto"
            metodo_enum = next(m for m in MetodoPago if m.value == self.combo_egr_metodo.get())
            registrar_egreso_caja(monto, metodo_enum, desc)
            self.entry_egr_monto.delete(0, 'end')
            self.entry_egr_desc.delete(0, 'end')
            self.actualizar_estado_caja()
            self.actualizar_estadisticas()
        except ValueError:
            self.marcar_error(self.entry_egr_monto)

    def accion_cerrar_caja(self):
        ingresos_dict, tot_ing, tot_egr, saldo_ini, saldo = obtener_resumen_caja_abierta()
        if tot_ing == 0 and tot_egr == 0:
            messagebox.showinfo("Caja Vacia", "No hay movimientos para cerrar.")
            return
            
        confirmar = messagebox.askyesno("Confirmar Cierre", f"¿Deseas cerrar la caja?\n\nIngresos: ${tot_ing:,.2f}\nEgresos: ${tot_egr:,.2f}\nSaldo Final: ${saldo:,.2f}")
        if not confirmar: return

        cierre_id = cerrar_caja()
        if cierre_id:
            fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
            nombre_pdf = f"cierre_caja_{cierre_id}_{fecha_str}.pdf"
            generar_pdf(ingresos_dict, tot_ing, tot_egr, saldo, nombre_pdf)
            self.actualizar_tabla_cierres()
            self.actualizar_estado_caja()
            self.actualizar_estadisticas()
            messagebox.showinfo("Cierre Exitoso", f"Caja cerrada. PDF Generado: {nombre_pdf}")

    def actualizar_tabla_cierres(self):
        desde = self.entry_filtro_desde.get().strip()
        hasta = self.entry_filtro_hasta.get().strip()
        for fila in self.tabla_cierres.get_children():
            self.tabla_cierres.delete(fila)
        for c in obtener_historial_cierres(desde, hasta):
            self.tabla_cierres.insert("", "end", values=(c['id'], c['fecha'], f"${c['ingresos']:.2f}", f"${c['egresos']:.2f}", f"${c['saldo_final']:.2f}"))

    def accion_ver_detalle_cierre(self, event):
        seleccion = self.tabla_cierres.selection()
        if not seleccion: return
        item = self.tabla_cierres.item(seleccion[0])['values']
        cierre_id, fecha, saldo_fin = item[0], item[1], item[4]
        vent = ctk.CTkToplevel(self)
        vent.title(f"Detalle de Caja | {fecha} | Saldo: {saldo_fin}")
        vent.geometry("850x450")
        vent.transient(self)
        try:
            ruta_icono = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.ico")
            vent.iconbitmap(ruta_icono)
        except Exception: pass
        tree = ttk.Treeview(vent, columns=("hora", "tipo", "metodo", "desc", "monto", "saldo_momento"), show='headings')
        tree.tag_configure("ingreso", foreground="#007a1a")
        tree.tag_configure("egreso", foreground="#d90000")
        for col, txt in zip(tree["columns"], ["Hora", "Movimiento", "Medio", "Descripcion", "Monto", "Saldo en Caja"]):
            tree.heading(col, text=txt)
        tree.column("hora", width=80, anchor='center')
        tree.column("tipo", width=80, anchor='center')
        tree.column("metodo", width=120, anchor='center')
        tree.column("desc", width=250, anchor='w')
        tree.column("monto", width=100, anchor='e')
        tree.column("saldo_momento", width=120, anchor='e')
        tree.pack(fill='both', expand=True, padx=20, pady=20)
        for d in obtener_detalle_cierre(cierre_id):
            tag = "ingreso" if d['tipo'] == 'INGRESO' else "egreso"
            monto_str = f"${d['monto']:.2f}"
            if d['tipo'] == 'EGRESO': monto_str = f"- {monto_str}"
            tree.insert("", "end", values=(d['fecha'], d['tipo'], d['metodo'], d['descripcion'], monto_str, f"${d['saldo_momento']:.2f}"), tags=(tag,))

    def construir_tab_proveedores(self):
        frame_superior = ctk.CTkFrame(self.tab_proveedores)
        frame_superior.pack(fill='x', padx=10, pady=10)
        frame_botones = ctk.CTkFrame(frame_superior, fg_color="transparent")
        frame_botones.pack(side='left', anchor='n', pady=10)
        
        ctk.CTkButton(frame_botones, text="Nuevo", command=self.accion_nuevo_proveedor, width=100).pack(side='left', padx=5)
        ctk.CTkButton(frame_botones, text="Modificar", command=self.accion_modificar_proveedor, fg_color="gray", width=100).pack(side='left', padx=5)
        ctk.CTkButton(frame_botones, text="Recibir Pedido", command=self.accion_cargar_pedido, fg_color="#17a2b8", hover_color="#138496", width=120).pack(side='left', padx=15)
        ctk.CTkButton(frame_botones, text="Registrar Pago", command=self.accion_pagar, fg_color="#007bff", width=120).pack(side='left', padx=5)
        
        frame_vencimientos = ctk.CTkFrame(frame_superior, fg_color="transparent")
        frame_vencimientos.pack(side='left', fill='both', expand=True, padx=(25, 10))
        ctk.CTkLabel(frame_vencimientos, text="Vencimientos (Clic en dia rojo)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor='w')
        frame_cal_content = ctk.CTkFrame(frame_vencimientos, fg_color="transparent")
        frame_cal_content.pack(fill='both', expand=True, pady=2)
        
        self.cal_venc = Calendar(frame_cal_content, selectmode="day", showweeknumbers=False, font="Arial 9", cursor="hand2")
        self.cal_venc.pack(side='left', padx=(0, 10))
        self.caja_detalle_venc = ctk.CTkTextbox(frame_cal_content, height=170, text_color="#721c24", fg_color="#f8d7da", font=ctk.CTkFont(size=12, weight="bold"))
        self.caja_detalle_venc.pack(side='left', fill='both', expand=True)
        self.caja_detalle_venc.insert("0.0", "Selecciona un dia rojo para ver los detalles...")
        self.caja_detalle_venc.configure(state="disabled")
        self.cal_venc.bind("<<CalendarSelected>>", self.mostrar_detalle_fecha)

        frame_tabla = ctk.CTkFrame(self.tab_proveedores)
        frame_tabla.pack(fill='both', expand=True, padx=10, pady=10)
        frame_busqueda = ctk.CTkFrame(frame_tabla, fg_color="transparent")
        frame_busqueda.pack(fill='x', padx=10, pady=5)
        ctk.CTkLabel(frame_busqueda, text="Buscar Proveedor:", font=ctk.CTkFont(weight="bold")).pack(side='left', padx=(0, 10))
        self.entry_buscar_prov = ctk.CTkEntry(frame_busqueda, placeholder_text="Escribe nombre...", width=300)
        self.entry_buscar_prov.pack(side='left', padx=5)
        self.entry_buscar_prov.bind("<KeyRelease>", lambda e: self.actualizar_tabla_proveedores())
        ctk.CTkButton(frame_busqueda, text="Limpiar", width=120, fg_color="gray", command=lambda: (self.entry_buscar_prov.delete(0, 'end'), self.actualizar_tabla_proveedores())).pack(side='left', padx=10)
        
        self.tabla_prov = ttk.Treeview(frame_tabla, columns=("id", "nombre", "saldo"), show='headings')
        self.tabla_prov.tag_configure("cero", foreground="gray")
        self.tabla_prov.tag_configure("deuda", foreground="black")
        self.tabla_prov.tag_configure("alerta", foreground="#d90000", font=("Helvetica", 10, "bold"))
        self.tabla_prov.heading("id", text="ID")
        self.tabla_prov.heading("nombre", text="Proveedor")
        self.tabla_prov.heading("saldo", text="Deuda Pendiente ($)")
        self.tabla_prov.column("id", width=40, anchor='center')
        self.tabla_prov.column("nombre", width=400, anchor='w')
        self.tabla_prov.column("saldo", width=150, anchor='e')
        self.tabla_prov.bind("<Double-1>", self.accion_ver_historial_proveedor)
        self.tabla_prov.pack(fill='both', expand=True, padx=10, pady=(0,10))
        self.actualizar_tabla_proveedores()
        self.actualizar_calendario()

    def construir_tab_stats(self):
        frame_stats_main = ctk.CTkFrame(self.tab_stats, fg_color="transparent")
        frame_stats_main.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame_stats_main, text="Resumen Financiero y Estadisticas", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 20))
        self.frame_cards = ctk.CTkFrame(frame_stats_main, fg_color="transparent")
        self.frame_cards.pack(fill="x", pady=10)
        
        self.card_deuda_prov = ctk.CTkFrame(self.frame_cards, fg_color="#F8D7DA", corner_radius=10)
        self.card_deuda_prov.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        self.lbl_card_deuda_val = ctk.CTkLabel(self.card_deuda_prov, text="$0.00", font=ctk.CTkFont(size=22, weight="bold"), text_color="#721C24")
        self.lbl_card_deuda_val.pack(pady=(20, 5))
        ctk.CTkLabel(self.card_deuda_prov, text="Deuda Total con Proveedores", font=ctk.CTkFont(size=12), text_color="#721C24").pack(pady=(0, 20))

        self.card_ingresos_gen = ctk.CTkFrame(self.frame_cards, fg_color="#D4EDDA", corner_radius=10)
        self.card_ingresos_gen.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        self.lbl_card_ing_val = ctk.CTkLabel(self.card_ingresos_gen, text="$0.00", font=ctk.CTkFont(size=22, weight="bold"), text_color="#155724")
        self.lbl_card_ing_val.pack(pady=(20, 5))
        ctk.CTkLabel(self.card_ingresos_gen, text="Ingresos Totales Registrados", font=ctk.CTkFont(size=12), text_color="#155724").pack(pady=(0, 20))

        self.card_egresos_gen = ctk.CTkFrame(self.frame_cards, fg_color="#FFF3CD", corner_radius=10)
        self.card_egresos_gen.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        self.lbl_card_egr_val = ctk.CTkLabel(self.card_egresos_gen, text="$0.00", font=ctk.CTkFont(size=22, weight="bold"), text_color="#856404")
        self.lbl_card_egr_val.pack(pady=(20, 5))
        ctk.CTkLabel(self.card_egresos_gen, text="Egresos / Gastos Totales", font=ctk.CTkFont(size=12), text_color="#856404").pack(pady=(0, 20))

        frame_detalles_metodos = ctk.CTkFrame(frame_stats_main)
        frame_detalles_metodos.pack(fill="both", expand=True, padx=10, pady=20)
        ctk.CTkLabel(frame_detalles_metodos, text="Ingresos Acumulados por Metodo de Pago", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        self.txt_metodos_stats = ctk.CTkTextbox(frame_detalles_metodos, height=150, font=ctk.CTkFont(size=13))
        self.txt_metodos_stats.pack(fill="both", expand=True, padx=20, pady=10)
        self.txt_metodos_stats.configure(state="disabled")
        ctk.CTkButton(frame_stats_main, text="Actualizar Estadisticas", command=self.actualizar_estadisticas).pack(pady=10)
        self.actualizar_estadisticas()

    def actualizar_estadisticas(self):
        stats = obtener_estadisticas_generales()
        self.lbl_card_deuda_val.configure(text=f"${stats['total_deuda']:,.2f}")
        self.lbl_card_ing_val.configure(text=f"${stats['tot_ingresos']:,.2f}")
        self.lbl_card_egr_val.configure(text=f"${stats['tot_egresos']:,.2f}")
        texto_metodos = ""
        for metodo, monto in stats['metodos_ingreso'].items():
            texto_metodos += f"• {metodo}: ${monto:,.2f}\n"
        self.txt_metodos_stats.configure(state="normal")
        self.txt_metodos_stats.delete("0.0", "end")
        self.txt_metodos_stats.insert("0.0", texto_metodos)
        self.txt_metodos_stats.configure(state="disabled")

    def actualizar_calendario(self):
        self.cal_venc.calevent_remove('all')
        vencimientos = obtener_vencimientos_calendario()
        for fecha_obj, facturas_list in vencimientos.items():
            texto_tooltip = "\n".join(facturas_list)
            self.cal_venc.calevent_create(fecha_obj, texto_tooltip, "alerta_venc")
        self.cal_venc.tag_config("alerta_venc", background="#dc3545", foreground="white")

    def mostrar_detalle_fecha(self, event):
        fecha_sel = self.cal_venc.selection_get()
        ev_ids = self.cal_venc.get_calevents(date=fecha_sel)
        self.caja_detalle_venc.configure(state="normal")
        self.caja_detalle_venc.delete("0.0", "end")
        if ev_ids:
            textos = [self.cal_venc.calevent_cget(ev_id, 'text') for ev_id in ev_ids]
            self.caja_detalle_venc.insert("0.0", "\n".join(textos))
        else:
            self.caja_detalle_venc.insert("0.0", "Sin vencimientos este dia.")
        self.caja_detalle_venc.configure(state="disabled")

    def actualizar_tabla_proveedores(self):
        busq = self.entry_buscar_prov.get().strip() if hasattr(self, 'entry_buscar_prov') else ""
        for fila in self.tabla_prov.get_children():
            self.tabla_prov.delete(fila)
        for p in obtener_proveedores(busq):
            tag = "cero"
            if p['saldo'] > 0: tag = "alerta" if p['saldo'] > 50000 else "deuda"
            self.tabla_prov.insert("", "end", values=(p['id'], p['nombre'], f"${p['saldo']:.2f}"), tags=(tag,))

    def accion_nuevo_proveedor(self):
        self._abrir_dialogo_proveedor(es_nuevo=True)

    def accion_modificar_proveedor(self):
        seleccion = self.tabla_prov.selection()
        if not seleccion: return
        prov_id = self.tabla_prov.item(seleccion[0])['values'][0]
        self._abrir_dialogo_proveedor(es_nuevo=False, prov_id=prov_id)

    def _abrir_dialogo_proveedor(self, es_nuevo=True, prov_id=None):
        vent = ctk.CTkToplevel(self)
        vent.title("Nuevo Proveedor" if es_nuevo else "Modificar Proveedor")
        vent.geometry("350x180")
        vent.transient(self)
        try:
            ruta_icono = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.ico")
            vent.iconbitmap(ruta_icono)
        except Exception: pass
        ctk.CTkLabel(vent, text="Nombre del Proveedor:").pack(pady=(20,5))
        ent_nombre = ctk.CTkEntry(vent, width=250)
        ent_nombre.pack()
        if not es_nuevo and prov_id:
            prov = obtener_proveedor(prov_id)
            ent_nombre.insert(0, prov['nombre'])
        def guardar():
            nombre = ent_nombre.get().strip()
            if not nombre:
                self.marcar_error(ent_nombre)
                return
            if es_nuevo: agregar_proveedor(nombre)
            else: modificar_proveedor(prov_id, nombre)
            self.actualizar_tabla_proveedores()
            self.actualizar_estadisticas()
            vent.destroy()
        ctk.CTkButton(vent, text="Guardar", command=guardar).pack(pady=20)

    def accion_cargar_pedido(self):
        seleccion = self.tabla_prov.selection()
        if not seleccion: return
        prov_id, prov_nombre = self.tabla_prov.item(seleccion[0])['values'][:2]
        vent = ctk.CTkToplevel(self)
        vent.title(f"Recibir Pedido - {prov_nombre}")
        vent.geometry("400x480")
        vent.transient(self)
        try:
            ruta_icono = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.ico")
            vent.iconbitmap(ruta_icono)
        except Exception: pass
        def crear_campo(texto, placeholder=""):
            ctk.CTkLabel(vent, text=texto).pack(pady=(10,2))
            ent = ctk.CTkEntry(vent, width=300, placeholder_text=placeholder)
            ent.pack()
            return ent
        ent_monto = crear_campo("Monto de la Deuda ($) *:")
        ent_fact = crear_campo("Nro. Factura (Opcional):")
        ent_remito = crear_campo("Nro. Remito (Opcional):")
        ent_venc = crear_campo("Fecha Vencimiento (Si en blanco = 30 dias auto):", "Ej: 15/11/2026")
        ent_desc = crear_campo("Descripcion general:")
        
        def guardar():
            try:
                monto_str = ent_monto.get().replace(',', '.')
                if not monto_str: raise ValueError
                monto = float(monto_str)
                fecha_v = ent_venc.get().strip()
                if fecha_v:
                    try:
                        datetime.strptime(fecha_v, "%d/%m/%Y")
                    except ValueError:
                        messagebox.showerror("Error de Formato", "El formato debe ser DD/MM/AAAA.")
                        self.marcar_error(ent_venc)
                        return
                else:
                    fecha_v = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
                registrar_pedido_proveedor(prov_id, monto, ent_desc.get(), ent_fact.get(), ent_remito.get(), fecha_v)
                self.actualizar_tabla_proveedores()
                self.actualizar_calendario()
                self.actualizar_estadisticas()
                vent.destroy()
            except ValueError:
                self.marcar_error(ent_monto)
        ctk.CTkButton(vent, text="Guardar Pedido", command=guardar).pack(pady=25)

    def accion_pagar(self):
        seleccion = self.tabla_prov.selection()
        if not seleccion: return
        prov_id, prov_nombre = self.tabla_prov.item(seleccion[0])['values'][:2]
        vent = ctk.CTkToplevel(self)
        vent.title(f"Pagar a {prov_nombre}")
        vent.geometry("350x320")
        vent.transient(self)
        try:
            ruta_icono = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.ico")
            vent.iconbitmap(ruta_icono)
        except Exception: pass
        ctk.CTkLabel(vent, text="Monto a Pagar ($):").pack(pady=(20,5))
        ent_monto = ctk.CTkEntry(vent, width=200)
        ent_monto.pack()
        ctk.CTkLabel(vent, text="Medio de pago:").pack(pady=(15,5))
        combo_metodo = ctk.CTkComboBox(vent, values=[m.value for m in MetodoPago], width=200)
        combo_metodo.pack()
        var_caja = ctk.StringVar(value="on")
        switch = ctk.CTkSwitch(vent, text="Descontar de la Caja actual", variable=var_caja, onvalue="on", offvalue="off")
        switch.pack(pady=20)
        def procesar():
            try:
                monto = float(ent_monto.get().replace(',', '.'))
                if monto > 10000:
                    conf = messagebox.askyesno("Confirmar Pago", f"¿Estas seguro de registrar pago por ${monto:,.2f} a {prov_nombre}?")
                    if not conf: return
                metodo_enum = next(m for m in MetodoPago if m.value == combo_metodo.get())
                descontar = True if var_caja.get() == "on" else False
                pagar_deuda_proveedor(prov_id, monto, metodo_enum, descontar)
                self.actualizar_tabla_proveedores()
                self.actualizar_estado_caja()
                self.actualizar_calendario()
                self.actualizar_estadisticas()
                vent.destroy()
            except ValueError:
                self.marcar_error(ent_monto)
        ctk.CTkButton(vent, text="Procesar Pago", command=procesar).pack(pady=10)

    def accion_ver_historial_proveedor(self, event):
        seleccion = self.tabla_prov.selection()
        if not seleccion: return
        item = self.tabla_prov.item(seleccion[0])['values']
        prov_id, prov_nombre, saldo_actual = item[0], item[1], item[2]
        
        vent = ctk.CTkToplevel(self)
        vent.title(f"Historial - {prov_nombre}")
        vent.geometry("1100x480")
        vent.transient(self)
        try:
            ruta_icono = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono.ico")
            vent.iconbitmap(ruta_icono)
        except Exception: pass
        
        frame_top_hist = ctk.CTkFrame(vent, fg_color="transparent")
        frame_top_hist.pack(fill='x', padx=20, pady=(20,0))
        lbl_titulo = ctk.CTkLabel(frame_top_hist, text=f"Deuda Actual: {saldo_actual}", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_titulo.pack(side='left')
        
        def exportar():
            from services import obtener_historial_proveedor
            hist = obtener_historial_proveedor(prov_id)
            if not hist: return
            f_str = datetime.now().strftime("%Y%m%d_%H%M")
            n_pdf = f"resumen_cuenta_{prov_nombre.replace(' ', '_')}_{f_str}.pdf"
            generar_pdf_proveedor(prov_nombre, lbl_titulo.cget("text").replace("Deuda Actual: ", ""), hist, n_pdf)
            messagebox.showinfo("Exportado", f"Resumen generado exitosamente:\n{n_pdf}")
            
        ctk.CTkButton(frame_top_hist, text="Exportar a PDF", fg_color="#28a745", hover_color="#218838", command=exportar).pack(side='right')
        
        def abrir_edicion():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Atencion", "Selecciona un pedido de la lista para modificar.")
                return
            item_vals = tree.item(sel[0])['values']
            m_id, m_fecha, m_tipo, m_monto_str, m_fact, m_remito, m_venc, m_desc = item_vals[0], item_vals[1], item_vals[2], item_vals[3], item_vals[4], item_vals[5], item_vals[6], item_vals[7]
            
            if m_tipo != 'PEDIDO':
                messagebox.showerror("Error", "Solo puedes modificar PEDIDOS desde esta opcion.")
                return
            
            monto_limpio = str(m_monto_str).replace('$', '').replace(',', '')
            
            v_ed = ctk.CTkToplevel(vent)
            v_ed.title(f"Modificar Pedido - {prov_nombre}")
            v_ed.geometry("400x520")
            v_ed.transient(vent)
            v_ed.grab_set()
            
            def crear_campo(texto, valor):
                ctk.CTkLabel(v_ed, text=texto).pack(pady=(10,2))
                e = ctk.CTkEntry(v_ed, width=300)
                e.insert(0, valor if valor != "-" else "")
                e.pack()
                return e
                
            e_monto = crear_campo("Monto de la Deuda ($) *:", monto_limpio)
            e_fact = crear_campo("Nro. Factura:", m_fact)
            e_remito = crear_campo("Nro. Remito:", m_remito)
            e_venc = crear_campo("Fecha Vencimiento (DD/MM/AAAA):", m_venc)
            e_desc = crear_campo("Descripcion:", m_desc)
            
            def guardar():
                try:
                    nmonto = float(e_monto.get().replace(',', '.'))
                    fvenc = e_venc.get().strip()
                    if fvenc:
                        datetime.strptime(fvenc, "%d/%m/%Y") 
                    if messagebox.askyesno("Confirmar Cambios", "¿Estas seguro de guardar los cambios?\n\nEsto recalculara el historial."):
                        from services import modificar_pedido_proveedor, obtener_proveedor
                        modificar_pedido_proveedor(m_id, nmonto, e_desc.get(), e_fact.get(), e_remito.get(), fvenc)
                        cargar_arbol()
                        self.actualizar_tabla_proveedores()
                        self.actualizar_estadisticas()
                        if hasattr(self, 'actualizar_calendario'): self.actualizar_calendario()
                        p_act = obtener_proveedor(prov_id)
                        lbl_titulo.configure(text=f"Deuda Actual: ${p_act['saldo']:,.2f}")
                        v_ed.destroy()
                        messagebox.showinfo("Exito", "Pedido modificado correctamente.")
                except ValueError:
                    messagebox.showerror("Error", "Monto o Fecha invalida. Revisa los formatos.")
            ctk.CTkButton(v_ed, text="Guardar Cambios", fg_color="#ffc107", text_color="black", hover_color="#e0a800", command=guardar).pack(pady=25)
            
        ctk.CTkButton(frame_top_hist, text="Modificar Pedido", fg_color="#17a2b8", hover_color="#138496", command=abrir_edicion).pack(side='right', padx=10)
        
        cols = ("id", "fecha", "tipo", "monto", "factura", "remito", "venc", "desc", "saldo_mom")
        tree = ttk.Treeview(vent, columns=cols, show='headings', displaycolumns=("fecha", "tipo", "monto", "factura", "remito", "venc", "desc", "saldo_mom"))
        tree.tag_configure("pago", foreground="#007a1a")
        tree.tag_configure("pedido", foreground="#d90000")
        
        for col, txt in zip(cols[1:], ["Fecha", "Tipo", "Monto", "Factura", "Remito", "Venc.", "Descripcion", "Saldo Final Dia"]):
            tree.heading(col, text=txt)
            
        tree.column("fecha", width=120, anchor='center')
        tree.column("tipo", width=80, anchor='center')
        tree.column("monto", width=100, anchor='e')
        tree.column("factura", width=90, anchor='center')
        tree.column("remito", width=90, anchor='center')
        tree.column("venc", width=90, anchor='center')
        tree.column("desc", width=250)
        tree.column("saldo_mom", width=110, anchor='e')
        tree.pack(fill='both', expand=True, padx=20, pady=20)
        
        def cargar_arbol():
            from services import obtener_historial_proveedor
            for fila in tree.get_children(): tree.delete(fila)
            for h in obtener_historial_proveedor(prov_id):
                tag = "pago" if h['tipo'] == 'PAGO' else "pedido"
                m_str = f"${h['monto']:.2f}"
                if h['tipo'] == 'PAGO': m_str = f"- {m_str}"
                tree.insert("", "end", values=(h['id'], h['fecha'], h['tipo'], m_str, h['factura'], h['remito'], h['vencimiento'], h['descripcion'], f"${h['saldo_momento']:.2f}"), tags=(tag,))
        cargar_arbol()

if __name__ == "__main__":
    app = InterfazCajaApp()
    app.mainloop()
