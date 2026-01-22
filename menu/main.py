from nicegui import ui, app
import os
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import json

# --- CONFIGURATION & ENVIRONMENT SETUP ---
# Determine if running in production (Render) or local development
IS_PRODUCTION = os.environ.get('RENDER') is not None
# Set the base URL for the Node.js backend/viewer depending on the environment
NODE_BASE_URL = "/app" if IS_PRODUCTION else "http://127.0.0.1:3006"

# Configure CORS to allow requests from any origin (standard for this type of setup)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount the 'menu' directory to serve static images for the UI cards
menu_path = os.path.dirname(__file__) 
app.add_static_files('/menu', menu_path)

# --- CONSTANTS & DATA ---

C1, C2, C3, C4 = "Hanging oil lamp", "Two table candles", "Two floor chandeliers", "Four floor chandeliers"
D1T1, D1T2, D1T3 = "Time: 10:00 am", "Time: 10:53 am", "Time: 12:53 pm" # Dec 25th
D2T1, D2T2, D2T3 = "Time: 10:00 am", "Time: 10:56 am", "Time: 13:56 pm" # Apr 1st
D3T1, D3T2, D3T3 = "Time: 10:00 am", "Time: 11:53 am", "Time: 13:53 pm" # Jun 6th

# Default images to load when the app starts
DEFAULT_IMAGE = "XII/Artificial/C1-pv2.exr"
DEFAULT_IMAGE2 = "XII/Artificial/C2-pv2.exr"

# --- MAIN PAGE ENTRY POINT ---

