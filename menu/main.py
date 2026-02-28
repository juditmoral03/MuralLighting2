from nicegui import ui, app
import os
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import json
import datetime
import uuid
import asyncio  # Required for sleep/wait times

# --- CONFIGURATION & ENVIRONMENT SETUP ---
IS_PRODUCTION = os.environ.get('RENDER') is not None
NODE_BASE_URL = "/app" if IS_PRODUCTION else "http://127.0.0.1:3006"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

menu_path = os.path.dirname(__file__) 
app.add_static_files('/menu', menu_path)

# --- LOGGING CONFIGURATION ---
LOG_FILE = "visit_log.json"
INTERACTIONS_FILE = "interactions.json"

def log_visitor(request: Request, session_id: str):
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0] if forwarded else (request.client.host if request.client else "Unknown")
    
    visit_data = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": client_ip,
        "session_id": session_id,
        "user_agent": request.headers.get("user-agent", "Unknown")
    }

    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f: logs = json.load(f)
        except: logs = []

    should_log = True
    if logs:
        last_visit = logs[-1]
        last_session = last_visit.get('session_id')
        same_user = (last_session and last_session == session_id) or (not last_session and last_visit['ip'] == client_ip)
        if same_user:
            last_time = datetime.datetime.strptime(last_visit['timestamp'], "%Y-%m-%d %H:%M:%S")
            now_time = datetime.datetime.strptime(visit_data['timestamp'], "%Y-%m-%d %H:%M:%S")
            if (now_time - last_time).total_seconds() < 5: should_log = False

    if should_log:
        logs.append(visit_data)
        with open(LOG_FILE, "w") as f: json.dump(logs, f, indent=4)
    return len(logs)

def log_interaction(request: Request, action: str, detail: str, session_id: str = "Unknown"):
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0] if forwarded else (request.client.host if request.client else "Unknown")
    event_data = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": client_ip,
        "session_id": session_id,
        "action": action,
        "detail": detail
    }
    events = []
    if os.path.exists(INTERACTIONS_FILE):
        try:
            with open(INTERACTIONS_FILE, "r") as f: events = json.load(f)
        except: events = []
    events.append(event_data)
    with open(INTERACTIONS_FILE, "w") as f: json.dump(events, f, indent=4)

# --- CONSTANTS ---
C1, C2, C3, C4 = "Hanging oil lamp", "Two table candles", "Two floor chandeliers", "Four floor chandeliers"
D1T1, D1T2, D1T3 = "Time: 10:00 am", "Time: 10:53 am", "Time: 12:53 pm" # Dec 25th
D2T1, D2T2, D2T3 = "Time: 10:00 am", "Time: 10:56 am", "Time: 13:56 pm" # Apr 1st
D3T1, D3T2, D3T3 = "Time: 10:00 am", "Time: 11:53 am", "Time: 13:53 pm" # Jun 6th
DEFAULT_IMAGE = "XII/Artificial/C1-pv2.exr"
DEFAULT_IMAGE2 = "XII/Artificial/C2-pv2.exr"

# --- MAIN PAGE ENTRY POINT ---

