from nicegui import ui, app
import os,json
from fastapi import Request

from nicegui import app
from fastapi import Request

from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

"""def load_selected():
    if os.path.exists("selected.json"):
        with open("selected.json") as f:
            return json.load(f).get("selected")
    return None

def save_selected(value):
    with open("selected.json", "w") as f:
        json.dump({"selected": value}, f)"""

selected_window = None #load_selected()

@app.post('/set_selected_window')
async def set_selected_window(request: Request):
    global selected_window
    data = await request.json()
    selected_window = data.get('selected') or "none"
    #save_selected(selected_window)
    return {'status': 'ok', 'selected': selected_window}


@app.get('/get_selected_window')
async def get_selected_window():
    return {'selected': selected_window or "none"}  


menu_path = os.path.dirname(__file__) 
app.add_static_files('/menu', menu_path)

selected_cards = []
all_cards = {}
iframe_container = None
visible_D2T1_natural = True
visible_D2T2_natural = True
visible_D2T3_natural = True
visible_D3T1_natural = True
visible_D3T2_natural = True
visible_D3T3_natural = True
visible_D1T1_natural = True
visible_D1T2_natural = True
visible_D1T3_natural = True

visible_D1T3_C2_natart = True
visible_D1T3_C5_natart = True
visible_D2T3_C2_natart = True
visible_D2T3_C5_natart = True

visible_D2T1_all = True
visible_D2T2_all = True
visible_D2T3_all = True
visible_D3T1_all = True
visible_D3T2_all = True
visible_D3T3_all = True
visible_D1T1_all = True
visible_D1T2_all = True
visible_D1T3_all = True

visible_D1T3_C2_all = True
visible_D1T3_C5_all = True
visible_D2T3_C2_all = True
visible_D2T3_C5_all = True


visible_C1_all = True
visible_C2_all = True
visible_C3_all = True
visible_C4_all = True
visible_C5_all = True


natural_hour= None
natural_day= None

natart_hour= None
natart_day= None

all_hour= None
all_day= None


DEFAULT_IMAGE = "XII/Artificial/C1-pv2.exr"
DEFAULT_IMAGE2 = "XII/Artificial/C2-pv2.exr"


selected_left = None
selected_right = None
# Helper functions

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
        if not image_path:
            return None
        if "D2" in image_path:
            return "Apr 1st"
        elif "D3" in image_path:
            return "Jun 6th"
        elif "D1" in image_path:
            return "Dec 25th"
        return None

    
    img1 = format_exr(selected_left["image"]) if selected_left else DEFAULT_IMAGE
    img2 = format_exr(selected_right["image"]) if selected_right else DEFAULT_IMAGE2

    label1_main = format_label_text(selected_left["text"]) if selected_left else "Hanging oil lamp"
    label2_main = format_label_text(selected_right["text"]) if selected_right else "Two table candles"

 
    day1 = infer_day_from_image(selected_left["image"]) if selected_left else None
    day2 = infer_day_from_image(selected_right["image"]) if selected_right else None

 
    label1 = f"{day1}<br><span>{label1_main}</span>" if day1 else label1_main
    label2 = f"{day2}<br><span>{label2_main}</span>" if day2 else label2_main

 
    url = f"http://127.0.0.1:3006/index.html?img1={img1}&img2={img2}"

   
    html = f"""
    <div style="position: relative; width: 100%; height: 100%;">
        <iframe 
            src="{url}" 
            style="width:100%; height:100%; border:none; position: absolute; top:0; left:0; z-index:0;"
            allowfullscreen
            loading="lazy">
        </iframe>

        <!-- Labels -->
        <div style="
            position: absolute;
            bottom: 60px;
            left: 25%;
            transform: translateX(-50%);
            font-size: 12px;
            font-weight: 500;
            color: #eee;
            text-align: center;
            text-shadow: 0 0 5px rgba(0,0,0,0.6);
            z-index: 2;
        ">{label1}</div>

        <div style="
            position: absolute;
            bottom: 60px;
            left: 75%;
            transform: translateX(-50%);
            font-size: 12px;
            font-weight: 500;
            color: #eee;
            text-align: center;
            text-shadow: 0 0 5px rgba(0,0,0,0.6);
            z-index: 2;
        ">{label2}</div>
    </div>
    """
    return html




def update_all_cards_visibility():
    selected_images = []
    if selected_left:
        selected_images.append(selected_left["image"])
    if selected_right:
        selected_images.append(selected_right["image"])

    for image, buttons in all_cards.items():
        for button in buttons:
            button.set_visibility(False)
            button.props('flat fab')  

            if image == (selected_left["image"] if selected_left else None):
                button.set_visibility(True)
                button.props('color=white')
                button.classes('absolute top-0 right-0 m-1 bg-white text-black font-bold text-[15px] flex items-center justify-center')
                button._text = "L"

            elif image == (selected_right["image"] if selected_right else None):
                button.set_visibility(True)
                button.props('color=white')
                button.classes('absolute top-0 right-0 m-1 bg-white text-black font-bold text-[15px] flex items-center justify-center')
                button._text = "R"



def card(image, text, classes, max_selected=2):
    with ui.card().tight().classes(classes) as c:
        with ui.image(image) as img:
        
            button = ui.button('', on_click=None).props('flat color=white').classes('absolute top-2 right-2 m-1 bg-white text-black font-bold text-[15px] flex items-center justify-center')
            button.set_visibility(False)
            button.style('''
                width: 22px !important;
                height: 22px !important;
                min-width: 0 !important;
                min-height: 0 !important;
                border-radius: 50% !important;
                font-size: 10px !important;
                padding: 0 !important;
            ''')


            if image not in all_cards:
                all_cards[image] = []
            all_cards[image].append(button)

            def toggle_selection():
                global selected_left, selected_right, iframe_container, selected_window

                
                if not selected_window:
                    ui.notify("⚠️ Select a window", color='orange')
                    return

               
                if selected_window == "left":
                    selected_left = {"card": c, "image": image, "text": text}
                    update_all_cards_visibility()
                    if iframe_container:
                        iframe_container.content = show_selected_images()
                    return

                
                if selected_window == "right":
                    selected_right = {"card": c, "image": image, "text": text}
                    update_all_cards_visibility()
                    if iframe_container:
                        iframe_container.content = show_selected_images()
                    return

            img.on('click', toggle_selection)

        with ui.card_section():
            if isinstance(text, list):
                for t in text:
                    ui.markdown(t)
            else:
                ui.markdown(text)