@ui.page('/')
async def main():
    # --- 1. SESSION STATE ---
    # Stores state specific to the current connected user/browser tab
    class SessionState:
        def __init__(self):
            self.hour = None          # Global filter: Selected hour
            self.day = None           # Global filter: Selected day
            self.selected_left = None # Currently selected image data for Left View
            self.selected_right = None# Currently selected image data for Right View
            self.all_cards = {}       # Dictionary to track UI button references for toggling visibility
            self.iframe_container = None # Reference to the HTML container holding the iframe
            self.iframe = None
            # Placeholders for UI containers (Natural, Mixed, All combinations)
            # These allow us to clear and repopulate specific sections dynamically
            self.c_nat1 = self.c_nat2 = self.c_nat3 = None
            self.c_na1 = self.c_na2 = None
            self.c_all1 = self.c_all2 = self.c_all3 = self.c_all4 = self.c_all5 = self.c_all6 = None

    state = SessionState()

    # --- 2. HELPER FUNCTIONS ---

    def format_exr(image_name):
        """
        Converts the UI thumbnail path (jpg) to the backend EXR path.
        Handles URL encoding for special characters like '+'.
        """
        if image_name.startswith('/menu/'):
            image_name = image_name[len('/menu/'):]
        parts = image_name.rsplit('/', 1)
        folder = parts[0]
        file_name = parts[1].rsplit('.', 1)[0]
        folder = folder.replace('+', '%2B') # Encode '+' for URL safety
        return f"XII/{folder}/{file_name}.exr"
    
    def format_label_html(text, image_path):
        """
        Formats the overlay label text to include the Date (inferred from filename)
        and the Description. Returns HTML string.
        """
        text_str = "<br>".join(str(t) for t in text) if isinstance(text, list) else str(text)
        day = None
        if image_path:
            if "D2" in image_path: day = "Apr 1st"
            elif "D3" in image_path: day = "Jun 6th"
            elif "D1" in image_path: day = "Dec 25th"
        
        if day:
            return f"{day}<br><span>{text_str}</span>"
        else:
            return text_str

    def show_selected_images():
        """
        Generates the HTML code for the Iframe viewer.
        It constructs the URL with query parameters (img1, img2) and
        creates the overlay divs for text labels.
        """
        # Internal helper to format paths
        def format_exr_inner(image_name):
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
        
        # Determine images and labels based on session state or defaults
        img1 = format_exr_inner(state.selected_left["image"]) if state.selected_left else DEFAULT_IMAGE
        img2 = format_exr_inner(state.selected_right["image"]) if state.selected_right else DEFAULT_IMAGE2

        label1_main = format_label_text(state.selected_left["text"]) if state.selected_left else "Hanging oil lamp"
        label2_main = format_label_text(state.selected_right["text"]) if state.selected_right else "Two table candles"
    
        day1 = infer_day_from_image(state.selected_left["image"]) if state.selected_left else None
        day2 = infer_day_from_image(state.selected_right["image"]) if state.selected_right else None
    
        label1 = f"{day1}<br><span>{label1_main}</span>" if day1 else label1_main
        label2 = f"{day2}<br><span>{label2_main}</span>" if day2 else label2_main
    
        # Construct the Viewer URL
        url = f"{NODE_BASE_URL}/index.html?img1={img1}&img2={img2}&v=2"
    
        # Return the complete HTML block (Iframe + Absolute positioned labels)
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
        """
        Iterates through all UI cards to update the 'Selected' badge (L or R).
        Shows the badge only if the card matches the currently selected Left or Right image.
        """
        for image, buttons in state.all_cards.items():
            for button in buttons:
                button.set_visibility(False); button.props('flat fab')
                if image == (state.selected_left["image"] if state.selected_left else None):
                    # Style for Left selection
                    button.set_visibility(True); button.props('color=white'); button.classes('absolute top-0 right-0 m-1 bg-white text-black font-bold text-[10px] flex items-center justify-center'); button._text = "L"
                elif image == (state.selected_right["image"] if state.selected_right else None):
                    # Style for Right selection
                    button.set_visibility(True); button.props('color=white'); button.classes('absolute top-0 right-0 m-1 bg-white text-black font-bold text-[10px] flex items-center justify-center'); button._text = "R"

    def create_card(image, text, classes):
        """
        Creates a UI card representing a specific lighting scenario.
        Handles the 'Click' event to select the image.
        """
        with ui.card().tight().classes(classes) as c:
            with ui.image(image) as img:
                # The 'Badge' button indicating selection state
                button = ui.button('', on_click=None).props('flat color=white').classes('absolute top-2 right-2 m-1 bg-white text-black font-bold text-[10px] flex items-center justify-center')
                button.set_visibility(False)
                button.style('width: 16px !important; height: 16px !important; min-width: 0 !important; min-height: 0 !important; border-radius: 50% !important; font-size: 8px !important; padding: 0 !important;')
                
                # Register button in state for later updates
                if image not in state.all_cards: state.all_cards[image] = []
                state.all_cards[image].append(button)
                
                # --- CLICK HANDLER ---
                async def toggle_selection():
                    # Check Client-side localStorage to see which view (Left/Right) is currently active
                    selected_window = await ui.run_javascript('return localStorage.getItem("selectedWindow");')
                    
                    if not selected_window or selected_window == "none" or selected_window == "null": 
                        ui.notify("⚠️ Select a window first", color='orange')
                        return

                    text_json = json.dumps(text)
                    exr_path = format_exr(image)
                    new_label_html = format_label_html(text, image)

                    # Update LEFT View
                    if selected_window == "left":
                        state.selected_left = {"card": c, "image": image, "text": text}
                        await ui.run_javascript(f'localStorage.setItem("saved_L_img", "{image}");')
                        await ui.run_javascript(f'localStorage.setItem("saved_L_txt", \'{text_json}\');') 
                        update_all_cards_visibility()
                        # Send Message to Iframe to update texture without reload
                        js_img = f'var iframe = document.getElementById("viewer-iframe"); if(iframe) {{ iframe.contentWindow.postMessage({{ "type": "change_left", "path": "{exr_path}" }}, "*"); }}'
                        await ui.run_javascript(js_img)
                        # Update HTML label directly
                        await ui.run_javascript(f'document.getElementById("label-left").innerHTML = `{new_label_html}`;')
                        return
                    
                    # Update RIGHT View
                    if selected_window == "right":
                        state.selected_right = {"card": c, "image": image, "text": text}
                        await ui.run_javascript(f'localStorage.setItem("saved_R_img", "{image}");')
                        await ui.run_javascript(f'localStorage.setItem("saved_R_txt", \'{text_json}\');')
                        update_all_cards_visibility()
                        js_img = f'var iframe = document.getElementById("viewer-iframe"); if(iframe) {{ iframe.contentWindow.postMessage({{ "type": "change_right", "path": "{exr_path}" }}, "*"); }}'
                        await ui.run_javascript(js_img)
                        await ui.run_javascript(f'document.getElementById("label-right").innerHTML = `{new_label_html}`;')
                        return
                img.on('click', toggle_selection)
            with ui.card_section():
                if isinstance(text, list):
                    for t in text: ui.markdown(t)
                else: ui.markdown(text)

    classes_card = "h-[20vh] w-[15vh]"

    # --- 3. REFRESH LOGIC (FILTERING) ---
    # These functions rebuild the menu panels based on the selected Hour/Day filters.

    def refresh_cards_natural():
        """Refreshes the 'Natural Illumination' panel."""
        if not state.c_nat1: return
        
        gh = state.hour
        # Determine visibility booleans for each time slot based on the selected Global Hour (gh)
        v_D2T1, v_D2T2, v_D2T3 = (gh=="10:00" or gh=="All" or not gh), (gh=="10:56" or gh=="All" or not gh), (gh=="13:56" or gh=="All" or not gh)
        v_D3T1, v_D3T2, v_D3T3 = (gh=="10:00" or gh=="All" or not gh), (gh=="11:53" or gh=="All" or not gh), (gh=="13:53" or gh=="All" or not gh)
        v_D1T1, v_D1T2, v_D1T3 = (gh=="10:00" or gh=="All" or not gh), (gh=="10:53" or gh=="All" or not gh), (gh=="12:53" or gh=="All" or not gh)
        
        # Specific overrides for incompatible times
        if gh == "10:53": v_D2T1=v_D2T2=v_D2T3=v_D3T1=v_D3T2=v_D3T3=v_D1T1=v_D1T3=False
        if gh == "10:56": v_D2T1=v_D2T3=v_D3T1=v_D3T2=v_D3T3=v_D1T1=v_D1T2=v_D1T3=False
        
        lbl_style = "font-size: 1.6vh; font-weight: 400; margin-bottom: 2px; color: black;"

        # Render April 1st Section
        show_nat1 = (state.day is None or state.day == "Apr 1st" or state.day == "All") and (v_D2T1 or v_D2T2 or v_D2T3)
        state.c_nat1.set_visibility(show_nat1); state.c_nat1.clear()
        if show_nat1:
            with state.c_nat1:
                ui.label("Apr 1st").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D2T1: create_card("/menu/Natural/D2T1-pv2.jpg", [D2T1], classes_card)
                    if v_D2T2: create_card("/menu/Natural/D2T2-pv2.jpg", [D2T2], classes_card)
                    if v_D2T3: create_card("/menu/Natural/D2T3-pv2.jpg", [D2T3], classes_card)

        # Render June 6th Section
        show_nat2 = (state.day is None or state.day == "Jun 6th" or state.day == "All") and (v_D3T1 or v_D3T2 or v_D3T3)
        state.c_nat2.set_visibility(show_nat2); state.c_nat2.clear()
        if show_nat2:
            with state.c_nat2:
                ui.label("Jun 6th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D3T1: create_card("/menu/Natural/D3T1-pv2.jpg", [D3T1], classes_card)
                    if v_D3T2: create_card("/menu/Natural/D3T2-pv2.jpg", [D3T2], classes_card)
                    if v_D3T3: create_card("/menu/Natural/D3T3-pv2.jpg", [D3T3], classes_card)

        # Render Dec 25th Section
        show_nat3 = (state.day is None or state.day == "Dec 25th" or state.day == "All") and (v_D1T1 or v_D1T2 or v_D1T3)
        state.c_nat3.set_visibility(show_nat3); state.c_nat3.clear()
        if show_nat3:
            with state.c_nat3:
                ui.label("Dec 25th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D1T1: create_card("/menu/Natural/D1T1-pv2.jpg", [D1T1], classes_card)
                    if v_D1T2: create_card("/menu/Natural/D1T2-pv2.jpg", [D1T2], classes_card)
                    if v_D1T3: create_card("/menu/Natural/D1T3-pv2.jpg", [D1T3], classes_card)
        update_all_cards_visibility()

    def refresh_cards_natart():
        """Refreshes the 'Natural + Artificial' panel."""
        if not state.c_na1: return
        
        gh = state.hour
        v_D1T3_C2 = v_D1T3_C5 = True; v_D2T3_C2 = v_D2T3_C5 = True
        
        # Logic to hide incompatible mixed scenarios
        if gh == "12:53": v_D2T3_C2 = v_D2T3_C5 = False
        elif gh == "13:56": v_D1T3_C2 = v_D1T3_C5 = False
        elif gh and gh != "All" and gh not in ["12:53", "13:56"]: v_D1T3_C2 = v_D1T3_C5 = v_D2T3_C2 = v_D2T3_C5 = False
        
        lbl_style = "font-size: 1.6vh; font-weight: 400; margin-bottom: 0.5vh; color: black;"

        # Render sections based on day filter and visibility logic
        show_na1 = (v_D2T3_C2 or v_D2T3_C5) and (state.day is None or state.day == "Apr 1st" or state.day == "All")
        state.c_na1.set_visibility(show_na1); state.c_na1.clear()
        if show_na1:
            with state.c_na1:
                ui.label("Apr 1st").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D2T3_C2: create_card("/menu/Natural+Artificial/D2T3-C2-pv2.jpg", [D2T3,C2], classes_card)
                    if v_D2T3_C5: create_card("/menu/Natural+Artificial/D2T3-C5-pv2.jpg", [D2T3,"All artificial lighting"], classes_card)
        
        show_na2 = (v_D1T3_C5 or v_D1T3_C2) and (state.day is None or state.day == "Dec 25th" or state.day == "All")
        state.c_na2.set_visibility(show_na2); state.c_na2.clear()
        if show_na2:
            with state.c_na2:
                ui.label("Dec 25th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D1T3_C2: create_card("/menu/Natural+Artificial/D1T3-C2-pv2.jpg", [D1T3,C2], classes_card)
                    if v_D1T3_C5: create_card("/menu/Natural+Artificial/D1T3-C5-pv2.jpg", [D1T3,"All artificial lighting"], classes_card)
        update_all_cards_visibility()

    def refresh_cards_all():
        """Refreshes the 'All Combinations' panel (Large wide menu)."""
        if not state.c_all1: return
        
        gh = state.hour
        # Default all to True
        v_nat_D2T1=v_nat_D2T2=v_nat_D2T3=True; v_nat_D3T1=v_nat_D3T2=v_nat_D3T3=True; v_nat_D1T1=v_nat_D1T2=v_nat_D1T3=True
        v_na_D1T3_C2=v_na_D1T3_C5=True; v_na_D2T3_C2=v_na_D2T3_C5=True

        # Extensive logic to disable specific cards based on selected hour
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
        
        # --- NATURAL SECTION (in All) ---
        show_all1 = (state.day is None or state.day == "Apr 1st" or state.day == "All") and (v_nat_D2T1 or v_nat_D2T2 or v_nat_D2T3)
        state.c_all1.set_visibility(show_all1); state.c_all1.clear()
        if show_all1:
            with state.c_all1:
                ui.label("Apr 1st").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_nat_D2T1: create_card("/menu/Natural/D2T1-pv2.jpg", [D2T1], classes_card)
                    if v_nat_D2T2: create_card("/menu/Natural/D2T2-pv2.jpg", [D2T2], classes_card)
                    if v_nat_D2T3: create_card("/menu/Natural/D2T3-pv2.jpg", [D2T3], classes_card)
        
        # ... (Similar logic for June 6th and Dec 25th in 'All' view)
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
        
        # --- ARTIFICIAL SECTION (in All) ---
        state.c_all4.clear()
        with state.c_all4:
             ui.label("Spacer").style(lbl_style + "visibility: hidden;")
             with ui.row().classes('gap-2 items-start'): 
                create_card("/menu/Artificial/C1-pv2.jpg", [C1], classes_card)
                create_card("/menu/Artificial/C2-pv2.jpg", [C2], classes_card)
                create_card("/menu/Artificial/C3-pv2.jpg", [C3], classes_card)
                create_card("/menu/Artificial/C4-pv2.jpg", [C4], classes_card)
                create_card("/menu/Artificial/C5-pv2.jpg", ["All artificial lighting"], classes_card)
        
        # --- NAT+ART SECTION (in All) ---
        show_all5 = (v_na_D2T3_C2 or v_na_D2T3_C5) and (state.day is None or state.day == "Apr 1st" or state.day == "All")
        state.c_all5.set_visibility(show_all5); state.c_all5.clear()
        if show_all5:
            with state.c_all5:
                ui.label("Apr 1st").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_na_D2T3_C2: create_card("/menu/Natural+Artificial/D2T3-C2-pv2.jpg", [D2T3,C2], classes_card)
                    if v_na_D2T3_C5: create_card("/menu/Natural+Artificial/D2T3-C5-pv2.jpg", [D2T3,"All artificial lighting"], classes_card)
        
        show_all6 = (v_na_D1T3_C5 or v_na_D1T3_C2) and (state.day is None or state.day == "Dec 25th" or state.day == "All")
        state.c_all6.set_visibility(show_all6); state.c_all6.clear()
        if show_all6:
            with state.c_all6:
                ui.label("Dec 25th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_na_D1T3_C2: create_card("/menu/Natural+Artificial/D1T3-C2-pv2.jpg", [D1T3,C2], classes_card)
                    if v_na_D1T3_C5: create_card("/menu/Natural+Artificial/D1T3-C5-pv2.jpg", [D1T3,"All artificial lighting"], classes_card)
        update_all_cards_visibility()

    def refresh_all_views():
        """Master refresh function."""
        refresh_cards_natural()
        refresh_cards_natart()
        refresh_cards_all()

    # --- 4. HTML INJECTION & STYLES ---
    
    # Inject JS to handle click detection on the container (Split screen logic)
    ui.add_body_html("""
    <script>
    async function restoreSelectedWindow() {
        const container = document.getElementById('container');
        if (!container) return;
        
        // Restore previous selection from local storage
        let saved = localStorage.getItem('selectedWindow');
        if (saved) {
            updateSelectedWindowHighlight(saved);
        }
        
        // Listen for clicks to determine which side (Left/Right) is active
        container.addEventListener('click', async (e) => {
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            let selectedWindow = (x < rect.width / 2) ? 'left' : 'right';
            localStorage.setItem('selectedWindow', selectedWindow);
            updateSelectedWindowHighlight(selectedWindow);
        });
    }
    window.addEventListener('load', restoreSelectedWindow);
    
    // Listen for messages from the Iframe
    window.addEventListener('message', function(event) {
        if (event.data && event.data.type === 'window_selected') {
            console.log("Recibido desde Iframe:", event.data.value);
            localStorage.setItem('selectedWindow', event.data.value);
        }
    });
    </script>
    """)

    # Inject CSS for custom scrollbars and dropdown panel animations
    ui.add_head_html('''
    <style>
    body, html { margin: 0; padding: 0; overflow: hidden; width: 100%; height: 100%; }
    .menu-row { width: 100%; margin: 0; padding: 0; background-color: white; }
    
    .dropdown-panel {
        position: absolute; top: 100%; left: 0; right: 0; height: auto; max-height: 85vh;
        background-color: white; z-index: 40; display: flex; flex-direction: column; align-items: stretch;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding-bottom: 5px; 
    }
    
    .dropdown-panel .q-card { 
        box-shadow: 0 2px 5px rgba(0,0,0,0.15) !important; border: 1px solid #e0e0e0;
        display: flex; flex-direction: column; padding: 0 !important; margin: 0 !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .dropdown-panel .q-card:hover {
        transform: translateY(-2px); box-shadow: 0 8px 15px rgba(0,0,0,0.2) !important; z-index: 10;
    }
    
    .dropdown-panel .q-card .q-img { height: 70%; width: 100%; object-fit: cover; }
    
    .dropdown-panel .q-card__section { 
        height: 30%; 
        display: flex !important; flex-direction: column !important;
        justify-content: center !important; align-items: center !important; 
    }

    .dropdown-panel .q-card__section div, 
    .dropdown-panel .q-card__section p,
    .dropdown-panel .q-card__section span {
        text-align: center !important; width: 100% !important; margin: 0 !important;
        line-height: 1.1 !important; font-size: 1.15vh !important; color: #333;
    }

    .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 200, 'GRAD' 0, 'opsz' 24 }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap" />
    ''')

    categories = ["Inici", "Natural illumination", "Artificial illumination", "Natural + Artificial illumination", "All combinations"]
    menu_panels = {}

   
    # --- HOME INFO DIALOG ---
    with ui.dialog() as home_dialog, ui.card().classes('w-[600px] max-w-[90vw] p-0'):
        # Header with Title and Close 'X'
        with ui.row().classes('w-full items-center justify-between p-4 bg-gray-100 border-b'):
            ui.label('About the Application').classes('text-lg font-bold text-gray-800')
            # The 'X' to close
            ui.icon('close').classes('cursor-pointer text-gray-500 hover:text-black hover:bg-gray-200 rounded-full p-1 transition') \
                .on('click', home_dialog.close)
        
        # Scrollable Content Area
        with ui.scroll_area().classes('h-[50vh] p-6'):
            # Style definition for the icons inside markdown
            icon_style = "vertical-align: text-bottom; font-size: 1.2rem; margin-right: 4px; color: #555;"

            ui.markdown(f"""
            ### Mural Lighting Viewer
            
            This tool allows you to rediscover the original perception of mural paintings through the simulation of historical light, both natural and artificial.
            
            #### How does it work?
            
            1. **Window Selection (Split Screen):**
               - Click on the **Left** or **Right** half of the screen to activate it.
               - Once selected, a **yellow border** will appear around that half.
               - Select an image from the menu to load it on that side.
               
            2. **Lighting Menus:**
               Hover over the top icons to view the options:
               - <span class="material-symbols-outlined" style="{icon_style}">sunny</span> **Natural:** Different times and months of the year.
               - <span class="material-symbols-outlined" style="{icon_style}">lightbulb_2</span> **Artificial:** Candles, oil lamps, and chandeliers.
               - <span class="material-symbols-outlined" style="{icon_style}">sunny</span><span style="vertical-align: text-bottom;">+</span><span class="material-symbols-outlined" style="{icon_style}">lightbulb_2</span> **Combinacions:** Mixture of natural and artificial light.
               - <span style=" font-size: 0.9rem;">ALL</span> **All Combinations:** All options in a single large panel.
            
            3. **Global Filters:**
               - <span class="material-symbols-outlined" style="{icon_style}">access_time</span> **Clock**: Filter by time.
               - <span class="material-symbols-outlined" style="{icon_style}">calendar_today</span> **Calendar**: Filter by date.
            
            4. **Tools (Left):**
               - <span class="material-symbols-outlined" style="{icon_style}">link</span> **Sync (Link):** Moves both cameras simultaneously if enabled.
               - <span class="material-symbols-outlined" style="{icon_style}">tune</span> **Tone Mapping:** Opens a dropdown menu where you can adjust image processing settings.
               - <span class="material-symbols-outlined" style="{icon_style}">difference</span> **Difference:** Visualizes the changes between the two images.
            """).classes('text-gray-700 leading-relaxed')

    ui.timer(0.1, home_dialog.open, once=True)


            
        

    # --- 5. UI LAYOUT CONSTRUCTION ---
    with ui.column().classes('absolute-full gap-0 no-wrap'):

        # --- MENU ROW (TOP BAR) ---
        with ui.element('div').classes('w-full bg-white shadow-sm z-50 relative flex flex-col md:flex-row items-center px-2 md:px-6 py-1 md:py-0 h-auto md:h-[50px]'):
            
            # --- [1] LEFT: TOOLS (SYNC, TONE MAPPING) ---
            with ui.row().classes('items-center justify-start md:mr-auto z-50'):
                # A) SYNC VIEW TOGGLE
                sync_state = {'active': True}
                async def toggle_sync():
                    sync_state['active'] = not sync_state['active']
                    if sync_state['active']: icon_sync.classes('text-black', remove='text-gray-300')
                    else: icon_sync.classes('text-gray-300', remove='text-black')
                    
                    # Post message to iframe to enable/disable camera sync
                    await ui.run_javascript(f'''
                        var iframe = document.getElementById("viewer-iframe");
                        if(iframe) {{
                            iframe.contentWindow.postMessage({{ 
                                "type": "toggle_sync", 
                                "value": {str(sync_state['active']).lower()} 
                            }}, "*");
                        }}
                    ''')

                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    icon_sync = ui.icon('link', size="22px") \
                        .classes('cursor-pointer text-black hover:text-gray-600 material-symbols-outlined transition-colors') \
                        .on('click', toggle_sync)
                    with ui.tooltip('Sync Views'): pass


                 # --- B) TONE MAPPING (DYNAMIC MENU) ---
                tm_state = {
                    'algo': 'toneMappingReinhardBasic', 
                    'target': 'both',
                    'fix': False,
                    # Parameters for different algorithms
                    'exposure': 1.0,  
                    'key': 0.18,      
                    'white': 1.0,     
                    'maxLum': 0.00005 
                }

                async def update_tm_js():
                    # Send entire Tone Mapping state to JS
                    await ui.run_javascript(f'''
                        var iframe = document.getElementById("viewer-iframe");
                        if(iframe) {{
                            iframe.contentWindow.postMessage({{ 
                                "type": "tm_update", 
                                "algo": "{tm_state['algo']}",
                                "target": "{tm_state['target']}",
                                "fix": {str(tm_state['fix']).lower()},
                                "exposure": {tm_state['exposure']},
                                "key": {tm_state['key']},
                                "white": {tm_state['white']},
                                "maxLum": {tm_state['maxLum']}
                            }}, "*");
                        }}
                    ''')

                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    ui.icon('tune', size="22px").classes('cursor-pointer text-gray-600 hover:text-black material-symbols-outlined')
                    
                    # Tone Mapping Dropdown Menu
                    with ui.menu().props('auto-close="false" anchor="bottom middle" self="top middle"').classes('bg-white shadow-xl rounded-md p-4 z-50 w-64'):
                        ui.label("Tone Mapping").classes('text-xs font-bold text-gray-400 mb-2 uppercase')
                        
                        # 1. Target (Both, Window 1, Window 2)
                        ui.select(
                            options={'both': 'Both Windows', 'window1': 'Window 1', 'window2': 'Window 2'},
                            value=tm_state['target'], label="Apply To"
                        ).bind_value(tm_state, 'target').on_value_change(update_tm_js).classes('w-full mb-2 text-sm')

                        # 2. Algorithm Selector
                        ui.select(
                            options={
                                "toneMappingLinear": "Linear", 
                                "toneMappingReinhardBasic": "Reinhard Basic", 
                                "toneMappingReinhardExtended": "Reinhard Extended", 
                                "toneMappingLuminance": "Luminance"
                            },
                            value=tm_state['algo'], label="Algorithm"
                        ).bind_value(tm_state, 'algo').on_value_change(update_tm_js).classes('w-full mb-2 text-sm')
                        
                        # --- DYNAMIC CONTROLS (Visibility depends on selected Algo) ---

                        # Exposure Slider
                        with ui.column().classes('w-full p-0 m-0 gap-0').bind_visibility_from(tm_state, 'algo', backward=lambda x: x in ['toneMappingLinear', 'toneMappingReinhardBasic']):
                            ui.label("Exposure").classes('text-xs text-gray-500 mt-2')
                            with ui.row().classes('w-full items-center gap-2'):
                                ui.slider(min=0.1, max=10.0, step=0.1, value=tm_state['exposure']).bind_value(tm_state, 'exposure').on_value_change(update_tm_js).classes('col-grow')
                                ui.label().bind_text_from(tm_state, 'exposure', backward=lambda x: f"{x:.1f}").classes('text-xs w-8 text-right')

                        # Reinhard Extended Sliders
                        with ui.column().classes('w-full p-0 m-0 gap-0').bind_visibility_from(tm_state, 'algo', backward=lambda x: x == 'toneMappingReinhardExtended'):
                            # Key
                            ui.label("Key").classes('text-xs text-gray-500 mt-2')
                            with ui.row().classes('w-full items-center gap-2'):
                                ui.slider(min=0.0, max=1.0, step=0.01, value=tm_state['key']).bind_value(tm_state, 'key').on_value_change(update_tm_js).classes('col-grow')
                                ui.label().bind_text_from(tm_state, 'key', backward=lambda x: f"{x:.2f}").classes('text-xs w-8 text-right')
                            # L White
                            ui.label("L White").classes('text-xs text-gray-500 mt-1')
                            with ui.row().classes('w-full items-center gap-2'):
                                ui.slider(min=0.1, max=10.0, step=0.1, value=tm_state['white']).bind_value(tm_state, 'white').on_value_change(update_tm_js).classes('col-grow')
                                ui.label().bind_text_from(tm_state, 'white', backward=lambda x: f"{x:.1f}").classes('text-xs w-8 text-right')

                        # Luminance Slider
                        with ui.column().classes('w-full p-0 m-0 gap-0').bind_visibility_from(tm_state, 'algo', backward=lambda x: x == 'toneMappingLuminance'):
                            ui.label("Max Luminance").classes('text-xs text-gray-500 mt-2')
                            with ui.row().classes('w-full items-center gap-2'):
                                ui.slider(min=0.00001, max=0.001, step=0.00001, value=tm_state['maxLum']) \
                                    .bind_value(tm_state, 'maxLum') \
                                    .on_value_change(update_tm_js) \
                                    .classes('col-grow')
                                
                                ui.label().bind_text_from(
                                    tm_state, 
                                    'maxLum', 
                                    backward=lambda x: f"{x:.5f}".rstrip('0').rstrip('.')
                                ).classes('text-xs w-12 text-right')
                                
                        # Fix Normalization toggle
                        ui.separator().classes('my-2')
                        ui.switch('Fix Normalization', value=tm_state['fix']).bind_value(tm_state, 'fix').on_value_change(update_tm_js).props('dense').classes('text-sm text-gray-700 w-full') 
                    with ui.tooltip('Tone Mapping'): pass
                    
                # C) IMAGE DIFFERENCE TOOL
                async def open_diff_js():
                    await ui.run_javascript('''
                        var iframe = document.getElementById("viewer-iframe");
                        if(iframe) {
                            iframe.contentWindow.postMessage({ "type": "open_diff" }, "*");
                        }
                    ''')

                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    ui.icon('difference', size="22px") \
                        .classes('cursor-pointer text-gray-600 hover:text-black material-symbols-outlined') \
                        .on('click', open_diff_js)
                    with ui.tooltip('Image Difference'): pass


            # --- [2] CENTER: CATEGORIES (MAIN MENU) ---
            active_panel = {'name': None}
            def show_panel(e, cat):
                """Mouse-over handler to show/hide category panels."""
                current = active_panel['name']
                if current and current in menu_panels and current != cat:
                    menu_panels[current].set_visibility(False)
                if cat != "Inici":
                    if cat in menu_panels:
                        menu_panels[cat].set_visibility(True)
                        active_panel['name'] = cat
                else:
                    # Hide all if Home/Inici is hovered
                    if current and current in menu_panels: menu_panels[current].set_visibility(False)
                    active_panel['name'] = None

            with ui.row().classes('w-full md:w-auto flex justify-center gap-8 md:absolute md:left-1/2 md:transform md:-translate-x-1/2 flex-wrap md:flex-nowrap'):
                icon_size = '24px' 
                for cat in categories:
                    # Render icons for each category with mouseover events
                    if cat == "Inici": 
                        
                        ui.icon('info', size=icon_size).classes('cursor-pointer text-gray-700 hover:text-black hover:bg-gray-100 p-1 rounded transition material-symbols-outlined') \
                            .on('mouseover', lambda e, cat=cat: show_panel(e, cat)) \
                            .on('click', home_dialog.open) 

                    elif cat == "Natural illumination": 
                        ui.icon('sunny', size=icon_size).classes('cursor-pointer text-gray-700 hover:text-black hover:bg-gray-100 p-1 rounded transition material-symbols-outlined').on('mouseover', lambda e, cat=cat: show_panel(e, cat))
                    elif cat == "Artificial illumination": 
                        ui.icon('lightbulb_2', size=icon_size).classes('cursor-pointer text-gray-700 hover:text-black hover:bg-gray-100 p-1 rounded transition material-symbols-outlined').on('mouseover', lambda e, cat=cat: show_panel(e, cat))
                    elif cat == "Natural + Artificial illumination":
                        with ui.row().classes('cursor-pointer hover:bg-gray-100 p-1 rounded transition items-center gap-1').on('mouseover', lambda e, cat=cat: show_panel(e, cat)):
                            ui.icon('sunny', size=icon_size).classes('material-symbols-outlined text-gray-700')
                            ui.label('+').style('font-size: 18px; font-weight: 300;')
                            ui.icon('lightbulb_2', size=icon_size).classes('material-symbols-outlined text-gray-700')
                    elif cat == "All combinations":
                        ui.label('ALL').classes('cursor-pointer hover:bg-gray-100 px-2 py-1 rounded transition text-gray-700 font-light text-md').on('mouseover', lambda e, cat=cat: show_panel(e, cat))

            # --- [3] RIGHT: FILTERS (HOUR / DAY) ---
            with ui.row().classes('w-full md:w-auto flex justify-center md:justify-end gap-6 md:ml-auto items-center flex-nowrap mt-2 md:mt-0'):
                
                # --- [B] HOUR FILTER ---
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

                # --- [C] DAY FILTER ---
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

                # --- [D] VISIBILITY ICON (Placeholder) ---
                #with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    #ui.icon('visibility', size="22px").classes('cursor-pointer text-gray-600 hover:text-black material-symbols-outlined')

                # --- LIFECYCLE: RESTORE STATE FROM LOCALSTORAGE ---
                async def restore_globals():
                    """Restores selected hour/day from browser storage on load."""
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

                async def restore_session_images():
                    """Restores previously selected images (Left/Right) from browser storage."""
                    l_img = await ui.run_javascript('return localStorage.getItem("saved_L_img");')
                    l_txt_raw = await ui.run_javascript('return localStorage.getItem("saved_L_txt");')
                    l_txt = None
                    if l_txt_raw and l_txt_raw != "null":
                        try: l_txt = json.loads(l_txt_raw)
                        except: pass

                    if l_img and l_img != "null":
                        state.selected_left = {"card": None, "image": l_img, "text": l_txt if l_txt else "Loading..."}

                    r_img = await ui.run_javascript('return localStorage.getItem("saved_R_img");')
                    r_txt_raw = await ui.run_javascript('return localStorage.getItem("saved_R_txt");')
                    r_txt = None
                    if r_txt_raw and r_txt_raw != "null":
                        try: r_txt = json.loads(r_txt_raw)
                        except: pass

                    if l_img or r_img:
                        update_all_cards_visibility()
                        if state.iframe_container: 
                            state.iframe_container.content = show_selected_images()

                ui.timer(0.2, restore_session_images, once=True)

            # --- DROPDOWN PANELS ---

            def hide_panel(panel_key):
                if panel_key in menu_panels: menu_panels[panel_key].set_visibility(False)
                if active_panel['name'] == panel_key: active_panel['name'] = None

            # 1. Natural Panel
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["Natural illumination"] = panel; panel.on('mouseleave', lambda: hide_panel("Natural illumination"))
                with ui.row().classes('w-full overflow-x-auto no-scrollbar gap-[3vh]').style('padding-left: 5vh; white-space: nowrap; padding-top: 1.5vh; padding-bottom: 1.5vh;'):
                    with ui.row().classes('justify-start gap-[3vh] items-start flex-nowrap').style('display: inline-flex;'):
                        # Placeholders to be filled by refresh_cards_natural
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_nat1: pass
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_nat2: pass
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_nat3: pass

            # 2. Artificial Panel (Static content)
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["Artificial illumination"] = panel; panel.on('mouseleave', lambda: hide_panel("Artificial illumination"))
                with ui.row().classes('w-full overflow-x-auto no-scrollbar').style('padding-left: 5vh; white-space: nowrap; padding-top: 1.5vh; padding-bottom: 1.5vh;'):
                    with ui.row().classes('justify-start gap-2 items-start flex-nowrap').style('display: inline-flex;'):
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start; margin-left: 0px;'):
                            with ui.row().classes('gap-2 items-start'):
                                create_card("/menu/Artificial/C1-pv2.jpg", [C1], classes_card); create_card("/menu/Artificial/C2-pv2.jpg", [C2], classes_card)
                                create_card("/menu/Artificial/C3-pv2.jpg", [C3], classes_card); create_card("/menu/Artificial/C4-pv2.jpg", [C4], classes_card)
                                create_card("/menu/Artificial/C5-pv2.jpg", ["All artificial lighting"], classes_card)

            # 3. Mixed Panel
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["Natural + Artificial illumination"] = panel; panel.on('mouseleave', lambda: hide_panel("Natural + Artificial illumination"))
                with ui.row().classes('w-full overflow-x-auto no-scrollbar gap-[3vh]').style('padding-left: 5vh; white-space: nowrap; padding-top: 1.5vh; padding-bottom: 1.5vh;'):
                    with ui.row().classes('justify-start gap-[3vh] items-start flex-nowrap').style('display: inline-flex;'):
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_na1: pass
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_na2: pass

            # 4. All Combinations Panel
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["All combinations"] = panel; panel.on('mouseleave', lambda: hide_panel("All combinations"))
                with ui.row().classes('cards-wrapper w-full overflow-x-auto overflow-y-hidden no-scrollbar flex-nowrap pl-10 pr-10 items-start').style('white-space: nowrap; margin-top: 1.5vh; padding-bottom: 1.5vh; gap: 6vh;'):
                    
                    with ui.column().classes('items-start w-auto flex-shrink-0'):
                        ui.label("Natural illumination").classes('text-black font-semibold mb-1').style('font-size: 2vh;') 
                        with ui.row().classes('items-start gap-[2vh]'): 
                            with ui.column().classes('flex-shrink-0') as state.c_all1: pass
                            with ui.column().classes('flex-shrink-0') as state.c_all2: pass
                            with ui.column().classes('flex-shrink-0') as state.c_all3: pass
                    
                    with ui.column().classes('items-start w-auto flex-shrink-0'):
                        ui.label("Artificial illumination").classes('text-black font-semibold mb-1').style('font-size: 2vh;') 
                        with ui.row().classes('gap-1 items-start'):
                            with ui.column().classes('flex-shrink-0') as state.c_all4: pass
                    
                    with ui.column().classes('items-start w-auto flex-shrink-0'):
                        ui.label("Natural+Artificial illumination").classes('text-black font-semibold mb-1').style('font-size: 2vh;') 
                        with ui.row().classes('items-start gap-[2vh]'): 
                            with ui.column().classes('flex-shrink-0') as state.c_all5: pass
                            with ui.column().classes('flex-shrink-0') as state.c_all6: pass
        
        # --- IFRAME VIEWER CONTAINER ---
        state.iframe_container = ui.html(show_selected_images(), sanitize=False).classes('w-full flex-grow').style('border: none; margin: 0; padding: 0;')

ui.run(title="Mural Lighting")