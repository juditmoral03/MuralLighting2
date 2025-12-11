from nicegui import ui, app
import os
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import json

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

IS_PRODUCTION = os.environ.get('RENDER') is not None
NODE_BASE_URL = "/app" if IS_PRODUCTION else "http://127.0.0.1:3006"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# NOTA: Hemos eliminado las variables globales y el endpoint @app.post('/set_selected_window')
# porque causan conflictos entre usuarios.

menu_path = os.path.dirname(__file__) 
app.add_static_files('/menu', menu_path)

# CONSTANTS
C1, C2, C3, C4 = "Hanging oil lamp", "Two table candles", "Two floor chandeliers", "Four floor chandeliers"
D1T1, D1T2, D1T3 = "Time: 10:00 am", "Time: 10:53 am", "Time: 12:53 pm"
D2T1, D2T2, D2T3 = "Time: 10:00 am", "Time: 10:56 am", "Time: 13:56 pm"
D3T1, D3T2, D3T3 = "Time: 10:00 am", "Time: 11:53 am", "Time: 13:53 pm"
DEFAULT_IMAGE = "XII/Artificial/C1-pv2.exr"
DEFAULT_IMAGE2 = "XII/Artificial/C2-pv2.exr"

# --- PÁGINA PRINCIPAL ---