# Category data
NATURAL = "**Natural illumination**: "
NAT_NONE = "**Natural illumination**: no"
ARTIFICIAL = "**Artificial illumination**: "
ART_NONE = "**Artificial illumination**: no"
C1 = "Hanging oil lamp"
C2 = "Two table candles"
C3 = "Two floor chandeliers"
C4 = "Four floor chandeliers"

D1 = "Dec 25th"
D2 = "Apr 1st"
D3 = "Jun 6th"
DD1 = f"Date: {D1}"
DD2 = f"Date: {D2}"   
DD3 = f"Date: {D3}"
D1T1 = "Time: 10:00 am"
D1T2 = "Time: 10:53 am"
D1T3 = "Time: 12:53 pm"
D2T1 = "Time: 10:00 am"
D2T2 = "Time: 10:56 am"
D2T3 = "Time: 13:56 pm"
D3T1 = "Time: 10:00 am"
D3T2 = "Time: 11:53 am"
D3T3 = "Time: 13:53 pm"

@ui.page('/')


def main():
    global iframe_container
    selected_cards.clear()

    categories = ["Inici", "Natural illumination", "Artificial illumination", "Natural + Artificial illumination", "All combinations"]
    menu_panels = {}


    ui.add_body_html("""
<script>

async function restoreSelectedWindow() {
    const container = document.getElementById('container');
    if (!container) return;

    let saved = localStorage.getItem('selectedWindow');

    if (saved) {
    
        updateSelectedWindowHighlight(saved);
        await fetch('/set_selected_window', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({selected: saved})
        });
    } else {
    
        await fetch('/set_selected_window', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({selected: null})
        });
    }


    container.addEventListener('click', async (e) => {
        const rect = container.getBoundingClientRect();
        const x = e.clientX - rect.left;
        let selectedWindow = (x < rect.width / 2) ? 'left' : 'right';

        localStorage.setItem('selectedWindow', selectedWindow);
        updateSelectedWindowHighlight(selectedWindow);

        await fetch('/set_selected_window', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({selected: selectedWindow})
        });

       
    });
}


window.addEventListener('load', restoreSelectedWindow);
</script>

""")


    
     

    ui.add_head_html('''
<style>
body, html {
    margin: 0;
    padding: 0;
    overflow-x: hidden;
}

.menu-row {
    width: 100%;
    margin: 0;
    padding: 0;
    display: flex;
    justify-content: center;
    background-color: white;
}
                     



.dropdown-panel {
    position: absolute;
    top: 70px;
    left: 0;
    right: 0;
    height: 46vh;
    background-color: white;
    z-index: 50;
    display: flex;
    flex-direction: column; 
    align-items: stretch;
}


.dropdown-panel .controls {
    flex-shrink: 0; 
    padding: 0 40px;
    margin-top: 5px;
    display: flex;
    justify-content: flex-end;
    gap: 1.5rem;
    align-items: center;
}


.dropdown-panel .cards-wrapper {
    overflow-x: auto;
    overflow-y: hidden;
    white-space: nowrap;
    display: flex;
    gap: 2.5rem;
    padding: 10px;
    flex-shrink: 0; 
    padding-left:50px;
}

/* Fixed size for all cards */
.dropdown-panel .q-card {
    transform: scale(0.65); 
    margin: -30px;         
    display: flex;
    flex-direction: column;
    vertical-align: top;
}
        

/* First thistle with more space on the left */
.dropdown-panel .q-card:first-child {
    margin-left: 20px;
}

/* Set the size of the image inside the card */
.dropdown-panel .q-card .q-img {
    width: 100%;       
    height: 180px;     
    object-fit: cover; 
}

/* Compact text below */
.dropdown-panel .q-card__section {
    
    font-size: 1rem;
    line-height: 1rem;
    text-align: center;
    justify-content:center;
    
}
                              

.material-symbols-outlined {
  font-variation-settings:
  'FILL' 0,
  'wght' 200,
  'GRAD' 0,
  'opsz' 24
}
                     




                    
</style>
                     


''')



    ui.add_head_html('''
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap" />
''')



    with ui.row().classes('menu-row overflow-x-auto no-scrollbar flex-nowrap').style('white-space: nowrap; justify-content: center; gap: 2rem; padding: 0 20px;'):
        active_panel = {'name': None}

        def show_panel(e, cat):
            # hide all panels
            for name, p in menu_panels.items():
                p.set_visibility(False)
            # show only what is relevant
            if cat != "Inici":
                menu_panels[cat].set_visibility(True)
                active_panel['name'] = cat

        for cat in categories:
            if cat == "Inici":
                
                ui.icon('home', size='28px')\
                    .classes('cursor-pointer px-3 py-2 rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')\
                    .on('mouseover', lambda e, cat=cat: show_panel(e, cat))
            elif cat == "Natural illumination":
               
                ui.icon('sunny', size='28px')\
                    .classes('cursor-pointer px-3 py-2 rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')\
                    .on('mouseover', lambda e, cat=cat: show_panel(e, cat))
            elif cat == "Artificial illumination":
                
                ui.icon('lightbulb_2', size='28px')\
                    .classes('cursor-pointer px-3 py-2 rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')\
                    .on('mouseover', lambda e, cat=cat: show_panel(e, cat))
            elif cat == "Natural + Artificial illumination":
                
                with ui.row().classes(
                    'cursor-pointer px-2 py-2 rounded hover:bg-gray-100 transition flex-shrink-0'
                ).style('gap: 4px;').on('mouseover', lambda e, cat=cat: show_panel(e, cat)):
                    ui.icon('sunny', size='28px').classes('material-symbols-outlined')
                    ui.label('+').style('font-size: 24px; font-weight: 300;')
                    ui.icon('lightbulb_2', size='28px').classes('material-symbols-outlined')

            elif cat == "All combinations":
              
                ui.label('ALL')\
                    .classes('cursor-pointer px-3 py-2 rounded hover:bg-gray-100 transition flex-shrink-0 items-center')\
                    .style('font-size: 18px;font-weight: 300;')\
                    .on('mouseover', lambda e, cat=cat: show_panel(e, cat))




    # FOLDABLE PANEL
    for cat in categories:
        with ui.column().classes('dropdown-panel') as panel:
            panel.set_visibility(False)
            menu_panels[cat] = panel

            # When it leaves the panel, we hide it
            panel.on('mouseleave', lambda e, cat=cat: menu_panels[cat].set_visibility(False))



   # Function to refresh Natural illumination cards 
    def refresh_cards_natural():
        
       #  We delete old content
        cards_container_natural1.clear()
        cards_container_natural2.clear()
        cards_container_natural3.clear()

       #  Update visibility based on time
        if natural_hour == "10:00":
            visible_D2T1_natural = True
            visible_D2T2_natural = False
            visible_D2T3_natural = False
            visible_D3T1_natural = True
            visible_D3T2_natural = False
            visible_D3T3_natural = False
            visible_D1T1_natural = True
            visible_D1T2_natural = False
            visible_D1T3_natural = False
        elif natural_hour == "10:53":
            visible_D2T1_natural = False
            visible_D2T2_natural = False
            visible_D2T3_natural = False
            visible_D3T1_natural = False
            visible_D3T2_natural = False
            visible_D3T3_natural = False
            visible_D1T1_natural = False
            visible_D1T2_natural = True
            visible_D1T3_natural = False
        elif natural_hour == "10:56":
            visible_D2T1_natural = False
            visible_D2T2_natural = True
            visible_D2T3_natural = False
            visible_D3T1_natural = False
            visible_D3T2_natural = False
            visible_D3T3_natural = False
            visible_D1T1_natural = False
            visible_D1T2_natural = False
            visible_D1T3_natural = False
        elif natural_hour == "11:53":
            visible_D2T1_natural = False
            visible_D2T2_natural = False
            visible_D2T3_natural = False
            visible_D3T1_natural = False
            visible_D3T2_natural = True
            visible_D3T3_natural = False
            visible_D1T1_natural = False
            visible_D1T2_natural = False
            visible_D1T3_natural = False
        elif natural_hour == "12:53":
            visible_D2T1_natural = False
            visible_D2T2_natural = False
            visible_D2T3_natural = False
            visible_D3T1_natural = False
            visible_D3T2_natural = False
            visible_D3T3_natural = False
            visible_D1T1_natural = False
            visible_D1T2_natural = False
            visible_D1T3_natural = True
        elif natural_hour == "13:53":
            visible_D2T1_natural = False
            visible_D2T2_natural = False
            visible_D2T3_natural = False
            visible_D3T1_natural = False
            visible_D3T2_natural = False
            visible_D3T3_natural = True
            visible_D1T1_natural = False
            visible_D1T2_natural = False
            visible_D1T3_natural = False
        elif natural_hour == "13:56":
            visible_D2T1_natural = False
            visible_D2T2_natural = False
            visible_D2T3_natural = True
            visible_D3T1_natural = False
            visible_D3T2_natural = False
            visible_D3T3_natural = False
            visible_D1T1_natural = False
            visible_D1T2_natural = False
            visible_D1T3_natural = False
        else:
            visible_D2T1_natural = True
            visible_D2T2_natural = True
            visible_D2T3_natural = True
            visible_D3T1_natural = True
            visible_D3T2_natural = True
            visible_D3T3_natural = True
            visible_D1T1_natural = True
            visible_D1T2_natural = True
            visible_D1T3_natural = True


       # First column: Apr 1st
        if (visible_D2T1_natural or visible_D2T2_natural or visible_D2T3_natural) and \
        (natural_day is None or natural_day == "Apr 1st" or natural_day == "All"):
            with cards_container_natural1:
                ui.label("Apr 1st").classes('text-sm').style('margin-bottom: 5px; line-height: 1;')
                with ui.row().classes('gap-2 items-start').style('margin-top: -18px; margin-left: -45px; transform-origin: top left;'):
                    if visible_D2T1_natural:
                        card("/menu/natural/D2T1-pv2.jpg", [D2T1], classes)
                    if visible_D2T2_natural:
                        card("/menu/natural/D2T2-pv2.jpg", [D2T2], classes)
                    if visible_D2T3_natural:
                        card("/menu/natural/D2T3-pv2.jpg", [D2T3], classes)


        # Second column: Jun 6th 
        if (visible_D3T1_natural or visible_D3T2_natural or visible_D3T3_natural) and \
        (natural_day is None or natural_day == "Jun 6th" or natural_day == "All"):
            with cards_container_natural2:
                ui.label("Jun 6th").classes('text-sm').style('margin-bottom: 5px; line-height: 1;')
                with ui.row().classes('gap-2 items-start').style('margin-top: -18px; margin-left: -45px; transform-origin: top left;'):
                    if visible_D3T1_natural:
                        card("/menu/natural/D3T1-pv2.jpg", [D3T1], classes)
                    if visible_D3T2_natural:
                        card("/menu/natural/D3T2-pv2.jpg", [D3T2], classes)
                    if visible_D3T3_natural:
                        card("/menu/natural/D3T3-pv2.jpg", [D3T3], classes)

       # Third column: Dec 25th 
        if (visible_D1T1_natural or visible_D1T2_natural or visible_D1T3_natural)and \
        (natural_day is None or natural_day == "Dec 25th" or natural_day == "All"):
            with cards_container_natural3:
                ui.label("Dec 25th").classes('text-sm').style('margin-bottom: 5px; line-height: 1;')
                with ui.row().classes('gap-2 items-start').style('margin-top: -18px; margin-left: -45px; transform-origin: top left;'):
                    if visible_D1T1_natural:
                        card("/menu/natural/D1T1-pv2.jpg", [D1T1], classes)
                    if visible_D1T2_natural:
                        card("/menu/natural/D1T2-pv2.jpg", [D1T2], classes)
                    if visible_D1T3_natural:
                        card("/menu/natural/D1T3-pv2.jpg", [D1T3], classes)

    
        update_all_cards_visibility()



    def refresh_cards_natart():
        
       #  We delete old content
        cards_container_natart1.clear()
        cards_container_natart2.clear()
       

       #  Update visibility based on time
       
        if natart_hour == "12:53":
            visible_D1T3_C2_natart=True
            visible_D1T3_C5_natart=True
            visible_D2T3_C2_natart=False
            visible_D2T3_C5_natart=False
        elif natart_hour == "13:56":
            visible_D1T3_C2_natart=False
            visible_D1T3_C5_natart=False
            visible_D2T3_C2_natart=True
            visible_D2T3_C5_natart=True
        else:
            visible_D1T3_C2_natart=True
            visible_D1T3_C5_natart=True
            visible_D2T3_C2_natart=True
            visible_D2T3_C5_natart=True
            


       # First column: Apr 1st
        if (visible_D2T3_C2_natart or visible_D2T3_C5_natart) and \
        (natart_day is None or natart_day == "Apr 1st" or natart_day == "All"):
            with cards_container_natart1:
                ui.label("Apr 1st").classes('text-sm').style('margin-bottom: 5px; line-height: 1;')
                with ui.row().classes('gap-2 items-start').style('margin-top: -18px; margin-left: -45px; transform-origin: top left;'):
                    if visible_D2T3_C2_natart:
                        card("/menu/Natural+Artificial/D2T3-C2-pv2.jpg", [D2T3,C2], classes)
                    if visible_D2T3_C5_natart:
                        card("/menu/Natural+Artificial/D2T3-C5-pv2.jpg", [D2T3,C1,C2,C4], classes)


        # Second column: Dec 25th 
        if (visible_D1T3_C5_natart or visible_D1T3_C2_natart) and \
        (natart_day is None or natart_day == "Dec 25th" or natart_day == "All"):
            with cards_container_natart2:
                ui.label("Dec 25th").classes('text-sm').style('margin-bottom: 5px; line-height: 1;')
                with ui.row().classes('gap-2 items-start').style('margin-top: -18px; margin-left: -45px; transform-origin: top left;'):
                    if visible_D1T3_C2_natart:
                        card("/menu/Natural+Artificial/D1T3-C2-pv2.jpg", [D1T3,C2], classes)
                    if visible_D1T3_C5_natart:
                        card("/menu/Natural+Artificial/D1T3-C5-pv2.jpg", [D1T3,C1,C2,C4], classes)

    
        update_all_cards_visibility()


    def refresh_cards_all():
        
       #  We delete old content
        cards_container_all1.clear()
        cards_container_all2.clear()
        cards_container_all3.clear()
        cards_container_all4.clear()
        cards_container_all5.clear()
        cards_container_all6.clear()
       

       #  Update visibility based on time
       
        if all_hour == "10:00":
            visible_D2T1_all = True
            visible_D2T2_all = False
            visible_D2T3_all = False
            visible_D3T1_all = True
            visible_D3T2_all = False
            visible_D3T3_all = False
            visible_D1T1_all = True
            visible_D1T2_all = False
            visible_D1T3_all = False
            visible_D1T3_C2_all=False
            visible_D1T3_C5_all=False
            visible_D2T3_C2_all=False
            visible_D2T3_C5_all=False
        elif all_hour == "10:53":
            visible_D2T1_all = False
            visible_D2T2_all = False
            visible_D2T3_all = False
            visible_D3T1_all = False
            visible_D3T2_all = False
            visible_D3T3_all = False
            visible_D1T1_all = False
            visible_D1T2_all = True
            visible_D1T3_all = False
            visible_D1T3_C2_all=False
            visible_D1T3_C5_all=False
            visible_D2T3_C2_all=False
            visible_D2T3_C5_all=False
        elif all_hour == "10:56":
            visible_D2T1_all = False
            visible_D2T2_all = True
            visible_D2T3_all = False
            visible_D3T1_all = False
            visible_D3T2_all = False
            visible_D3T3_all = False
            visible_D1T1_all = False
            visible_D1T2_all = False
            visible_D1T3_all = False
            visible_D1T3_C2_all=False
            visible_D1T3_C5_all=False
            visible_D2T3_C2_all=False
            visible_D2T3_C5_all=False
        elif all_hour == "11:53":
            visible_D2T1_all = False
            visible_D2T2_all = False
            visible_D2T3_all = False
            visible_D3T1_all = False
            visible_D3T2_all = True
            visible_D3T3_all = False
            visible_D1T1_all = False
            visible_D1T2_all = False
            visible_D1T3_all = False
            visible_D1T3_C2_all=False
            visible_D1T3_C5_all=False
            visible_D2T3_C2_all=False
            visible_D2T3_C5_all=False
        elif all_hour == "12:53":
            visible_D2T1_all = False
            visible_D2T2_all = False
            visible_D2T3_all = False
            visible_D3T1_all = False
            visible_D3T2_all = False
            visible_D3T3_all = False
            visible_D1T1_all = False
            visible_D1T2_all = False
            visible_D1T3_all = True
            visible_D1T3_C2_all=True
            visible_D1T3_C5_all=True
            visible_D2T3_C2_all=False
            visible_D2T3_C5_all=False
        elif all_hour == "13:53":
            visible_D2T1_all = False
            visible_D2T2_all = False
            visible_D2T3_all = False
            visible_D3T1_all = False
            visible_D3T2_all = False
            visible_D3T3_all = True
            visible_D1T1_all = False
            visible_D1T2_all = False
            visible_D1T3_all = False
            visible_D1T3_C2_all=False
            visible_D1T3_C5_all=False
            visible_D2T3_C2_all=False
            visible_D2T3_C5_all=False
        elif all_hour == "13:56":
            visible_D2T1_all = False
            visible_D2T2_all = False
            visible_D2T3_all= True
            visible_D3T1_all = False
            visible_D3T2_all = False
            visible_D3T3_all= False
            visible_D1T1_all = False
            visible_D1T2_all = False
            visible_D1T3_all = False
            visible_D1T3_C2_all=False
            visible_D1T3_C5_all=False
            visible_D2T3_C2_all=True
            visible_D2T3_C5_all=True
        else:
            visible_D2T1_all= True
            visible_D2T2_all = True
            visible_D2T3_all = True
            visible_D3T1_all = True
            visible_D3T2_all = True
            visible_D3T3_all = True
            visible_D1T1_all = True
            visible_D1T2_all = True
            visible_D1T3_all = True
            visible_D1T3_C2_all=True
            visible_D1T3_C5_all=True
            visible_D2T3_C2_all=True
            visible_D2T3_C5_all=True
            

        #Natural

       # First column: Apr 1st
        if (visible_D2T1_all or visible_D2T2_all or visible_D2T3_all) and \
        (all_day is None or all_day == "Apr 1st" or all_day == "All"):
            with cards_container_all1:
                ui.label("Apr 1st").classes('text-sm').style('margin-bottom: 5px; line-height: 1;')
                with ui.row().classes('gap-2 items-start').style('margin-top: -18px; margin-left: -45px;transform: scale(0.9); transform-origin: top left;'):
                    if visible_D2T1_all:
                        card("/menu/natural/D2T1-pv2.jpg", [D2T1], classes)
                    if visible_D2T2_all:
                        card("/menu/natural/D2T2-pv2.jpg", [D2T2], classes)
                    if visible_D2T3_all:
                        card("/menu/natural/D2T3-pv2.jpg", [D2T3], classes)


        # Second column: Jun 6th 
        if (visible_D3T1_all or visible_D3T2_all or visible_D3T3_all) and \
        (all_day is None or all_day == "Jun 6th" or all_day == "All"):
            with cards_container_all2:
                ui.label("Jun 6th").classes('text-sm').style('margin-bottom: 5px; line-height: 1;')
                with ui.row().classes('gap-2 items-start').style('margin-top: -18px; margin-left: -45px;transform: scale(0.9); transform-origin: top left;'):
                    if visible_D3T1_all:
                        card("/menu/natural/D3T1-pv2.jpg", [D3T1], classes)
                    if visible_D3T2_all:
                        card("/menu/natural/D3T2-pv2.jpg", [D3T2], classes)
                    if visible_D3T3_all:
                        card("/menu/natural/D3T3-pv2.jpg", [D3T3], classes)

        # Third column: Dec 25th 
        if (visible_D1T1_all or visible_D1T2_all or visible_D1T3_all)and \
        (all_day is None or all_day == "Dec 25th" or all_day == "All"):
            with cards_container_all3:
                ui.label("Dec 25th").classes('text-sm').style('margin-bottom: 5px; line-height: 1;')
                with ui.row().classes('gap-2 items-start').style('margin-top: -18px; margin-left: -45px;transform: scale(0.9); transform-origin: top left;'):
                    if visible_D1T1_all:
                        card("/menu/natural/D1T1-pv2.jpg", [D1T1], classes)
                    if visible_D1T2_all:
                        card("/menu/natural/D1T2-pv2.jpg", [D1T2], classes)
                    if visible_D1T3_all:
                        card("/menu/natural/D1T3-pv2.jpg", [D1T3], classes)

        #Artificial

        with cards_container_all4:
                with ui.row().classes('gap-2 items-start').style('margin-top: 18px; margin-left: -45px;transform: scale(0.9); transform-origin: top left;'):
                   
                    card("/menu/artificial/C1-pv2.jpg", [C1], classes)
                    card("/menu/artificial/C2-pv2.jpg", [C2], classes)
                    card("/menu/artificial/C3-pv2.jpg", [C3], classes)
                    card("/menu/artificial/C4-pv2.jpg", [C4], classes)
                    card("/menu/artificial/C5-pv2.jpg", [C1, C2, C4], classes)
        

        #Nat+Art

        # First column: Apr 1st
        if (visible_D2T3_C2_all or visible_D2T3_C5_all) and \
        (all_day is None or all_day == "Apr 1st" or all_day == "All"):
            with cards_container_all5:
                ui.label("Apr 1st").classes('text-sm').style('margin-bottom: 5px; line-height: 1;')
                with ui.row().classes('gap-2 items-start').style('margin-top: -18px; margin-left: -45px;transform: scale(0.9); transform-origin: top left;'):
                    if visible_D2T3_C2_all:
                        card("/menu/Natural+Artificial/D2T3-C2-pv2.jpg", [D2T3,C2], classes)
                    if visible_D2T3_C5_all:
                        card("/menu/Natural+Artificial/D2T3-C5-pv2.jpg", [D2T3,C1,C2,C4], classes)

        # Second column: Dec 25st
        if (visible_D1T3_C5_all or visible_D1T3_C2_all) and \
        (all_day is None or all_day == "Dec 25th" or all_day == "All"):
            with cards_container_all6:
                ui.label("Dec 25th").classes('text-sm').style('margin-bottom: 5px; line-height: 1;')
                with ui.row().classes('gap-2 items-start').style('margin-top: -18px; margin-left: -45px;transform: scale(0.9); transform-origin: top left;'):
                    if visible_D1T3_C2_all:
                        card("/menu/Natural+Artificial/D1T3-C2-pv2.jpg", [D1T3,C2], classes)
                    if visible_D1T3_C5_all:
                        card("/menu/Natural+Artificial/D1T3-C5-pv2.jpg", [D1T3,C1,C2,C4], classes)

    
        update_all_cards_visibility()

        

            



   
    # Natural illumination
    with menu_panels["Natural illumination"]:
        classes = "w-[180px] h-[320px]"

        # main container
        with ui.row().classes('w-full justify-end items-center gap-6').style('padding: 0px 40px 0 40px;margin-top:5px'):
            # Relative container for the "Time" menu
            with ui.element('div').classes('relative'):

                icon_hour= ui.icon('access_time', size="20px").classes('cursor-pointer rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')
                label_hour = ui.label("Hour").classes(
                    'text-sm text-gray-500 cursor-pointer hover:text-black select-none'
                )

                # Time selection menu
                with ui.menu().props(
                    'auto-close="false" anchor="bottom middle" self="top middle"'
                ).classes('bg-white shadow-md rounded-md p-2 z-50 w-40') as hour_menu:
                    ui.label("Select hour").classes('text-sm text-gray-600 px-2 py-1')
                    ui.separator()

                    def set_hour(hour):
                        global natural_hour
                        natural_hour = hour


                        ui.run_javascript(f'localStorage.setItem("natural_hour", "{hour}")')

                        if hour == "All":
                            icon_hour.set_visibility(True)
                            label_hour.set_text("")
                        else:
                            label_hour.set_text(hour)
                            icon_hour.set_visibility(False)
                        refresh_cards_natural()

                    ui.menu_item("All", lambda: set_hour("All"))
                    ui.menu_item("10:00 am", lambda: set_hour("10:00"))
                    ui.menu_item("10:53 am", lambda: set_hour("10:53"))
                    ui.menu_item("10:56 am", lambda: set_hour("10:56"))
                    ui.menu_item("11:53 am", lambda: set_hour("11:53"))
                    ui.menu_item("12:53 pm", lambda: set_hour("12:53"))
                    ui.menu_item("13:53 pm", lambda: set_hour("13:53"))
                    ui.menu_item("13:56 pm", lambda: set_hour("13:56"))

                label_hour.on('click', hour_menu.toggle)
                icon_hour.on('click', hour_menu.toggle)


                async def restore_hour_from_localstorage():
                    saved_hour = await ui.run_javascript('localStorage.getItem("natural_hour")')
                    if not saved_hour or saved_hour == "All":
                        icon_hour.set_visibility(True)
                        label_hour.set_text("")
                    else:
                        icon_hour.set_visibility(False)
                        label_hour.set_text(saved_hour)
                        global natural_hour
                        natural_hour = saved_hour
                        refresh_cards_natural()

                ui.timer(0.1, restore_hour_from_localstorage, once=True)

            


           # Relative container for the "Day" menu
            with ui.element('div').classes('relative'):

                icon_day= ui.icon('calendar_today', size="20px").classes('cursor-pointer rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')
                label_day = ui.label("Day").classes(
                    'text-sm text-gray-500 cursor-pointer hover:text-black select-none'
                )

               # Day selection menu
                with ui.menu().props(
                    'auto-close="false" anchor="bottom middle" self="top middle"'
                ).classes('bg-white shadow-md rounded-md p-2 z-50 w-40') as day_menu:
                    ui.label("Select day ").classes('text-sm text-gray-600 px-2 py-1')
                    ui.separator()

                    def set_day(day):
                        global natural_day
                        natural_day = day
                        ui.run_javascript(f'localStorage.setItem("natural_day", "{day}")')
                        if day == "All":
                            label_day.set_text("")
                            icon_day.set_visibility(True)
                        else:
                            label_day.set_text(day)
                            icon_day.set_visibility(False)
                        refresh_cards_natural()

                    ui.menu_item("All", lambda: set_day("All"))
                    ui.menu_item("Apr 1st", lambda: set_day("Apr 1st"))
                    ui.menu_item("Jun 6th", lambda: set_day("Jun 6th"))
                    ui.menu_item("Dec 25th", lambda: set_day("Dec 25th"))
                    

                label_day.on('click', day_menu.toggle)
                icon_day.on('click', day_menu.toggle)


                async def restore_day_from_localstorage():
                    saved_day = await ui.run_javascript('localStorage.getItem("natural_day")')
                    if not saved_day or saved_day == "All":
                        icon_day.set_visibility(True)
                        label_day.set_text("")
                    else:
                        icon_day.set_visibility(False)
                        label_day.set_text(saved_day)
                        global natural_day
                        natural_day = saved_day
                        refresh_cards_natural()

                ui.timer(0.1, restore_day_from_localstorage, once=True)

          # view label 
            ui.icon('visibility', size="20px").classes('cursor-pointer rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')
        

        

        #Content with horizontal scroll
        with ui.row().classes('w-full overflow-x-auto no-scrollbar').style('padding-left: 40px; white-space: nowrap; padding-top: 15px;'):
            with ui.row().classes('justify-start gap-1 items-start flex-nowrap').style('display: inline-flex;'):

                # First column: Apr 1st
                with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start; margin-left: 0px;') as cards_container_natural1:
                    pass

                # Second column: Jun 6th
                with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start; margin-left: 20px;') as cards_container_natural2:
                    pass

                #Third column: Dec 25th
                with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start; margin-left: 20px;') as cards_container_natural3:
                    pass

        
        refresh_cards_natural()


    # Artificial illumination
    with menu_panels["Artificial illumination"]:
        classes = "w-[180px] h-[320px]"

        with ui.row().classes('w-full justify-end items-center gap-6').style('padding: 0px 40px 0 40px; margin-top:5px'):
            ui.icon('visibility', size="20px").classes('cursor-pointer rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')

        with ui.row().classes('w-full overflow-x-auto no-scrollbar').style('padding-left: 50px; white-space: nowrap; padding-top: 0px;'):
            with ui.row().classes('justify-start gap-8 items-start flex-nowrap').style('display: inline-flex;'):
                
                
                with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start; margin-left: 0px;'):
                    
                    with ui.row().classes('gap-2 items-start').style('margin-top: 20px; margin-left: -55px;'):

                        card("/menu/artificial/C1-pv2.jpg", [C1], classes)
                        card("/menu/artificial/C2-pv2.jpg", [C2], classes)
                        card("/menu/artificial/C3-pv2.jpg", [C3], classes)
                        card("/menu/artificial/C4-pv2.jpg", [C4], classes)
                        card("/menu/artificial/C5-pv2.jpg", [C1, C2, C4], classes)




    # Natural + Artificial illumination

    with menu_panels["Natural + Artificial illumination"]:
        classes = "w-[180px] h-[320px]"

        # main container
        with ui.row().classes('w-full justify-end items-center gap-6').style('padding: 0px 40px 0 40px; margin-top:5px'):
            # Relative container for the "Time" menu
            with ui.element('div').classes('relative'):
                icon_hour3= ui.icon('access_time', size="20px").classes('cursor-pointer rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')
                label_hour3 = ui.label("Hour").classes(
                    'text-sm text-gray-500 cursor-pointer hover:text-black select-none'
                )

                # Time selection menu
                with ui.menu().props(
                    'auto-close="false" anchor="bottom middle" self="top middle"'
                ).classes('bg-white shadow-md rounded-md p-2 z-50 w-40') as hour_menu3:
                    ui.label("Select hour").classes('text-sm text-gray-600 px-2 py-1')
                    ui.separator()

                    def set_hour3(hour3):
                        global natart_hour
                        natart_hour = hour3

                        ui.run_javascript(f'localStorage.setItem("natart_hour", "{hour3}")')

                        if hour3 == "All":
                            icon_hour3.set_visibility(True)
                            label_hour3.set_text("")
                        else:
                            label_hour3.set_text(hour3)
                            icon_hour3.set_visibility(False)
                        refresh_cards_natart()

                    ui.menu_item("All", lambda: set_hour3("All"))
                    ui.menu_item("12:53 pm", lambda: set_hour3("12:53"))
                    ui.menu_item("13:56 pm", lambda: set_hour3("13:56"))

                label_hour3.on('click', hour_menu3.toggle)
                icon_hour3.on('click', hour_menu3.toggle)


                async def restore_hour3_from_localstorage():
                    saved_hour3 = await ui.run_javascript('localStorage.getItem("natart_hour")')
                    if not saved_hour3 or saved_hour3 == "All":
                        icon_hour3.set_visibility(True)
                        label_hour3.set_text("")
                    else:
                        icon_hour3.set_visibility(False)
                        label_hour3.set_text(saved_hour3)
                        global natart_hour
                        natart_hour = saved_hour3
                        refresh_cards_natural()

                ui.timer(0.1, restore_hour3_from_localstorage, once=True)



           # Relative container for the "Day" menu
            with ui.element('div').classes('relative'):
                icon_day3= ui.icon('calendar_today', size="20px").classes('cursor-pointer rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')
                label_day3 = ui.label("Day").classes(
                    'text-sm text-gray-500 cursor-pointer hover:text-black select-none'
                )

               # Day selection menu
                with ui.menu().props(
                    'auto-close="false" anchor="bottom middle" self="top middle"'
                ).classes('bg-white shadow-md rounded-md p-2 z-50 w-40') as day_menu3:
                    ui.label("Select day").classes('text-sm text-gray-600 px-2 py-1')
                    ui.separator()

                    def set_day3(day3):
                        global natart_day
                        natart_day = day3

                        ui.run_javascript(f'localStorage.setItem("natart_day", "{day3}")')

                        if day3 == "All":
                            label_day3.set_text("")
                            icon_day3.set_visibility(True)
                        else:
                            label_day3.set_text(day3)
                            icon_day3.set_visibility(False)
                        refresh_cards_natart()

                    ui.menu_item("All", lambda: set_day3("All"))
                    ui.menu_item("Apr 1st", lambda: set_day3("Apr 1st"))
                    ui.menu_item("Dec 25th", lambda: set_day3("Dec 25th"))
                    

                label_day3.on('click', day_menu3.toggle)
                icon_day3.on('click', day_menu3.toggle)

                async def restore_day3_from_localstorage():
                    saved_day3 = await ui.run_javascript('localStorage.getItem("natart_day")')
                    if not saved_day3 or saved_day3 == "All":
                        icon_day3.set_visibility(True)
                        label_day3.set_text("")
                    else:
                        icon_day3.set_visibility(False)
                        label_day3.set_text(saved_day3)
                        global natart_day
                        natart_day = saved_day3
                        refresh_cards_natart()

                ui.timer(0.1, restore_day3_from_localstorage, once=True)

          # view label 
            ui.icon('visibility', size="20px").classes('cursor-pointer rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')

        #Content with horizontal scroll
        with ui.row().classes('w-full overflow-x-auto no-scrollbar').style('padding-left: 40px; white-space: nowrap; padding-top: 15px;'):
            with ui.row().classes('justify-start gap-1 items-start flex-nowrap').style('display: inline-flex;'):

                # First column: Apr 1st
                with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start; margin-left: 0px;') as cards_container_natart1:
                    pass

                # Second column: Dec 25th
                with ui.column().classes('items-start flex-shrink-0').style('align-items: flex-start; margin-left: 20px;') as cards_container_natart2:
                    pass

        
        refresh_cards_natart()
  


    
    #All Combinations


    with menu_panels["All combinations"]:
        classes = "w-[180px] h-[320px]"

        with ui.row().classes(' controls w-full justify-end items-center gap-6').style('padding: 0px 40px; margin-top:5px'):
            # Hour menu
            with ui.element('div').classes('relative'):

                icon_hour4= ui.icon('access_time', size="20px").classes('cursor-pointer rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')
                label_hour4 = ui.label("Hour").classes('text-sm text-gray-500 cursor-pointer hover:text-black select-none')
                with ui.menu().props('auto-close="false" anchor="bottom middle" self="top middle"') \
                        .classes('bg-white shadow-md rounded-md p-2 z-50 w-40') as hour_menu4:
                    ui.label("Select hour").classes('text-sm text-gray-600 px-2 py-1')
                    ui.separator()
                    def set_hour4(hour4):
                        global all_hour
                        all_hour = hour4

                        ui.run_javascript(f'localStorage.setItem("all_hour", "{hour4}")')
                        
                        if hour4 =="All":
                            icon_hour4.set_visibility(True)
                            label_hour4.set_text("")
                        else:
                            label_hour4.set_text(hour4)
                            icon_hour4.set_visibility(False)


                        refresh_cards_all()
                    ui.menu_item("All", lambda: set_hour4("All"))
                    ui.menu_item("10:00 am", lambda: set_hour4("10:00"))
                    ui.menu_item("10:53 am", lambda: set_hour4("10:53"))
                    ui.menu_item("10:56 am", lambda: set_hour4("10:56"))
                    ui.menu_item("11:53 am", lambda: set_hour4("11:53"))
                    ui.menu_item("12:53 pm", lambda: set_hour4("12:53"))
                    ui.menu_item("13:53 pm", lambda: set_hour4("13:53"))
                    ui.menu_item("13:56 pm", lambda: set_hour4("13:56"))


                label_hour4.on('click', hour_menu4.toggle)
                icon_hour4.on('click', hour_menu4.toggle)

                async def restore_hour4_from_localstorage():
                    saved_hour4 = await ui.run_javascript('localStorage.getItem("all_hour")')
                    if not saved_hour4 or saved_hour4 == "All":
                        icon_hour4.set_visibility(True)
                        label_hour4.set_text("")
                    else:
                        icon_hour4.set_visibility(False)
                        label_hour4.set_text(saved_hour4)
                        global all_hour
                        all_hour = saved_hour4
                        refresh_cards_all()

                ui.timer(0.1, restore_hour4_from_localstorage, once=True)
            # Day menu
            with ui.element('div').classes('relative'):

                icon_day4= ui.icon('calendar_today', size="20px").classes('cursor-pointer rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')
                label_day4 = ui.label("Day").classes('text-sm text-gray-500 cursor-pointer hover:text-black select-none')
                with ui.menu().props('auto-close="false" anchor="bottom middle" self="top middle"') \
                        .classes('bg-white shadow-md rounded-md p-2 z-50 w-40') as day_menu4:
                    ui.label("Select day").classes('text-sm text-gray-600 px-2 py-1')
                    ui.separator()
                    def set_day4(day4):
                        global all_day
                        all_day = day4

                        ui.run_javascript(f'localStorage.setItem("all_day", "{day4}")')

                        if day4 =="All":
                            icon_day4.set_visibility(True)
                            label_day4.set_text("")
                        else:
                            label_day4.set_text(day4)
                            icon_day4.set_visibility(False)
                        refresh_cards_all()
                    ui.menu_item("All", lambda: set_day4("All"))
                    ui.menu_item("Apr 1st", lambda: set_day4("Apr 1st"))
                    ui.menu_item("Jun 6th", lambda: set_day4("Jun 6th"))
                    ui.menu_item("Dec 25th", lambda: set_day4("Dec 25th"))
                label_day4.on('click', day_menu4.toggle)
                icon_day4.on('click', day_menu4.toggle)


                async def restore_day4_from_localstorage():
                    saved_day4 = await ui.run_javascript('localStorage.getItem("all_day")')
                    if not saved_day4 or saved_day4 == "All":
                        icon_day4.set_visibility(True)
                        label_day4.set_text("")
                    else:
                        icon_day4.set_visibility(False)
                        label_day4.set_text(saved_day4)
                        global all_day
                        all_day = saved_day4
                        refresh_cards_all()

                ui.timer(0.1, restore_day4_from_localstorage, once=True)

            # View label
            ui.icon('visibility', size="20px").classes('cursor-pointer rounded hover:bg-gray-100 transition flex-shrink-0 material-symbols-outlined')

        # --- Scrollable Cards Row ---
        with ui.row().classes(
            'cards-wrapper w-full overflow-x-auto no-scrollbar flex-nowrap gap-10 pl-10 pr-10 items-start'
        ).style('white-space: nowrap;'):
            
            # Natural
            with ui.column().classes('items-start w-auto flex-shrink-0'):
                ui.label("Natural illumination").classes('text-black text-sm font-semibold mb-2')
                with ui.row().classes('gap-1 items-start'):
                    with ui.column().classes('flex-shrink-0') as cards_container_all1: pass
                    with ui.column().classes('flex-shrink-0') as cards_container_all2: pass
                    with ui.column().classes('flex-shrink-0') as cards_container_all3: pass

            # Artificial
            with ui.column().classes('items-start w-auto flex-shrink-0'):
                ui.label("Artificial illumination").classes('text-black text-sm font-semibold mb-2')
                with ui.row().classes('gap-1 items-start'):
                    with ui.column().classes('flex-shrink-0') as cards_container_all4: pass

            # Natural + Artificial
            with ui.column().classes('items-start w-auto flex-shrink-0 -ml-6'):
                ui.label("Natural+Artificial illumination").classes('text-black text-sm font-semibold mb-2')
                with ui.row().classes('gap-1 items-start'):
                    with ui.column().classes('flex-shrink-0') as cards_container_all5: pass
                    with ui.column().classes('flex-shrink-0') as cards_container_all6: pass

            refresh_cards_all()     


    # Main viewer occupying all the rest of the screen
    iframe_container = ui.html(show_selected_images(), sanitize=False)\
    .classes('w-screen')\
    .style('height: calc(100vh - 50px); position: relative; z-index: 0; margin-left: -16px;')


port = int(os.environ.get("PORT", 10000))
ui.run(port=port)