@ui.page('/')
async def main(request: Request):

    # --- 0. UNIQUE USER IDENTIFICATION ---
    if 'user_uid' not in app.storage.browser:
        app.storage.browser['user_uid'] = str(uuid.uuid4())
    session_id = app.storage.browser['user_uid']
    log_visitor(request, session_id)

    # --- NEW: SESSION ID DIALOG ---
    with ui.dialog() as session_dialog, ui.card().classes('w-[400px] max-w-[90vw] p-6 flex flex-col items-center gap-4'):
        ui.icon('badge', size='48px').classes('text-blue-500 mb-2')
        ui.label('Session Information').classes('text-xl font-bold text-gray-800')
        ui.label('Please copy your session ID number:').classes('text-sm text-gray-600 text-center')
        
        # Box with the ID and copy button
        with ui.row().classes('w-full items-center justify-between border-2 border-gray-200 p-2 rounded-lg bg-gray-50 no-wrap'):
            ui.label(session_id).classes('font-mono text-xs text-gray-700 break-all ml-2')
            
            # Function to copy and notify
            def copy_id():
                ui.clipboard.write(session_id)
                ui.notify('Session ID copied to clipboard!', color='positive', icon='check_circle')
                
            ui.button(icon='content_copy', on_click=copy_id).props('flat round color=primary').classes('ml-2')
            
        ui.button('Continue to App', on_click=session_dialog.close).classes('w-full mt-4').props('color=primary')

    # Automatically open the dialog on load
    ui.timer(0.1, session_dialog.open, once=True)
   


    # --- 1. SESSION STATE ---
    class SessionState:
        def __init__(self):
            self.hour = None
            self.day = None
            self.selected_left = None
            self.selected_right = None
            self.all_cards = {}
            self.iframe_container = None
            self.ignore_logs = False  # Flag to prevent logs when system updates state
            self.c_nat1 = self.c_nat2 = self.c_nat3 = None
            self.c_na1 = self.c_na2 = None
            self.c_all1 = self.c_all2 = self.c_all3 = self.c_all4 = self.c_all5 = self.c_all6 = None

    state = SessionState()

    # --- 1.5 TONE MAPPING STATE ---
    tm_state = {
        'algo': 'toneMappingReinhardBasic', 
        'target': 'both',
        'fix': False,      
        'exposure': 1.0,  
        'key': 0.18,      
        'white': 1.0,     
        'maxLum': 0.00005 
    }

    async def update_tm_js():
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

    # --- 2. HELPER FUNCTIONS ---
    def format_exr(image_name):
        if image_name.startswith('/menu/'): image_name = image_name[len('/menu/'):]
        parts = image_name.rsplit('/', 1)
        folder = parts[0].replace('+', '%2B')
        return f"XII/{folder}/{parts[1].rsplit('.', 1)[0]}.exr"
    
    def format_label_html(text, image_path):
        text_str = "<br>".join(str(t) for t in text) if isinstance(text, list) else str(text)
        day = None
        if image_path:
            if "D2" in image_path: day = "Apr 1st"
            elif "D3" in image_path: day = "Jun 6th"
            elif "D1" in image_path: day = "Dec 25th"
        return f"{day}<br><span>{text_str}</span>" if day else text_str

    def show_selected_images():
        def format_exr_inner(image_name):
            if image_name.startswith('/menu/'): image_name = image_name[len('/menu/'):]
            parts = image_name.rsplit('/', 1)
            folder = parts[0].replace('+', '%2B')
            return f"XII/{folder}/{parts[1].rsplit('.', 1)[0]}.exr"
        
        def infer_day(p): 
            if not p: return None
            if "D2" in p: return "Apr 1st"
            if "D3" in p: return "Jun 6th"
            if "D1" in p: return "Dec 25th"
            return None

        img1 = format_exr_inner(state.selected_left["image"]) if state.selected_left else DEFAULT_IMAGE
        img2 = format_exr_inner(state.selected_right["image"]) if state.selected_right else DEFAULT_IMAGE2
        
        lbl1_txt = "<br>".join(state.selected_left["text"]) if state.selected_left and isinstance(state.selected_left["text"], list) else (state.selected_left["text"] if state.selected_left else "Hanging oil lamp")
        lbl2_txt = "<br>".join(state.selected_right["text"]) if state.selected_right and isinstance(state.selected_right["text"], list) else (state.selected_right["text"] if state.selected_right else "Two table candles")
        
        d1, d2 = infer_day(state.selected_left["image"] if state.selected_left else None), infer_day(state.selected_right["image"] if state.selected_right else None)
        l1 = f"{d1}<br><span>{lbl1_txt}</span>" if d1 else lbl1_txt
        l2 = f"{d2}<br><span>{lbl2_txt}</span>" if d2 else lbl2_txt
        
        return f"""
        <div style="position: relative; width: 100%; height: 100%;">
            <iframe id="viewer-iframe" src="{NODE_BASE_URL}/index.html?img1={img1}&img2={img2}&v=2" 
                style="width:100%; height:100%; border:none; position: absolute; top:0; left:0; z-index:0;" allowfullscreen loading="lazy"></iframe>
            <div id="label-left" style="position: absolute; bottom: 60px; left: 25%; transform: translateX(-50%); font-size: 12px; font-weight: 500; color: #eee; text-align: center; text-shadow: 0 0 5px rgba(0,0,0,0.6); z-index: 2;">{l1}</div>
            <div id="label-right" style="position: absolute; bottom: 60px; left: 75%; transform: translateX(-50%); font-size: 12px; font-weight: 500; color: #eee; text-align: center; text-shadow: 0 0 5px rgba(0,0,0,0.6); z-index: 2;">{l2}</div>
        </div>
        """

    # --- UPDATE BUTTON VISIBILITY (LOGIC L & R) ---
    def update_all_cards_visibility():
        current_left = state.selected_left["image"] if state.selected_left else None
        current_right = state.selected_right["image"] if state.selected_right else None

        for image, pairs in state.all_cards.items():
            for pair in pairs:
                # 1. Update Left Button
                if image == current_left:
                    pair['L'].set_visibility(True)
                else:
                    pair['L'].set_visibility(False)
                
                # 2. Update Right Button
                if image == current_right:
                    pair['R'].set_visibility(True)
                else:
                    pair['R'].set_visibility(False)

    # --- CREATE CARD (2 BUTTONS) ---
    def create_card(image, text, classes):
        with ui.card().tight().classes(classes) as c:
            with ui.image(image) as img:
                
                # BUTTON L (Top Left)
                btn_l = ui.button('L', on_click=None).props('flat color=white').classes('absolute top-2 left-2 m-1 bg-white text-black font-bold text-[10px] flex items-center justify-center')
                btn_l.style('width: 16px !important; height: 16px !important; min-width: 0 !important; min-height: 0 !important; border-radius: 50% !important; font-size: 8px !important; padding: 0 !important;')
                btn_l.set_visibility(False)

                # BUTTON R (Top Right)
                btn_r = ui.button('R', on_click=None).props('flat color=white').classes('absolute top-2 right-2 m-1 bg-white text-black font-bold text-[10px] flex items-center justify-center')
                btn_r.style('width: 16px !important; height: 16px !important; min-width: 0 !important; min-height: 0 !important; border-radius: 50% !important; font-size: 8px !important; padding: 0 !important;')
                btn_r.set_visibility(False)
                
                if image not in state.all_cards: state.all_cards[image] = []
                # Store both as a dictionary pair
                state.all_cards[image].append({'L': btn_l, 'R': btn_r})
                
                # --- MODIFIED SELECTION LOGIC (WITH MUTE LOGS + RESPECT STATE) ---
                async def toggle_selection():
                    log_interaction(request, "Select Image", str(text), session_id)
                    selected_window = await ui.run_javascript('return localStorage.getItem("selectedWindow");')
                    
                    if not selected_window or selected_window == "none" or selected_window == "null": 
                        ui.notify("⚠️ Select a window first", color='orange')
                        return

                    # 1. Capture user preference
                    was_fixed = tm_state['fix']
                    # 2. Activate Mute
                    state.ignore_logs = True

                    # 3. Only unlock exposure if user had it locked (to recalculate)
                    if was_fixed:
                        tm_state['fix'] = False
                        await update_tm_js()

                    text_json = json.dumps(text)
                    exr_path = format_exr(image)
                    new_label_html = format_label_html(text, image)

                    if selected_window == "left":
                        state.selected_left = {"card": c, "image": image, "text": text}
                        await ui.run_javascript(f'localStorage.setItem("saved_L_img", "{image}");')
                        await ui.run_javascript(f'localStorage.setItem("saved_L_txt", \'{text_json}\');') 
                        update_all_cards_visibility()
                        js_img = f'var iframe = document.getElementById("viewer-iframe"); if(iframe) {{ iframe.contentWindow.postMessage({{ "type": "change_left", "path": "{exr_path}" }}, "*"); }}'
                        await ui.run_javascript(js_img)
                        await ui.run_javascript(f'document.getElementById("label-left").innerHTML = `{new_label_html}`;')
                    
                    elif selected_window == "right":
                        state.selected_right = {"card": c, "image": image, "text": text}
                        await ui.run_javascript(f'localStorage.setItem("saved_R_img", "{image}");')
                        await ui.run_javascript(f'localStorage.setItem("saved_R_txt", \'{text_json}\');')
                        update_all_cards_visibility()
                        js_img = f'var iframe = document.getElementById("viewer-iframe"); if(iframe) {{ iframe.contentWindow.postMessage({{ "type": "change_right", "path": "{exr_path}" }}, "*"); }}'
                        await ui.run_javascript(js_img)
                        await ui.run_javascript(f'document.getElementById("label-right").innerHTML = `{new_label_html}`;')

                    # 4. Wait
                    await asyncio.sleep(0.5)

                    # 5. Restore state only if it was enabled
                    if was_fixed:
                        tm_state['fix'] = True
                        await update_tm_js()

                    # 6. Reactivate logs
                    await asyncio.sleep(0.1)
                    state.ignore_logs = False

                img.on('click', toggle_selection)
            with ui.card_section():
                if isinstance(text, list):
                    for t in text: ui.markdown(t)
                else: ui.markdown(text)

    classes_card = "h-[20vh] w-[15vh]"

    # --- 3. REFRESH LOGIC ---
    def refresh_cards_natural():
        if not state.c_nat1: return
        gh = state.hour
        v_D2T1, v_D2T2, v_D2T3 = (gh=="10:00" or gh=="All" or not gh), (gh=="10:56" or gh=="All" or not gh), (gh=="13:56" or gh=="All" or not gh)
        v_D3T1, v_D3T2, v_D3T3 = (gh=="10:00" or gh=="All" or not gh), (gh=="11:53" or gh=="All" or not gh), (gh=="13:53" or gh=="All" or not gh)
        v_D1T1, v_D1T2, v_D1T3 = (gh=="10:00" or gh=="All" or not gh), (gh=="10:53" or gh=="All" or not gh), (gh=="12:53" or gh=="All" or not gh)
        
        if gh == "10:53": v_D2T1=v_D2T2=v_D2T3=v_D3T1=v_D3T2=v_D3T3=v_D1T1=v_D1T3=False
        if gh == "10:56": v_D2T1=v_D2T3=v_D3T1=v_D3T2=v_D3T3=v_D1T1=v_D1T2=v_D1T3=False
        
        lbl_style = "font-size: 1.6vh; font-weight: 400; margin-bottom: 2px; color: black;"
        show_nat1 = (state.day is None or state.day == "Apr 1st" or state.day == "All") and (v_D2T1 or v_D2T2 or v_D2T3)
        state.c_nat1.set_visibility(show_nat1); state.c_nat1.clear()
        if show_nat1:
            with state.c_nat1:
                ui.label("Apr 1st").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D2T1: create_card("/menu/Natural/D2T1-pv2.jpg", [D2T1], classes_card)
                    if v_D2T2: create_card("/menu/Natural/D2T2-pv2.jpg", [D2T2], classes_card)
                    if v_D2T3: create_card("/menu/Natural/D2T3-pv2.jpg", [D2T3], classes_card)
        
        show_nat2 = (state.day is None or state.day == "Jun 6th" or state.day == "All") and (v_D3T1 or v_D3T2 or v_D3T3)
        state.c_nat2.set_visibility(show_nat2); state.c_nat2.clear()
        if show_nat2:
            with state.c_nat2:
                ui.label("Jun 6th").style(lbl_style)
                with ui.row().classes('gap-2 items-start'):
                    if v_D3T1: create_card("/menu/Natural/D3T1-pv2.jpg", [D3T1], classes_card)
                    if v_D3T2: create_card("/menu/Natural/D3T2-pv2.jpg", [D3T2], classes_card)
                    if v_D3T3: create_card("/menu/Natural/D3T3-pv2.jpg", [D3T3], classes_card)
        
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
        if not state.c_na1: return
        gh = state.hour
        v_D1T3_C2 = v_D1T3_C5 = True; v_D2T3_C2 = v_D2T3_C5 = True
        
        if gh == "12:53": v_D2T3_C2 = v_D2T3_C5 = False
        elif gh == "13:56": v_D1T3_C2 = v_D1T3_C5 = False
        elif gh and gh != "All" and gh not in ["12:53", "13:56"]: v_D1T3_C2 = v_D1T3_C5 = v_D2T3_C2 = v_D2T3_C5 = False
        
        lbl_style = "font-size: 1.6vh; font-weight: 400; margin-bottom: 0.5vh; color: black;"
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
        if not state.c_all1: return
        gh = state.hour
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
        
        state.c_all4.clear()
        with state.c_all4:
             ui.label("Spacer").style(lbl_style + "visibility: hidden;")
             with ui.row().classes('gap-2 items-start'): 
                create_card("/menu/Artificial/C1-pv2.jpg", [C1], classes_card)
                create_card("/menu/Artificial/C2-pv2.jpg", [C2], classes_card)
                create_card("/menu/Artificial/C3-pv2.jpg", [C3], classes_card)
                create_card("/menu/Artificial/C4-pv2.jpg", [C4], classes_card)
                create_card("/menu/Artificial/C5-pv2.jpg", ["All artificial lighting"], classes_card)
        
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
        refresh_cards_natural()
        refresh_cards_natart()
        refresh_cards_all()

    # --- 4. HTML INJECTION ---
    ui.add_body_html("""
    <script>
    async function restoreSelectedWindow() {
        const container = document.getElementById('container');
        let saved = localStorage.getItem('selectedWindow');
        if (typeof updateSelectedWindowHighlight === "function" && saved && saved !== "none") updateSelectedWindowHighlight(saved);
        if (container) {
            container.addEventListener('click', async (e) => {
                const rect = container.getBoundingClientRect();
                let selectedWindow = ((e.clientX - rect.left) < rect.width / 2) ? 'left' : 'right';
                triggerLogAndSave(selectedWindow);
            });
        }
    }
    function triggerLogAndSave(value) {
        localStorage.setItem('selectedWindow', value);
        if (typeof updateSelectedWindowHighlight === "function") updateSelectedWindowHighlight(value);
        let btnId = (value === 'left') ? 'log-btn-left' : (value === 'right' ? 'log-btn-right' : 'log-btn-none');
        const btn = document.getElementById(btnId);
        if (btn) btn.click();
    }
    window.addEventListener('load', restoreSelectedWindow);
    window.addEventListener('message', function(event) {
        if (event.data && event.data.type === 'window_selected') triggerLogAndSave(event.data.value);
    });
    </script>
    """)
    ui.add_head_html('''
    <style>
    body, html { margin: 0; padding: 0; overflow: hidden; width: 100%; height: 100%; }
    .menu-row { width: 100%; margin: 0; padding: 0; background-color: white; }
    .dropdown-panel { position: absolute; top: 100%; left: 0; right: 0; height: auto; max-height: 85vh; background-color: white; z-index: 40; display: flex; flex-direction: column; align-items: stretch; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); padding-bottom: 5px; }
    .dropdown-panel .q-card { box-shadow: 0 2px 5px rgba(0,0,0,0.15) !important; border: 1px solid #e0e0e0; display: flex; flex-direction: column; padding: 0 !important; margin: 0 !important; transition: transform 0.2s ease, box-shadow 0.2s ease; }
    .dropdown-panel .q-card:hover { transform: translateY(-2px); box-shadow: 0 8px 15px rgba(0,0,0,0.2) !important; z-index: 10; }
    .dropdown-panel .q-card .q-img { height: 70%; width: 100%; object-fit: cover; }
    .dropdown-panel .q-card__section { height: 30%; display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important; }
    .dropdown-panel .q-card__section div, .dropdown-panel .q-card__section p, .dropdown-panel .q-card__section span { text-align: center !important; width: 100% !important; margin: 0 !important; line-height: 1.1 !important; font-size: 1.15vh !important; color: #333; }
    .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 200, 'GRAD' 0, 'opsz' 24 }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap" />
    ''')

    categories = ["Home", "Natural illumination", "Artificial illumination", "Natural + Artificial illumination", "All combinations"]
    menu_panels = {}

    with ui.dialog() as home_dialog, ui.card().classes('w-[600px] max-w-[90vw] p-0'):
        with ui.row().classes('w-full items-center justify-between p-4 bg-gray-100 border-b'):
            ui.label('About the Application').classes('text-lg font-bold text-gray-800')
            ui.icon('close').classes('cursor-pointer text-gray-500 hover:text-black hover:bg-gray-200 rounded-full p-1 transition').on('click', home_dialog.close)
        with ui.scroll_area().classes('h-[50vh] p-6'):
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
               - <span class="material-symbols-outlined" style="{icon_style}">sunny</span><span style="vertical-align: text-bottom;">+</span><span class="material-symbols-outlined" style="{icon_style}">lightbulb_2</span> **Combinations:** Mixture of natural and artificial light.
               - <span style=" font-size: 0.9rem;">ALL</span> **All Combinations:** All options in a single large panel.
            
            3. **Global Filters:**
               - <span class="material-symbols-outlined" style="{icon_style}">access_time</span> **Clock**: Filter by time.
               - <span class="material-symbols-outlined" style="{icon_style}">calendar_today</span> **Calendar**: Filter by date.
            
            4. **Tools (Left):**
               - <span class="material-symbols-outlined" style="{icon_style}">link</span> **Sync (Link):** Moves both cameras simultaneously if enabled.
               - <span class="material-symbols-outlined" style="{icon_style}">tune</span> **Tone Mapping:** Opens a dropdown menu where you can adjust image processing settings.
               - <span class="material-symbols-outlined" style="{icon_style}">difference</span> **Difference:** Visualizes the changes between the two images.
            """).classes('text-gray-700 leading-relaxed')
    #ui.timer(0.1, home_dialog.open, once=True)

    # --- 5. UI LAYOUT ---
    with ui.column().classes('absolute-full gap-0 no-wrap'):
        ui.button(on_click=lambda: log_interaction(request, "Select Window", "Left View", session_id)).props('id=log-btn-left').style('display: none')
        ui.button(on_click=lambda: log_interaction(request, "Select Window", "Right View", session_id)).props('id=log-btn-right').style('display: none')
        ui.button(on_click=lambda: log_interaction(request, "Select Window", "Deselected (None)", session_id)).props('id=log-btn-none').style('display: none')

        with ui.element('div').classes('w-full bg-white shadow-sm z-50 relative flex flex-col md:flex-row items-center px-2 md:px-6 py-1 md:py-0 h-auto md:h-[50px]'):
            
            # --- LEFT TOOLS ---
            with ui.row().classes('items-center justify-start md:mr-auto z-50'):
                # RESET BUTTON (UPDATED - DEFAULT CARDS)
                async def reset_app():
                    log_interaction(request, "Global Reset", "Clicked", session_id)
                    state.ignore_logs = True 
                    
                    state.hour = None
                    state.day = None
                    
                    # --- RESTORE DEFAULT SELECTION IN PYTHON STATE ---
                    default_menu_L = "/menu/Artificial/C1-pv2.jpg"
                    default_menu_R = "/menu/Artificial/C2-pv2.jpg"
                    state.selected_left = {"image": default_menu_L, "text": [C1]}
                    state.selected_right = {"image": default_menu_R, "text": [C2]}
                    
                    tm_state.update({'algo': 'toneMappingReinhardBasic', 'target': 'both', 'fix': False, 'exposure': 1.0, 'key': 0.18, 'white': 1.0, 'maxLum': 0.00005})
                    sync_state['active'] = True
                    
                    icon_sync.classes('text-black', remove='text-gray-300')
                    icon_hour.set_visibility(True); label_hour.set_visibility(False)
                    icon_day.set_visibility(True); label_day.set_visibility(False)
                    
                    # Clear Storage (EXCEPT selectedWindow)
                    await ui.run_javascript(f'''
                        localStorage.removeItem("global_hour"); 
                        localStorage.removeItem("global_day");
                        localStorage.removeItem("saved_L_img"); 
                        localStorage.removeItem("saved_L_txt"); 
                        localStorage.removeItem("saved_R_img"); 
                        localStorage.removeItem("saved_R_txt");
                        
                        var iframe = document.getElementById("viewer-iframe"); 
                        if(iframe) {{ 
                            iframe.contentWindow.postMessage({{ "type": "toggle_sync", "value": true }}, "*");
                            
                            // FORCE IMMEDIATE IMAGE LOAD
                            iframe.contentWindow.postMessage({{ "type": "change_left", "path": "{DEFAULT_IMAGE}" }}, "*");
                            iframe.contentWindow.postMessage({{ "type": "change_right", "path": "{DEFAULT_IMAGE2}" }}, "*");
                        }}
                    ''')
                    
                    # Force Visual Update of L/R Buttons
                    update_all_cards_visibility() 
                    refresh_all_views() 
                    state.iframe_container.content = show_selected_images() 
                    
                    # Fix Normalization
                    await update_tm_js() 
                    await asyncio.sleep(2.0)
                    tm_state['fix'] = True
                    await update_tm_js() 
                    
                    state.ignore_logs = False
                    ui.notify("Application Reset", color="grey")

                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    ui.icon('restart_alt', size="22px").classes('cursor-pointer text-black hover:text-gray-600 material-symbols-outlined transition-colors').on('click', reset_app)
                    with ui.tooltip('Reset Application'): pass

                # SYNC
                sync_state = {'active': True}
                async def toggle_sync():
                    sync_state['active'] = not sync_state['active']
                    log_interaction(request, "Tool Sync", "On" if sync_state['active'] else "Off", session_id)
                    icon_sync.classes('text-black' if sync_state['active'] else 'text-gray-300', remove='text-gray-300' if sync_state['active'] else 'text-black')
                    await ui.run_javascript(f'var iframe = document.getElementById("viewer-iframe"); if(iframe) {{ iframe.contentWindow.postMessage({{ "type": "toggle_sync", "value": {str(sync_state["active"]).lower()} }}, "*"); }}')
                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    icon_sync = ui.icon('link', size="22px").classes('cursor-pointer text-black hover:text-gray-600 material-symbols-outlined transition-colors').on('click', toggle_sync)
                    with ui.tooltip('Sync Views'): pass

                # TONE MAPPING
                def log_tm_selection(category, value): log_interaction(request, "Tone Mapping Tool", f"{category}: {value}", session_id)
                async def on_algo_change(e):
                    tm_state['algo'] = e.value; await update_tm_js(); log_tm_selection("Algorithm", e.value)

                # FUNCIO NOVA AMB ASYNC
                async def handle_switch_log(e):
                    await update_tm_js()
                    # NOMÉS LOGUEJAR SI NO ÉS SISTEMA
                    if not state.ignore_logs:
                        log_tm_selection("Fix Normalization", "On" if e.value else "Off")

                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    ui.icon('tune', size="22px").classes('cursor-pointer text-gray-600 hover:text-black material-symbols-outlined')
                    with ui.menu().props('auto-close="false" anchor="bottom middle" self="top middle"').classes('bg-white shadow-xl rounded-md p-4 z-50 w-64'):
                        ui.label("Tone Mapping").classes('text-xs font-bold text-gray-400 mb-2 uppercase')
                        ui.select(options={'both': 'Both Windows', 'window1': 'Window 1', 'window2': 'Window 2'}, value=tm_state['target'], label="Apply To") \
                            .bind_value(tm_state, 'target').on_value_change(lambda e: [update_tm_js(), log_tm_selection("Target", e.value)]).classes('w-full mb-2 text-sm')
                        ui.select(options={"toneMappingLinear": "Linear", "toneMappingReinhardBasic": "Reinhard Basic", "toneMappingReinhardExtended": "Reinhard Extended", "toneMappingLuminance": "Luminance"}, value=tm_state['algo'], label="Algorithm") \
                            .on_value_change(on_algo_change).classes('w-full mb-2 text-sm')
                        
                        with ui.column().classes('w-full p-0 m-0 gap-0').bind_visibility_from(tm_state, 'algo', backward=lambda x: x in ['toneMappingLinear', 'toneMappingReinhardBasic']):
                            ui.label("Exposure").classes('text-xs text-gray-500 mt-2')
                            with ui.row().classes('w-full items-center gap-2'):
                                ui.slider(min=0.1, max=10.0, step=0.1, value=tm_state['exposure']).bind_value(tm_state, 'exposure').on_value_change(update_tm_js).classes('col-grow')
                                ui.label().bind_text_from(tm_state, 'exposure', backward=lambda x: f"{x:.1f}").classes('text-xs w-8 text-right')
                        
                        with ui.column().classes('w-full p-0 m-0 gap-0').bind_visibility_from(tm_state, 'algo', backward=lambda x: x == 'toneMappingReinhardExtended'):
                            ui.label("Key").classes('text-xs text-gray-500 mt-2'); 
                            with ui.row().classes('w-full items-center gap-2'): ui.slider(min=0.0, max=1.0, step=0.01, value=tm_state['key']).bind_value(tm_state, 'key').on_value_change(update_tm_js).classes('col-grow')
                            ui.label("L White").classes('text-xs text-gray-500 mt-1')
                            with ui.row().classes('w-full items-center gap-2'): ui.slider(min=0.1, max=10.0, step=0.1, value=tm_state['white']).bind_value(tm_state, 'white').on_value_change(update_tm_js).classes('col-grow')

                        with ui.column().classes('w-full p-0 m-0 gap-0').bind_visibility_from(tm_state, 'algo', backward=lambda x: x == 'toneMappingLuminance'):
                            ui.label("Max Luminance").classes('text-xs text-gray-500 mt-2')
                            with ui.row().classes('w-full items-center gap-2'):
                                ui.slider(min=0.00001, max=0.001, step=0.00001, value=tm_state['maxLum']).bind_value(tm_state, 'maxLum').on_value_change(update_tm_js).classes('col-grow')
                                ui.label().bind_text_from(tm_state, 'maxLum', backward=lambda x: f"{x:.5f}".rstrip('0').rstrip('.')).classes('text-xs w-12 text-right')

                        ui.separator().classes('my-2')
                        # MODIFICAT PER USAR LA FUNCIO ASYNC AMB FILTRE DE LOG
                        ui.switch('Fix Normalization', value=tm_state['fix']).bind_value(tm_state, 'fix') \
                            .on_value_change(handle_switch_log).props('dense').classes('text-sm text-gray-700 w-full') 
                    with ui.tooltip('Tone Mapping'): pass
                
                # DIFFERENCE TOOL
                async def open_diff_js():
                    log_interaction(request, "Tool Difference", "Clicked", session_id)
                    await ui.run_javascript('var iframe = document.getElementById("viewer-iframe"); if(iframe) { iframe.contentWindow.postMessage({ "type": "open_diff" }, "*"); }')
                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    ui.icon('difference', size="22px").classes('cursor-pointer text-gray-600 hover:text-black material-symbols-outlined').on('click', open_diff_js)
                    with ui.tooltip('Image Difference'): pass

            # --- CENTER MENU ---
            active_panel = {'name': None}
            def show_panel(e, cat):
                current = active_panel['name']
                if current and current in menu_panels and current != cat: menu_panels[current].set_visibility(False)
                if cat != "Home":
                    if cat in menu_panels: menu_panels[cat].set_visibility(True); active_panel['name'] = cat
                else:
                    if current and current in menu_panels: menu_panels[current].set_visibility(False)
                    active_panel['name'] = None
            
            with ui.row().classes('w-full md:w-auto flex justify-center gap-8 md:absolute md:left-1/2 md:transform md:-translate-x-1/2 flex-wrap md:flex-nowrap'):
                for cat in categories:
                    if cat == "Home": 
                        ui.icon('info', size='24px').classes('cursor-pointer text-gray-700 hover:text-black hover:bg-gray-100 p-1 rounded transition material-symbols-outlined') \
                            .on('mouseover', lambda e, cat=cat: show_panel(e, cat)).on('click', lambda: [log_interaction(request, "Open Info", "Home Icon", session_id), home_dialog.open()]) 
                    elif cat == "Natural illumination": ui.icon('sunny', size='24px').classes('cursor-pointer text-gray-700 hover:text-black hover:bg-gray-100 p-1 rounded transition material-symbols-outlined').on('mouseover', lambda e, cat=cat: show_panel(e, cat))
                    elif cat == "Artificial illumination": ui.icon('lightbulb_2', size='24px').classes('cursor-pointer text-gray-700 hover:text-black hover:bg-gray-100 p-1 rounded transition material-symbols-outlined').on('mouseover', lambda e, cat=cat: show_panel(e, cat))
                    elif cat == "Natural + Artificial illumination":
                        with ui.row().classes('cursor-pointer hover:bg-gray-100 p-1 rounded transition items-center gap-1').on('mouseover', lambda e, cat=cat: show_panel(e, cat)):
                            ui.icon('sunny', size='24px').classes('material-symbols-outlined text-gray-700'); ui.label('+').style('font-size: 18px; font-weight: 300;'); ui.icon('lightbulb_2', size='24px').classes('material-symbols-outlined text-gray-700')
                    elif cat == "All combinations": ui.label('ALL').classes('cursor-pointer hover:bg-gray-100 px-2 py-1 rounded transition text-gray-700 font-light text-md').on('mouseover', lambda e, cat=cat: show_panel(e, cat))

            # --- RIGHT FILTERS ---
            with ui.row().classes('w-full md:w-auto flex justify-center md:justify-end gap-6 md:ml-auto items-center flex-nowrap mt-2 md:mt-0'):
                # HOUR
                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    def toggle_hour_menu(): hour_menu.toggle()
                    icon_hour = ui.icon('access_time', size="22px").classes('cursor-pointer text-gray-600 hover:text-black material-symbols-outlined').on('click', toggle_hour_menu)
                    label_hour = ui.label("").classes('text-sm text-black cursor-pointer hover:text-black whitespace-nowrap').on('click', toggle_hour_menu); label_hour.set_visibility(False)
                    with ui.menu().props('auto-close="false" anchor="bottom middle" self="top middle"').classes('bg-white shadow-xl rounded-md p-2 z-50 w-40') as hour_menu:
                        ui.label("Global Hour").classes('text-xs font-bold text-gray-400 px-2 py-1 uppercase'); ui.separator().classes('mb-1')
                        def set_global_hour_fn(h):
                            log_interaction(request, "Filter Hour", h, session_id); state.hour = h; ui.run_javascript(f'localStorage.setItem("global_hour", "{h}")')
                            if h == "All": icon_hour.set_visibility(True); label_hour.set_visibility(False)
                            else: icon_hour.set_visibility(False); label_hour.set_text(h); label_hour.set_visibility(True)
                            refresh_all_views()
                        for h in ["All", "10:00", "10:53", "10:56", "11:53", "12:53", "13:53", "13:56"]: ui.menu_item(h if h=="All" else (h+" am" if int(h[:2])<12 else h+" pm"), lambda h=h: set_global_hour_fn(h))
                
                # DAY
                with ui.element('div').classes('relative flex items-center justify-center w-10'):
                    def toggle_day_menu(): day_menu.toggle()
                    icon_day = ui.icon('calendar_today', size="22px").classes('cursor-pointer text-gray-600 hover:text-black material-symbols-outlined').on('click', toggle_day_menu)
                    label_day = ui.label("").classes('text-sm text-black cursor-pointer hover:text-black whitespace-nowrap').on('click', toggle_day_menu); label_day.set_visibility(False)
                    with ui.menu().props('auto-close="false" anchor="bottom middle" self="top middle"').classes('bg-white shadow-xl rounded-md p-2 z-50 w-40') as day_menu:
                        ui.label("Global Day").classes('text-xs font-bold text-gray-400 px-2 py-1 uppercase'); ui.separator().classes('mb-1')
                        def set_global_day_fn(d):
                            log_interaction(request, "Filter Day", d, session_id); state.day = d; ui.run_javascript(f'localStorage.setItem("global_day", "{d}")')
                            if d == "All": icon_day.set_visibility(True); label_day.set_visibility(False)
                            else: icon_day.set_visibility(False); label_day.set_text(d); label_day.set_visibility(True)
                            refresh_all_views()
                        for d in ["All", "Apr 1st", "Jun 6th", "Dec 25th"]: ui.menu_item(d, lambda d=d: set_global_day_fn(d))

                # RESTORE LOGIC
                async def restore_globals():
                    g_hour = await ui.run_javascript('return localStorage.getItem("global_hour")')
                    g_day = await ui.run_javascript('return localStorage.getItem("global_day")')
                    if g_hour and g_hour != "All" and g_hour != "null": state.hour = g_hour; icon_hour.set_visibility(False); label_hour.set_text(g_hour); label_hour.set_visibility(True)
                    if g_day and g_day != "All" and g_day != "null": state.day = g_day; icon_day.set_visibility(False); label_day.set_text(g_day); label_day.set_visibility(True)
                    refresh_all_views()
                ui.timer(0.1, restore_globals, once=True)

                async def restore_session_images():
                    l_img = await ui.run_javascript('return localStorage.getItem("saved_L_img");')
                    l_txt = None; l_txt_raw = await ui.run_javascript('return localStorage.getItem("saved_L_txt");')
                    if l_txt_raw and l_txt_raw != "null": 
                        try: l_txt = json.loads(l_txt_raw)
                        except: pass
                    
                    # --- FIXED: SET DEFAULT IF NULL ---
                    if l_img and l_img != "null": 
                        state.selected_left = {"card": None, "image": l_img, "text": l_txt if l_txt else "Loading..."}
                    else:
                        state.selected_left = {"card": None, "image": "/menu/Artificial/C1-pv2.jpg", "text": [C1]}
                    
                    r_img = await ui.run_javascript('return localStorage.getItem("saved_R_img");')
                    r_txt = None; r_txt_raw = await ui.run_javascript('return localStorage.getItem("saved_R_txt");')
                    if r_txt_raw and r_txt_raw != "null": 
                        try: r_txt = json.loads(r_txt_raw)
                        except: pass
                    
                    # --- FIXED: SET DEFAULT IF NULL ---
                    if r_img and r_img != "null": 
                        state.selected_right = {"card": None, "image": r_img, "text": r_txt if r_txt else "Loading..."}
                    else:
                        state.selected_right = {"card": None, "image": "/menu/Artificial/C2-pv2.jpg", "text": [C2]}

                    # Always run update now that defaults are set
                    update_all_cards_visibility()
                    
                    # Only update iframe if we restored something custom, otherwise defaults load automatically
                    if (l_img and l_img != "null") or (r_img and r_img != "null"):
                        state.iframe_container.content = show_selected_images()

                ui.timer(0.2, restore_session_images, once=True)

                # --- INIT SEQUENCE (Wait then Fix) ---
                async def init_sequence():
                    state.ignore_logs = True # Silenciar inicialment
                    await update_tm_js() 
                    await asyncio.sleep(2.0)
                    tm_state['fix'] = True
                    await update_tm_js()
                    # Mantenir mute una mica més per seguretat
                    await asyncio.sleep(0.1)
                    state.ignore_logs = False # Reactivar logs
                ui.timer(0.1, init_sequence, once=True)

            # --- DROPDOWNS ---
            def hide_panel(panel_key):
                if panel_key in menu_panels: menu_panels[panel_key].set_visibility(False)
                if active_panel['name'] == panel_key: active_panel['name'] = None

            # 1. Natural
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["Natural illumination"] = panel; panel.on('mouseleave', lambda: hide_panel("Natural illumination"))
                with ui.row().classes('w-full overflow-x-auto no-scrollbar gap-[3vh]').style('padding-left: 5vh; white-space: nowrap; padding-top: 1.5vh; padding-bottom: 1.5vh;'):
                    with ui.row().classes('justify-start gap-[3vh] items-start flex-nowrap').style('display: inline-flex;'):
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_nat1: pass
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_nat2: pass
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_nat3: pass
            
            # 2. Artificial
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["Artificial illumination"] = panel; panel.on('mouseleave', lambda: hide_panel("Artificial illumination"))
                with ui.row().classes('w-full overflow-x-auto no-scrollbar').style('padding-left: 5vh; white-space: nowrap; padding-top: 1.5vh; padding-bottom: 1.5vh;'):
                    with ui.row().classes('justify-start gap-2 items-start flex-nowrap').style('display: inline-flex;'):
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start; margin-left: 0px;'):
                            with ui.row().classes('gap-2 items-start'):
                                create_card("/menu/Artificial/C1-pv2.jpg", [C1], classes_card); create_card("/menu/Artificial/C2-pv2.jpg", [C2], classes_card)
                                create_card("/menu/Artificial/C3-pv2.jpg", [C3], classes_card); create_card("/menu/Artificial/C4-pv2.jpg", [C4], classes_card)
                                create_card("/menu/Artificial/C5-pv2.jpg", ["All artificial lighting"], classes_card)
            
            # 3. Nat + Art
            with ui.column().classes('dropdown-panel') as panel:
                panel.set_visibility(False); menu_panels["Natural + Artificial illumination"] = panel; panel.on('mouseleave', lambda: hide_panel("Natural + Artificial illumination"))
                with ui.row().classes('w-full overflow-x-auto no-scrollbar gap-[3vh]').style('padding-left: 5vh; white-space: nowrap; padding-top: 1.5vh; padding-bottom: 1.5vh;'):
                    with ui.row().classes('justify-start gap-[3vh] items-start flex-nowrap').style('display: inline-flex;'):
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_na1: pass
                        with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start;') as state.c_na2: pass

            # 4. All
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

        state.iframe_container = ui.html(show_selected_images(), sanitize=False).classes('w-full flex-grow').style('border: none; margin: 0; padding: 0;').props('id=container')

# --- STATS PAGE ---
@ui.page('/stats')
def stats_page():
    # 1. Load all interactions grouped by session_id
    interactions_by_session = {}
    if os.path.exists(INTERACTIONS_FILE):
        try:
            with open(INTERACTIONS_FILE, "r") as f: raw_events = json.load(f)
            from collections import defaultdict
            temp_data = defaultdict(list)
            for e in raw_events: 
                temp_data[e.get('session_id', 'Unknown')].append(e)
            interactions_by_session = temp_data
        except: pass

    def reset_stats():
        if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
        if os.path.exists(INTERACTIONS_FILE): os.remove(INTERACTIONS_FILE)
        ui.notify('🧹 All data has been cleared.', color='positive')
        ui.timer(1.0, lambda: ui.open('/stats'), once=True)

    with ui.row().classes('w-full justify-between items-center mb-6'):
        ui.label('User Analytics (By Session)').classes('text-2xl font-bold')
        ui.button('Reset Data', on_click=reset_stats, icon='delete_forever').props('color=red outline')
    
    ui.label('Click on a Session ID to see every single interaction from that device.').classes('text-sm text-gray-500 mb-2')

    main_table = None 
    session_summary = {}

    # 2. Load general visits to build the main table (No IP tracking)
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f: visit_data = json.load(f)
        
        for visit in visit_data:
            sid = visit.get('session_id', 'Unknown')
            ts = visit.get('timestamp', '-')
            
            if sid not in session_summary: 
                session_summary[sid] = {'count': 0, 'last_seen': ts}
            
            session_summary[sid]['count'] += 1
            session_summary[sid]['last_seen'] = ts

        summary_rows = [
            {'session_id': k, 'short_id': k[:8] + '...' if len(k)>8 else k, 'count': v['count'], 'last_seen': v['last_seen']} 
            for k, v in session_summary.items()
        ]
        summary_rows.sort(key=lambda x: x['last_seen'], reverse=True) # Sort by most recent
        
        main_table = ui.table(columns=[
            {'name': 'short_id', 'label': 'Session ID', 'field': 'short_id', 'align': 'left', 'classes': 'font-bold text-blue-900'},
            {'name': 'count', 'label': 'Total Visits', 'field': 'count', 'align': 'center', 'sortable': True},
            {'name': 'last_seen', 'label': 'Last Seen', 'field': 'last_seen', 'align': 'right', 'sortable': True}
        ], rows=summary_rows, row_key='session_id', pagination=10).classes('w-full cursor-pointer hover:bg-gray-50 mb-8')
    else: 
        ui.label("No visit data found.").classes('text-gray-500 italic p-2')

    details_container = ui.column().classes('w-full transition-all')

    # 3. Show grouped step-by-step details (No IP tracking)
    def show_session_details(e):
        details_container.clear()
        
        # Safe extraction of the 'session_id' from the row click event arguments
        row_data = None
        for arg in e.args:
            if isinstance(arg, dict) and 'session_id' in arg:
                row_data = arg
                break
                
        if not row_data:
            ui.notify(f"Debug Info: {e.args}", color="negative", timeout=5000)
            return
            
        selected_sid = row_data['session_id']
        
        with details_container:
            ui.separator().classes('mb-4')
            with ui.card().classes('w-full border-l-4 border-blue-500 shadow-lg bg-gray-50 p-4'):
                with ui.row().classes('items-center justify-between w-full mb-2'):
                    ui.label(f"Interaction Log: {selected_sid}").classes('text-xl font-bold text-gray-800')
                    ui.button('Close', on_click=details_container.clear, icon='close').props('flat color=red dense')

                events = interactions_by_session.get(selected_sid, [])
                stats = session_summary.get(selected_sid, {'count': 0, 'last_seen': 'N/A'})
                
                # The IP address was intentionally removed from this label for privacy
                ui.label(f"Total Visits: {stats['count']} | Last Seen: {stats['last_seen']}").classes('text-sm text-gray-600 mb-4')

                if not events: 
                    ui.label("No specific clicks or interactions were recorded for this session yet.").classes('text-orange-600 italic')
                else:
                    # Group identical events and count their occurrences
                    aggregated_events = {}
                    for evt in events:
                        action = evt.get('action', 'Unknown')
                        detail = evt.get('detail', '-')
                        ts = evt.get('timestamp', '-')
                        
                        key = (action, detail)
                        if key not in aggregated_events:
                            aggregated_events[key] = {'count': 0, 'last_timestamp': ts}
                        
                        aggregated_events[key]['count'] += 1
                        
                        # Update to the most recent timestamp for this specific action
                        if ts > aggregated_events[key]['last_timestamp']:
                            aggregated_events[key]['last_timestamp'] = ts
                    
                    # Convert the aggregated dictionary back into a list format for the UI table
                    rows = [
                        {
                            "action": act,
                            "detail": det,
                            "count": data['count'],
                            "last_timestamp": data['last_timestamp']
                        } for (act, det), data in aggregated_events.items()
                    ]
                    
                    # Sort by the most recently performed action first
                    rows.sort(key=lambda x: x['last_timestamp'], reverse=True)
                    
                    ui.table(columns=[
                        {'name': 'action', 'label': 'Action', 'field': 'action', 'align': 'left', 'sortable': True}, 
                        {'name': 'detail', 'label': 'Detail (Selected item)', 'field': 'detail', 'align': 'left', 'sortable': True},
                        {'name': 'count', 'label': 'Times Clicked', 'field': 'count', 'align': 'center', 'sortable': True},
                        {'name': 'last_timestamp', 'label': 'Last Time', 'field': 'last_timestamp', 'align': 'right', 'sortable': True}
                    ], rows=rows, pagination=15).classes('w-full bg-white')
                    
        # Scroll smoothly to the bottom to display the newly rendered interaction table
        ui.run_javascript('window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });')

    if main_table: 
        main_table.on('rowClick', show_session_details)

ui.run(title="Mural Lighting", storage_secret='secret_key_change_this_to_something_random')