@ui.page('/')
async def main():
    # --- 1. ESTADO DE SESIÓN (ÚNICO POR USUARIO) ---
    class SessionState:
        def __init__(self):
            self.hour = None
            self.day = None
            self.selected_left = None
            self.selected_right = None
            self.all_cards = {} # Diccionario local de cartas
            self.iframe_container = None
            self.iframe = None
            # Placeholders para los contenedores UI
            self.c_nat1 = self.c_nat2 = self.c_nat3 = None
            self.c_na1 = self.c_na2 = None
            self.c_all1 = self.c_all2 = self.c_all3 = self.c_all4 = self.c_all5 = self.c_all6 = None

    state = SessionState()


    # Dentro de main(), al principio:
    
    def format_exr(image_name):
        # Esta lógica transforma "/menu/Natural/..." en "XII/Natural/..."
        if image_name.startswith('/menu/'):
            image_name = image_name[len('/menu/'):]
        parts = image_name.rsplit('/', 1)
        folder = parts[0]
        file_name = parts[1].rsplit('.', 1)[0]
        folder = folder.replace('+', '%2B')
        return f"XII/{folder}/{file_name}.exr"
    
    # Al principio de main(), junto a format_exr:
    
    def format_label_html(text, image_path):
        # 1. Formatear el texto principal
        text_str = "<br>".join(str(t) for t in text) if isinstance(text, list) else str(text)
        
        # 2. Inferir el día (Day)
        day = None
        if image_path:
            if "D2" in image_path: day = "Apr 1st"
            elif "D3" in image_path: day = "Jun 6th"
            elif "D1" in image_path: day = "Dec 25th"
        
        # 3. Combinar HTML
        if day:
            return f"{day}<br><span>{text_str}</span>"
        else:
            return text_str

    # --- 2. FUNCIONES AUXILIARES (DEFINIDAS DENTRO DE MAIN PARA ACCEDER A STATE) ---

    def show_selected_images():
        def format_exr(image_name):
            if image_name.startswith('/menu/'):
                image_name = image_name[len('/menu/'):]
            parts = image_name.rsplit('/', 1)
            folder = parts[0]
            file_name = parts[1].rsplit('.', 1)[0]
            folder = folder.replace('+', '%2B')
            return f"XII/{folder}/{file_name}.exr"

        def format_label_text(text):
            if isinstance(text, list):
                return "<br>".join(str(t) for t in text)
            return str(text)

        def infer_day_from_image(image_path):
            if not image_path: return None
            if "D2" in image_path: return "Apr 1st"
            elif "D3" in image_path: return "Jun 6th"
            elif "D1" in image_path: return "Dec 25th"
            return None
        
        img1 = format_exr(state.selected_left["image"]) if state.selected_left else DEFAULT_IMAGE
        img2 = format_exr(state.selected_right["image"]) if state.selected_right else DEFAULT_IMAGE2

        label1_main = format_label_text(state.selected_left["text"]) if state.selected_left else "Hanging oil lamp"
        label2_main = format_label_text(state.selected_right["text"]) if state.selected_right else "Two table candles"
    
        day1 = infer_day_from_image(state.selected_left["image"]) if state.selected_left else None
        day2 = infer_day_from_image(state.selected_right["image"]) if state.selected_right else None
    
        label1 = f"{day1}<br><span>{label1_main}</span>" if day1 else label1_main
        label2 = f"{day2}<br><span>{label2_main}</span>" if day2 else label2_main
    
        # Añadimos un parámetro 'dummy' (&v=2) para engañar al navegador y que crea que es un archivo nuevo
        url = f"{NODE_BASE_URL}/index.html?img1={img1}&img2={img2}&v=2"
    
        # En la función show_selected_images
        html = f"""
        <div style="position: relative; width: 100%; height: 100%;">
            <iframe 
                id="viewer-iframe" 
                src="{url}" 
                style="width:100%; height:100%; border:none; position: absolute; top:0; left:0; z-index:0;"
                allowfullscreen
                loading="lazy">
            </iframe>
            <div id="label-left" style="position: absolute; bottom: 60px; left: 25%; transform: translateX(-50%); font-size: 12px; font-weight: 500; color: #eee; text-align: center; text-shadow: 0 0 5px rgba(0,0,0,0.6); z-index: 2;">{label1}</div>
            <div id="label-right" style="position: absolute; bottom: 60px; left: 75%; transform: translateX(-50%); font-size: 12px; font-weight: 500; color: #eee; text-align: center; text-shadow: 0 0 5px rgba(0,0,0,0.6); z-index: 2;">{label2}</div>
        </div>
        """
        return html

    def update_all_cards_visibility():
        for image, buttons in state.all_cards.items():
            for button in buttons:
                button.set_visibility(False); button.props('flat fab')
                if image == (state.selected_left["image"] if state.selected_left else None):
                    button.set_visibility(True); button.props('color=white'); button.classes('absolute top-0 right-0 m-1 bg-white text-black font-bold text-[10px] flex items-center justify-center'); button._text = "L"
                elif image == (state.selected_right["image"] if state.selected_right else None):
                    button.set_visibility(True); button.props('color=white'); button.classes('absolute top-0 right-0 m-1 bg-white text-black font-bold text-[10px] flex items-center justify-center'); button._text = "R"

    def create_card(image, text, classes):
        with ui.card().tight().classes(classes) as c:
            with ui.image(image) as img:
                button = ui.button('', on_click=None).props('flat color=white').classes('absolute top-2 right-2 m-1 bg-white text-black font-bold text-[10px] flex items-center justify-center')
                button.set_visibility(False)
                button.style('width: 16px !important; height: 16px !important; min-width: 0 !important; min-height: 0 !important; border-radius: 50% !important; font-size: 8px !important; padding: 0 !important;')
                
                if image not in state.all_cards: state.all_cards[image] = []
                state.all_cards[image].append(button)
                
                async def toggle_selection():
                    selected_window = await ui.run_javascript('return localStorage.getItem("selectedWindow");')
                    
                    if not selected_window or selected_window == "none" or selected_window == "null": 
                        ui.notify("⚠️ Select a window first", color='orange')
                        return

                    text_json = json.dumps(text)
                    exr_path = format_exr(image)
                    
                    # Generamos el nuevo HTML para el texto
                    new_label_html = format_label_html(text, image)

                    if selected_window == "left":
                        state.selected_left = {"card": c, "image": image, "text": text}
                        await ui.run_javascript(f'localStorage.setItem("saved_L_img", "{image}");')
                        await ui.run_javascript(f'localStorage.setItem("saved_L_txt", \'{text_json}\');') 
                        
                        update_all_cards_visibility()
                        
                        # 1. Cambiar Imagen (Iframe)
                        js_img = f'var iframe = document.getElementById("viewer-iframe"); if(iframe) {{ iframe.contentWindow.postMessage({{ "type": "change_left", "path": "{exr_path}" }}, "*"); }}'
                        await ui.run_javascript(js_img)
                        
                        # 2. Cambiar Texto (Label) - ACTUALIZAMOS EL DOM DIRECTAMENTE
                        # Usamos .innerHTML para que interprete los <br> y <span>
                        await ui.run_javascript(f'document.getElementById("label-left").innerHTML = `{new_label_html}`;')
                        
                        return
                    
                    if selected_window == "right":
                        state.selected_right = {"card": c, "image": image, "text": text}
                        await ui.run_javascript(f'localStorage.setItem("saved_R_img", "{image}");')
                        await ui.run_javascript(f'localStorage.setItem("saved_R_txt", \'{text_json}\');')
                        
                        update_all_cards_visibility()
                        
                        # 1. Cambiar Imagen
                        js_img = f'var iframe = document.getElementById("viewer-iframe"); if(iframe) {{ iframe.contentWindow.postMessage({{ "type": "change_right", "path": "{exr_path}" }}, "*"); }}'
                        await ui.run_javascript(js_img)

                        # 2. Cambiar Texto
                        await ui.run_javascript(f'document.getElementById("label-right").innerHTML = `{new_label_html}`;')
                        
                        return
                img.on('click', toggle_selection)
            with ui.card_section():
                if isinstance(text, list):
                    for t in text: ui.markdown(t)
                else: ui.markdown(text)

    classes_card = "h-[24vh] w-[15vh]"

    # --- LÓGICA DE REFRESCO (Usa state.hour y state.day) ---
    # --- LÓGICA DE REFRESCO ACTUALIZADA ---
    def refresh_cards_natural():
        if not state.c_nat1: return
        
        gh = state.hour
        v_D2T1, v_D2T2, v_D2T3 = (gh=="10:00" or gh=="All" or not gh), (gh=="10:56" or gh=="All" or not gh), (gh=="13:56" or gh=="All" or not gh)
        v_D3T1, v_D3T2, v_D3T3 = (gh=="10:00" or gh=="All" or not gh), (gh=="11:53" or gh=="All" or not gh), (gh=="13:53" or gh=="All" or not gh)
        v_D1T1, v_D1T2, v_D1T3 = (gh=="10:00" or gh=="All" or not gh), (gh=="10:53" or gh=="All" or not gh), (gh=="12:53" or gh=="All" or not gh)
        if gh == "10:53": v_D2T1=v_D2T2=v_D2T3=v_D3T1=v_D3T2=v_D3T3=v_D1T1=v_D1T3=False
        if gh == "10:56": v_D2T1=v_D2T3=v_D3T1=v_D3T2=v_D3T3=v_D1T1=v_D1T2=v_D1T3=False
        
        lbl_style = "font-size: 1.6vh; font-weight: 400; margin-bottom: 0.5vh; color: black;"

        # Grupo 1: Apr 1st
        show_nat1 = (state.day is None or state.day == "Apr 1st" or state.day == "All") and (v_D2T1 or v_D2T2 or v_D2T3)
        state.c_nat1.set_visibility(show_nat1) # Ocultamos si no hay nada
        state.c_nat1.clear()
        if show_nat1:
            with state.c_nat1:
                ui.label("Apr 1st").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D2T1: create_card("/menu/Natural/D2T1-pv2.jpg", [D2T1], classes_card)
                    if v_D2T2: create_card("/menu/Natural/D2T2-pv2.jpg", [D2T2], classes_card)
                    if v_D2T3: create_card("/menu/Natural/D2T3-pv2.jpg", [D2T3], classes_card)

        # Grupo 2: Jun 6th
        show_nat2 = (state.day is None or state.day == "Jun 6th" or state.day == "All") and (v_D3T1 or v_D3T2 or v_D3T3)
        state.c_nat2.set_visibility(show_nat2)
        state.c_nat2.clear()
        if show_nat2:
            with state.c_nat2:
                ui.label("Jun 6th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D3T1: create_card("/menu/Natural/D3T1-pv2.jpg", [D3T1], classes_card)
                    if v_D3T2: create_card("/menu/Natural/D3T2-pv2.jpg", [D3T2], classes_card)
                    if v_D3T3: create_card("/menu/Natural/D3T3-pv2.jpg", [D3T3], classes_card)

        # Grupo 3: Dec 25th
        show_nat3 = (state.day is None or state.day == "Dec 25th" or state.day == "All") and (v_D1T1 or v_D1T2 or v_D1T3)
        state.c_nat3.set_visibility(show_nat3)
        state.c_nat3.clear()
        if show_nat3:
            with state.c_nat3:
                ui.label("Dec 25th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D1T1: create_card("/menu/Natural/D1T1-pv2.jpg", [D1T1], classes_card)
                    if v_D1T2: create_card("/menu/Natural/D1T2-pv2.jpg", [D1T2], classes_card)
                    if v_D1T3: create_card("/menu/Natural/D1T3-pv2.jpg", [D1T3], classes_card)
        update_all_cards_visibility()

    def refresh_cards_natart():
        if not state.c_na1: return
        
        gh = state.hour
        v_D1T3_C2 = v_D1T3_C5 = True; v_D2T3_C2 = v_D2T3_C5 = True
        if gh == "12:53": v_D2T3_C2 = v_D2T3_C5 = False
        elif gh == "13:56": v_D1T3_C2 = v_D1T3_C5 = False
        elif gh and gh != "All" and gh not in ["12:53", "13:56"]: v_D1T3_C2 = v_D1T3_C5 = v_D2T3_C2 = v_D2T3_C5 = False
        
        lbl_style = "font-size: 1.6vh; font-weight: 400; margin-bottom: 0.5vh; color: black;"

        # Grupo 1
        show_na1 = (v_D2T3_C2 or v_D2T3_C5) and (state.day is None or state.day == "Apr 1st" or state.day == "All")
        state.c_na1.set_visibility(show_na1)
        state.c_na1.clear()
        if show_na1:
            with state.c_na1:
                ui.label("Apr 1st").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D2T3_C2: create_card("/menu/Natural+Artificial/D2T3-C2-pv2.jpg", [D2T3,C2], classes_card)
                    if v_D2T3_C5: create_card("/menu/Natural+Artificial/D2T3-C5-pv2.jpg", [D2T3,C1,C2,C4], classes_card)
        
        # Grupo 2
        show_na2 = (v_D1T3_C5 or v_D1T3_C2) and (state.day is None or state.day == "Dec 25th" or state.day == "All")
        state.c_na2.set_visibility(show_na2)
        state.c_na2.clear()
        if show_na2:
            with state.c_na2:
                ui.label("Dec 25th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D1T3_C2: create_card("/menu/Natural+Artificial/D1T3-C2-pv2.jpg", [D1T3,C2], classes_card)
                    if v_D1T3_C5: create_card("/menu/Natural+Artificial/D1T3-C5-pv2.jpg", [D1T3,C1,C2,C4], classes_card)
        update_all_cards_visibility()

    def refresh_cards_all():
        if not state.c_all1: return
        
        gh = state.hour
        # ... Tus variables booleanas de hora (copia aquí toda tu lógica de horas igual que antes) ...
        v_nat_D2T1=v_nat_D2T2=v_nat_D2T3=True; v_nat_D3T1=v_nat_D3T2=v_nat_D3T3=True; v_nat_D1T1=v_nat_D1T2=v_nat_D1T3=True
        v_na_D1T3_C2=v_na_D1T3_C5=True; v_na_D2T3_C2=v_na_D2T3_C5=True

        if gh == "10:00":
             v_nat_D2T2=v_nat_D2T3=v_nat_D3T2=v_nat_D3T3=v_nat_D1T2=v_nat_D1T3=False
             v_na_D1T3_C2=v_na_D1T3_C5=v_na_D2T3_C2=v_na_D2T3_C5=False
        elif gh == "10:53":
             v_nat_D2T1=v_nat_D2T2=v_nat_D2T3=v_nat_D3T1=v_nat_D3T2=v_nat_D3T3=v_nat_D1T1=v_nat_D1T3=False
             v_na_D1T3_C2=v_na_D1T3_C5=v_na_D2T3_C2=v_na_D2T3_C5=False
        elif gh == "10:56":
             v_nat_D2T1=v_nat_D2T3=v_nat_D3T1=v_nat_D3T2=v_nat_D3T3=v_nat_D1T1=v_nat_D1T2=v_nat_D1T3=False
             v_na_D1T3_C2=v_na_D1T3_C5=v_na_D2T3_C2=v_na_D2T3_C5=False
        elif gh == "11:53":
             v_nat_D2T1=v_nat_D2T2=v_nat_D2T3=v_nat_D3T1=v_nat_D3T3=v_nat_D1T1=v_nat_D1T2=v_nat_D1T3=False
             v_na_D1T3_C2=v_na_D1T3_C5=v_na_D2T3_C2=v_na_D2T3_C5=False
        elif gh == "12:53":
             v_nat_D2T1=v_nat_D2T2=v_nat_D2T3=v_nat_D3T1=v_nat_D3T2=v_nat_D3T3=v_nat_D1T1=v_nat_D1T2=False
             v_na_D2T3_C2=v_na_D2T3_C5=False 
        elif gh == "13:53":
             v_nat_D2T1=v_nat_D2T2=v_nat_D2T3=v_nat_D3T1=v_nat_D3T2=False
             v_nat_D1T1=v_nat_D1T2=v_nat_D1T3=False
             v_na_D1T3_C2=v_na_D1T3_C5=v_na_D2T3_C2=v_na_D2T3_C5=False
        elif gh == "13:56":
             v_nat_D2T1=v_nat_D2T2=False; v_nat_D3T1=v_nat_D3T2=v_nat_D3T3=False; v_nat_D1T1=v_nat_D1T2=v_nat_D1T3=False
             v_na_D1T3_C2=v_na_D1T3_C5=False

        lbl_style = "font-size: 1.6vh; font-weight: 400; margin-bottom: 0.5vh; color: black;"
        
        # --- SECCIÓN NATURAL (En All) ---
        show_all1 = (state.day is None or state.day == "Apr 1st" or state.day == "All") and (v_nat_D2T1 or v_nat_D2T2 or v_nat_D2T3)
        state.c_all1.set_visibility(show_all1); state.c_all1.clear()
        if show_all1:
            with state.c_all1:
                ui.label("Apr 1st").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_nat_D2T1: create_card("/menu/Natural/D2T1-pv2.jpg", [D2T1], classes_card)
                    if v_nat_D2T2: create_card("/menu/Natural/D2T2-pv2.jpg", [D2T2], classes_card)
                    if v_nat_D2T3: create_card("/menu/Natural/D2T3-pv2.jpg", [D2T3], classes_card)
        
        show_all2 = (state.day is None or state.day == "Jun 6th" or state.day == "All") and (v_nat_D3T1 or v_nat_D3T2 or v_nat_D3T3)
        state.c_all2.set_visibility(show_all2); state.c_all2.clear()
        if show_all2:
            with state.c_all2:
                ui.label("Jun 6th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_nat_D3T1: create_card("/menu/Natural/D3T1-pv2.jpg", [D3T1], classes_card)
                    if v_nat_D3T2: create_card("/menu/Natural/D3T2-pv2.jpg", [D3T2], classes_card)
                    if v_nat_D3T3: create_card("/menu/Natural/D3T3-pv2.jpg", [D3T3], classes_card)
        
        show_all3 = (state.day is None or state.day == "Dec 25th" or state.day == "All") and (v_nat_D1T1 or v_nat_D1T2 or v_nat_D1T3)
        state.c_all3.set_visibility(show_all3); state.c_all3.clear()
        if show_all3:
            with state.c_all3:
                ui.label("Dec 25th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_nat_D1T1: create_card("/menu/Natural/D1T1-pv2.jpg", [D1T1], classes_card)
                    if v_nat_D1T2: create_card("/menu/Natural/D1T2-pv2.jpg", [D1T2], classes_card)
                    if v_nat_D1T3: create_card("/menu/Natural/D1T3-pv2.jpg", [D1T3], classes_card)
        
        # --- SECCIÓN ARTIFICIAL (En All) - Siempre visible ---
        state.c_all4.clear()
        with state.c_all4:
             ui.label("Spacer").style(lbl_style + "visibility: hidden;")
             with ui.row().classes('gap-2 items-start'): 
                create_card("/menu/Artificial/C1-pv2.jpg", [C1], classes_card)
                create_card("/menu/Artificial/C2-pv2.jpg", [C2], classes_card)
                create_card("/menu/Artificial/C3-pv2.jpg", [C3], classes_card)
                create_card("/menu/Artificial/C4-pv2.jpg", [C4], classes_card)
                create_card("/menu/Artificial/C5-pv2.jpg", [C1, C2, C4], classes_card)
        
        # --- SECCIÓN NAT+ART (En All) ---
        show_all5 = (v_na_D2T3_C2 or v_na_D2T3_C5) and (state.day is None or state.day == "Apr 1st" or state.day == "All")
        state.c_all5.set_visibility(show_all5); state.c_all5.clear()
        if show_all5:
            with state.c_all5:
                ui.label("Apr 1st").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_na_D2T3_C2: create_card("/menu/Natural+Artificial/D2T3-C2-pv2.jpg", [D2T3,C2], classes_card)
                    if v_na_D2T3_C5: create_card("/menu/Natural+Artificial/D2T3-C5-pv2.jpg", [D2T3,C1,C2,C4], classes_card)
        
        show_all6 = (v_na_D1T3_C5 or v_na_D1T3_C2) and (state.day is None or state.day == "Dec 25th" or state.day == "All")
        state.c_all6.set_visibility(show_all6); state.c_all6.clear()
        if show_all6:
            with state.c_all6:
                ui.label("Dec 25th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_na_D1T3_C2: create_card("/menu/Natural+Artificial/D1T3-C2-pv2.jpg", [D1T3,C2], classes_card)
                    if v_na_D1T3_C5: create_card("/menu/Natural+Artificial/D1T3-C5-pv2.jpg", [D1T3,C1,C2,C4], classes_card)
        update_all_cards_visibility()

    def refresh_all_views():
        refresh_cards_natural()
        refresh_cards_natart()
        refresh_cards_all()

    # --- HTML Y ESTILOS ---
    
    # Javascript helper para restaurar la ventana seleccionada en local storage (Visuales)
    ui.add_body_html("""
    <script>
    async function restoreSelectedWindow() {
        const container = document.getElementById('container');
        if (!container) return;
        let saved = localStorage.getItem('selectedWindow');
        if (saved) {
            updateSelectedWindowHighlight(saved);
        }
        // Listener para clicks en el iframe
        container.addEventListener('click', async (e) => {
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            let selectedWindow = (x < rect.width / 2) ? 'left' : 'right';
            localStorage.setItem('selectedWindow', selectedWindow);
            updateSelectedWindowHighlight(selectedWindow);
        });
    }
    window.addEventListener('load', restoreSelectedWindow);
    </script>
    """)


    # ... código anterior ...

    # JS helper para escuchar al iframe y guardar la selección en el localStorage PRINCIPAL
    ui.add_body_html("""
    <script>
    // 1. Escuchar mensajes que vienen del Iframe (puerto 3006)
    window.addEventListener('message', function(event) {
        // Verificamos que sea nuestro mensaje
        if (event.data && event.data.type === 'window_selected') {
            console.log("Recibido desde Iframe:", event.data.value);
            
            // 2. Guardar en el localStorage del PADRE (puerto 8080)
            localStorage.setItem('selectedWindow', event.data.value);
        }
    });

    // Código visual para restaurar (opcional, el que ya tenías)
    async function restoreSelectedWindow() {
        // ... (tu código anterior si lo necesitas) ...
    }
    </script>
    """)
    
    # ... resto del código ...

    ui.add_head_html('''
    <style>
    body, html { margin: 0; padding: 0; overflow: hidden; width: 100%; height: 100%; }
    .menu-row { width: 100%; margin: 0; padding: 0; background-color: white; }
    .dropdown-panel {
        position: absolute; top: 100%; left: 0; right: 0; height: auto; max-height: 85vh;
        background-color: white; z-index: 40; display: flex; flex-direction: column; align-items: stretch;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding-bottom: 25px; 
    }
    .dropdown-panel .q-card { 
        box-shadow: 0 2px 5px rgba(0,0,0,0.15) !important; border: 1px solid #e0e0e0;
        display: flex; flex-direction: column; padding: 0 !important; margin: 0 !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .dropdown-panel .q-card:hover {
        transform: translateY(-2px); box-shadow: 0 8px 15px rgba(0,0,0,0.2) !important; z-index: 10;
    }
    .dropdown-panel .q-card .q-img { height: 60%; width: 100%; object-fit: cover; }
    .dropdown-panel .q-card__section { 
        height: 40%; padding: 2px 4px !important; display: flex; flex-direction: column;
        justify-content: center; align-items: center; text-align: center; line-height: 1.15; 
    }
    .dropdown-panel .q-card__section p, .dropdown-panel .q-card__section div {
        font-size: 1.25vh; color: #333; overflow: hidden;
    }
    .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 200, 'GRAD' 0, 'opsz' 24 }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap" />
    ''')

    categories = ["Inici", "Natural illumination", "Artificial illumination", "Natural + Artificial illumination", "All combinations"]
    menu_panels = {}

    # --- WRAPPER PRINCIPAL UI ---
    with ui.column().classes('absolute-full gap-0 no-wrap'):

        # --- MENU ROW ---
        with ui.element('div').classes('w-full bg-white shadow-sm z-50 relative flex flex-col md:flex-row items-center px-2 md:px-6 py-2 md:py-0 h-auto md:h-[80px]'):
            
            ui.element('div').classes('hidden md:block') # Spacer Left

            # 2. Categorías (Centro)
            active_panel = {'name': None}
            def show_panel(e, cat):
                current = active_panel['name']
                if current and current in menu_panels and current != cat:
                    menu_panels[current].set_visibility(False)
                if cat != "Inici":
                    if cat in menu_panels:
                        menu_panels[cat].set_visibility(True)
                        active_panel['name'] = cat
                else:
                    if current and current in menu_panels: menu_panels[current].set_visibility(False)
                    active_panel['name'] = None

            with ui.row().classes('w-full md:w-auto flex justify-center gap-8 md:absolute md:left-1/2 md:transform md:-translate-x-1/2 flex-wrap md:flex-nowrap'):
                for cat in categories:
                    # (Tu lógica de iconos se mantiene igual)
                    if cat == "Inici": ui.icon('home', size='28px').classes('cursor-pointer text-gray-700 hover:text-black hover:bg-gray-100 p-1 rounded transition material-symbols-outlined').on('mouseover', lambda e, cat=cat: show_panel(e, cat))
                    elif cat == "Natural illumination": ui.icon('sunny', size='28px').classes('cursor-pointer text-gray-700 hover:text-black hover:bg-gray-100 p-1 rounded transition material-symbols-outlined').on('mouseover', lambda e, cat=cat: show_panel(e, cat))
                    elif cat == "Artificial illumination": ui.icon('lightbulb_2', size='28px').classes('cursor-pointer text-gray-700 hover:text-black hover:bg-gray-100 p-1 rounded transition material-symbols-outlined').on('mouseover', lambda e, cat=cat: show_panel(e, cat))
                    elif cat == "Natural + Artificial illumination":
                        with ui.row().classes('cursor-pointer hover:bg-gray-100 p-1 rounded transition items-center gap-1').on('mouseover', lambda e, cat=cat: show_panel(e, cat)):
                            ui.icon('sunny', size='28px').classes('material-symbols-outlined text-gray-700')
                            ui.label('+').style('font-size: 20px; font-weight: 300;')
                            ui.icon('lightbulb_2', size='28px').classes('material-symbols-outlined text-gray-700')
                    elif cat == "All combinations":
                        ui.label('ALL').classes('cursor-pointer hover:bg-gray-100 px-2 py-1 rounded transition text-gray-700 font-light text-lg').on('mouseover', lambda e, cat=cat: show_panel(e, cat))

            # 3. Filtros (Derecha)
            with ui.row().classes('w-full md:w-auto flex justify-center md:justify-end gap-6 md:ml-auto items-center flex-nowrap mt-2 md:mt-0'):
                
                # HOUR
                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    def toggle_hour_menu(): hour_menu.toggle()
                    icon_hour = ui.icon('access_time', size="22px").classes('cursor-pointer text-gray-600 hover:text-black material-symbols-outlined').on('click', toggle_hour_menu)
                    label_hour = ui.label("").classes('text-sm text-black cursor-pointer hover:text-black whitespace-nowrap').on('click', toggle_hour_menu); label_hour.set_visibility(False)
                    with ui.menu().props('auto-close="false" anchor="bottom middle" self="top middle"').classes('bg-white shadow-xl rounded-md p-2 z-50 w-40') as hour_menu:
                        ui.label("Global Hour").classes('text-xs font-bold text-gray-400 px-2 py-1 uppercase'); ui.separator().classes('mb-1')
                        def set_global_hour_fn(h):
                            state.hour = h; ui.run_javascript(f'localStorage.setItem("global_hour", "{h}")')
                            if h == "All": icon_hour.set_visibility(True); label_hour.set_visibility(False)
                            else: icon_hour.set_visibility(False); label_hour.set_text(h); label_hour.set_visibility(True)
                            refresh_all_views()
                        ui.menu_item("All", lambda: set_global_hour_fn("All")); ui.menu_item("10:00 am", lambda: set_global_hour_fn("10:00"))
                        ui.menu_item("10:53 am", lambda: set_global_hour_fn("10:53")); ui.menu_item("10:56 am", lambda: set_global_hour_fn("10:56"))
                        ui.menu_item("11:53 am", lambda: set_global_hour_fn("11:53")); ui.menu_item("12:53 pm", lambda: set_global_hour_fn("12:53"))
                        ui.menu_item("13:53 pm", lambda: set_global_hour_fn("13:53")); ui.menu_item("13:56 pm", lambda: set_global_hour_fn("13:56"))

                # DAY
                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    def toggle_day_menu(): day_menu.toggle()
                    icon_day = ui.icon('calendar_today', size="22px").classes('cursor-pointer text-gray-600 hover:text-black material-symbols-outlined').on('click', toggle_day_menu)
                    label_day = ui.label("").classes('text-sm text-black cursor-pointer hover:text-black whitespace-nowrap').on('click', toggle_day_menu); label_day.set_visibility(False)
                    with ui.menu().props('auto-close="false" anchor="bottom middle" self="top middle"').classes('bg-white shadow-xl rounded-md p-2 z-50 w-40') as day_menu:
                        ui.label("Global Day").classes('text-xs font-bold text-gray-400 px-2 py-1 uppercase'); ui.separator().classes('mb-1')
                        def set_global_day_fn(d):
                            state.day = d; ui.run_javascript(f'localStorage.setItem("global_day", "{d}")')
                            if d == "All": icon_day.set_visibility(True); label_day.set_visibility(False)
                            else: icon_day.set_visibility(False); label_day.set_text(d); label_day.set_visibility(True)
                            refresh_all_views()
                        ui.menu_item("All", lambda: set_global_day_fn("All")); ui.menu_item("Apr 1st", lambda: set_global_day_fn("Apr 1st"))
                        ui.menu_item("Jun 6th", lambda: set_global_day_fn("Jun 6th")); ui.menu_item("Dec 25th", lambda: set_global_day_fn("Dec 25th"))

                # VISIBILITY
                # VISIBILITY
                # CORRECCIÓN: Usamos 'with' para meter el icono DENTRO del div, igual que los otros.
                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    ui.icon('visibility', size="22px") \
                        .classes('cursor-pointer text-gray-600 hover:text-black material-symbols-outlined') \
                       

                async def restore_globals():
                    # Recuperar estado del navegador para este usuario
                    g_hour = await ui.run_javascript('return localStorage.getItem("global_hour")')
                    g_day = await ui.run_javascript('return localStorage.getItem("global_day")')
                    
                    if g_hour and g_hour != "All" and g_hour != "null": 
                        state.hour = g_hour; icon_hour.set_visibility(False); label_hour.set_text(g_hour); label_hour.set_visibility(True)
                    else: 
                        icon_hour.set_visibility(True); label_hour.set_visibility(False)
                    
                    if g_day and g_day != "All" and g_day != "null": 
                        state.day = g_day; icon_day.set_visibility(False); label_day.set_text(g_day); label_day.set_visibility(True)
                    else: 
                        icon_day.set_visibility(True); label_day.set_visibility(False)
                    
                    refresh_all_views()
                
                ui.timer(0.1, restore_globals, once=True)


                # ... código existente de restore_globals ...

                async def restore_session_images():
                # 1. Recuperar datos de la Izquierda
                    l_img = await ui.run_javascript('return localStorage.getItem("saved_L_img");')
                    l_txt_raw = await ui.run_javascript('return localStorage.getItem("saved_L_txt");') # Traemos texto crudo
                    
                    l_txt = None
                    if l_txt_raw and l_txt_raw != "null":
                        try:
                            l_txt = json.loads(l_txt_raw) # Convertimos en Python (más seguro)
                        except:
                            pass # Si falla, simplemente ignoramos el texto

                    if l_img and l_img != "null":
                        state.selected_left = {"card": None, "image": l_img, "text": l_txt if l_txt else "Loading..."}

                    # 2. Recuperar datos de la Derecha
                    r_img = await ui.run_javascript('return localStorage.getItem("saved_R_img");')
                    r_txt_raw = await ui.run_javascript('return localStorage.getItem("saved_R_txt");')
                    
                    r_txt = None
                    if r_txt_raw and r_txt_raw != "null":
                        try:
                            r_txt = json.loads(r_txt_raw)
                        except:
                            pass

                    if r_img and r_img != "null":
                        state.selected_right = {"card": None, "image": r_img, "text": r_txt if r_txt else "Loading..."}

                    # 3. Actualizar vista
                    if l_img or r_img:
                        update_all_cards_visibility()
                        if state.iframe_container: 
                            state.iframe_container.content = show_selected_images()

                ui.timer(0.2, restore_session_images, once=True)
            # --- PANELES DESPLEGABLES ---
            # --- PANELES DESPLEGABLES ---
            def hide_panel(panel_key):
                if panel_key in menu_panels: menu_panels[panel_key].set_visibility(False)
                if active_panel['name'] == panel_key: active_panel['name'] = None

            # 1. NATURAL ILLUMINATION
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["Natural illumination"] = panel; panel.on('mouseleave', lambda: hide_panel("Natural illumination"))
                # CAMBIO: Añadido gap-[3vh] y quitados los margin-left de las columnas
                with ui.row().classes('w-full overflow-x-auto no-scrollbar gap-[3vh]').style('padding-left: 5vh; white-space: nowrap; padding-top: 3vh; padding-bottom: 3vh;'):
                    with ui.row().classes('justify-start gap-[3vh] items-start flex-nowrap').style('display: inline-flex;'):
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_nat1: pass
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_nat2: pass
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_nat3: pass

            # 2. ARTIFICIAL ILLUMINATION
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["Artificial illumination"] = panel; panel.on('mouseleave', lambda: hide_panel("Artificial illumination"))
                with ui.row().classes('w-full overflow-x-auto no-scrollbar').style('padding-left: 5vh; white-space: nowrap; padding-top: 3vh; padding-bottom: 3vh;'):
                    with ui.row().classes('justify-start gap-2 items-start flex-nowrap').style('display: inline-flex;'):
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start; margin-left: 0px;'):
                            with ui.row().classes('gap-2 items-start'):
                                create_card("/menu/Artificial/C1-pv2.jpg", [C1], classes_card); create_card("/menu/Artificial/C2-pv2.jpg", [C2], classes_card)
                                create_card("/menu/Artificial/C3-pv2.jpg", [C3], classes_card); create_card("/menu/Artificial/C4-pv2.jpg", [C4], classes_card)
                                create_card("/menu/Artificial/C5-pv2.jpg", [C1, C2, C4], classes_card)

            # 3. NATURAL + ARTIFICIAL
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["Natural + Artificial illumination"] = panel; panel.on('mouseleave', lambda: hide_panel("Natural + Artificial illumination"))
                # CAMBIO: Añadido gap-[3vh] y quitados los margin-left
                with ui.row().classes('w-full overflow-x-auto no-scrollbar gap-[3vh]').style('padding-left: 5vh; white-space: nowrap; padding-top: 3vh; padding-bottom: 3vh;'):
                    with ui.row().classes('justify-start gap-[3vh] items-start flex-nowrap').style('display: inline-flex;'):
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_na1: pass
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_na2: pass

            # 4. ALL COMBINATIONS
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["All combinations"] = panel; panel.on('mouseleave', lambda: hide_panel("All combinations"))
                # CAMBIO: Ajuste de gaps y quitados los margin-left internos
                with ui.row().classes('cards-wrapper w-full overflow-x-auto overflow-y-hidden no-scrollbar flex-nowrap pl-10 pr-10 items-start').style('white-space: nowrap; margin-top: 3vh; padding-bottom: 3vh; gap: 6vh;'):
                    
                    # Columna Grupo Natural
                    with ui.column().classes('items-start w-auto flex-shrink-0'):
                        ui.label("Natural illumination").classes('text-black font-semibold mb-2').style('font-size: 2vh;')
                        with ui.row().classes('items-start gap-[2vh]'): # Gap aquí
                            with ui.column().classes('flex-shrink-0') as state.c_all1: pass
                            with ui.column().classes('flex-shrink-0') as state.c_all2: pass
                            with ui.column().classes('flex-shrink-0') as state.c_all3: pass
                    
                    # Columna Grupo Artificial
                    with ui.column().classes('items-start w-auto flex-shrink-0'):
                        ui.label("Artificial illumination").classes('text-black font-semibold mb-2').style('font-size: 2vh;')
                        with ui.row().classes('gap-1 items-start'):
                            with ui.column().classes('flex-shrink-0') as state.c_all4: pass
                    
                    # Columna Grupo Nat+Art
                    with ui.column().classes('items-start w-auto flex-shrink-0'):
                        ui.label("Natural+Artificial illumination").classes('text-black font-semibold mb-2').style('font-size: 2vh;')
                        with ui.row().classes('items-start gap-[2vh]'): # Gap aquí
                            with ui.column().classes('flex-shrink-0') as state.c_all5: pass
                            with ui.column().classes('flex-shrink-0') as state.c_all6: pass
        # --- IFRAME VIEWER ---
        state.iframe_container = ui.html(show_selected_images(), sanitize=False).classes('w-full flex-grow').style('border: none; margin: 0; padding: 0;')

ui.run()