from flask import Flask, request, redirect, session, send_file, jsonify
import io, json, zipfile, base64
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = "bulangu-v8-global-founder-mam-bulangu"

DATA_STORE = []  # {id, date, state, lga, ward, farmer, category, content, voice, image}

# --- NIGERIA 37 STATES + LGA SAMPLE (Full list - searchable) ---
NIGERIA_DATA = {
 "Abia": ["Aba North","Aba South","Umuahia North"],
 "Adamawa": ["Yola North","Yola South","Mubi North"],
 "Akwa Ibom": ["Uyo","Eket","Ikot Abasi"],
 "Anambra": ["Awka South","Onitsha North","Obosi"],
 "Bauchi": ["Bauchi","Katagum","Misau"],
 "Bayelsa": ["Yenagoa","Brass","Ogbia"],
 "Benue": ["Makurdi","Gboko","Otukpo"],
 "Borno": ["Maiduguri","Biu","Bama"],
 "Cross River": ["Calabar Municipal","Ogoja","Ikom"],
 "Delta": ["Asaba","Warri South","Ughelli North"],
 "Ebonyi": ["Abakaliki","Afikpo North","Onicha"],
 "Edo": ["Benin City","Auchi","Ekpoma"],
 "Ekiti": ["Ado Ekiti","Ikere","Ise Orun"],
 "Enugu": ["Enugu North","Nsukka","Udi"],
 "FCT": ["Abaji","AMAC","Bwari","Gwagwalada","Kuje","Kwali"],
 "Gombe": ["Gombe","Kaltungo","Dukku"],
 "Imo": ["Owerri Municipal","Orlu","Okigwe"],
 "Jigawa": ["Dutse","Hadejia","Gumel","Kazaure","Birnin Kudu","Maigatari","Bulangu"],
 "Kaduna": ["Kaduna North","Zaria","Kafanchan"],
 "Kano": ["Kano Municipal","Fagge","Gwale"],
 "Katsina": ["Katsina","Daura","Funtua"],
 "Kebbi": ["Birnin Kebbi","Argungu","Yauri"],
 "Kogi": ["Lokoja","Okene","Idah"],
 "Kwara": ["Ilorin West","Offa","Jebba"],
 "Lagos": ["Ikeja","Lagos Island","Alimosho","Badagry"],
 "Nasarawa": ["Lafia","Keffi","Akwanga"],
 "Niger": ["Minna","Bida","Suleja"],
 "Ogun": ["Abeokuta North","Ijebu Ode","Sagamu"],
 "Ondo": ["Akure South","Owo","Ondo West"],
 "Osun": ["Osogbo","Ile Ife","Ilesa"],
 "Oyo": ["Ibadan North","Ogbomosho","Oyo"],
 "Plateau": ["Jos North","Barkin Ladi","Pankshin"],
 "Rivers": ["Port Harcourt","Bonny","Eleme"],
 "Sokoto": ["Sokoto North","Tambuwal","Gwadabawa"],
 "Taraba": ["Jalingo","Wukari","Bali"],
 "Yobe": ["Damaturu","Potiskum","Nguru"],
 "Zamfara": ["Gusau","Kaura Namoda","Anka"]
}

HTML_LOGIN = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bulangu AI Lab - Global</title>
<style>body{font-family:sans-serif;background:#eef2f7;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.box{background:white;padding:35px;border-radius:12px;box-shadow:0 8px 25px rgba(0,0,0,0.15);width:360px;text-align:center}
input{width:100%;padding:12px;margin:8px 0;border:1px solid #ccc;border-radius:8px}
button{width:100%;padding:12px;background:#1877f2;color:white;border:none;border-radius:8px;font-weight:bold;cursor:pointer}
.founder{background:#e7f3ff;color:#1877f2;padding:8px;border-radius:6px;font-weight:bold;margin-top:12px}</style></head>
<body><div class="box"><h2>🌾 Bulangu AI Lab V8</h2><p>Global AI for Agriculture</p>
<form method="POST"><input name="username" placeholder="Username" required><input name="password" type="password" placeholder="Password" required><button>Login</button></form>
<div class="founder">Founder: Mam Bulangu</div><small>V8 Global English - Full Features</small></div></body></html>
"""

HTML_DASH = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bulangu AI Lab V8</title>
<style>
body{font-family:sans-serif;margin:0;background:#f5f7fb} header{background:#1877f2;color:white;padding:12px 18px;display:flex;justify-content:space-between;flex-wrap:wrap}
.container{padding:12px;max-width:1150px;margin:auto} .card{background:white;padding:16px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:14px}
button{padding:9px 14px;background:#1877f2;color:white;border:none;border-radius:6px;cursor:pointer;margin:2px} .btn-g{background:#42b72a} .btn-r{background:#fa3e3e} .btn-y{background:#f7b928;color:black}
select,input,textarea{padding:9px;border:1px solid #ccc;border-radius:6px;width:100%;box-sizing:border-box;margin:4px 0}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px} @media(max-width:800px){.grid3{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:13px} th,td{border:1px solid #ddd;padding:7px} th{background:#eef2f7}
.badge{padding:3px 8px;border-radius:10px;color:white;font-size:11px} .cat-image{background:#8e44ad} .cat-voice{background:#2980b9} .cat-proverb{background:#e67e22} .cat-market{background:#27ae60}
</style></head><body>
<header><div><b>Bulangu AI Lab V8</b> | Founder: Mam Bulangu | Global English</div>
<div><a href='/admin' style='color:white;margin-right:10px'>Admin</a><a href='/settings' style='color:white;margin-right:10px'>Settings</a><a href='/logout' style='color:white'>Logout</a></div></header>
<div class="container">

<div class="card"><h3>📍 Location - All Nigeria (37 States + FCT)</h3>
<div class="grid3">
<div><label>State (Click list):</label><select id="state" onchange="loadLGA()"><option value="">-- Select State --</option></select></div>
<div><label>LGA (Local Government):</label><select id="lga" onchange="loadWardHint()"><option value="">-- Select LGA --</option></select></div>
<div><label>Ward (Searchable - Type):</label><input list="wardList" id="ward" placeholder="Type ward - e.g Bulangu Ward"><datalist id="wardList"></datalist></div>
</div>
</div>

<div class="card"><h3>🎤 Voice Recording + Content - Example: Mam (not Alhaji Sani)</h3>
<label>Farmer Name (Example: Mam Bulangu):</label><input id="farmer" value="Mam Bulangu" placeholder="Mam Bulangu">
<div class="grid3">
<div><label>Category:</label><select id="category"><option value="image">Image</option><option value="voice">Voice</option><option value="proverb">Proverb</option><option value="market">Market</option></select></div>
<div><label>Upload Image:</label><input type="file" id="imgFile" accept="image/*"></div>
<div><label>Voice:</label><button id="recBtn" onclick="toggleRec()">🔴 Start Voice (15s)</button> <span id="recStatus">Ready</span></div>
</div><br>
<textarea id="content" placeholder="Enter content here... Example: Proverb - 'Farming is wealth' - Voice transcription will appear here... Market price - Rice 50k per bag" style="height:90px"></textarea><br><br>
<button class="btn-g" onclick="saveData()">💾 Save</button> <button onclick="clearForm()">Clear</button>
</div>

<div class="card"><h3>📊 Data Table - All Categories - Search & Share Link</h3>
<input id="search" placeholder="Search state, lga, ward, farmer, content..." onkeyup="filterTable()" style="margin-bottom:8px">
<table><thead><tr><th>Date</th><th>State/LGA/Ward</th><th>Farmer</th><th>Category</th><th>Content</th><th>Link</th></tr></thead><tbody id="tbody"></tbody></table><br>
<div class="grid3">
<button onclick="downloadZip('all')">📥 Download ALL ZIP</button>
<button onclick="downloadZip('image')">📥 ZIP Images</button>
<button onclick="downloadZip('voice')">📥 ZIP Voices</button>
<button onclick="downloadZip('proverb')">📥 ZIP Proverbs</button>
<button onclick="downloadZip('market')">📥 ZIP Market</button>
<button onclick="window.location='/download-excel'">📥 Download Excel</button>
</div>
</div>

<div class="card" style="background:#e7f3ff;text-align:center"><b>Founder: Mam Bulangu</b> | Bulangu AI Lab V8 Global | State click list, LGA click list, Ward searchable | Admin + Settings + Share Link Enabled</div>
</div>

<script>
const NIGERIA_DATA = __NIGERIA_DATA__;

function initStates(){
 let s=document.getElementById('state'); Object.keys(NIGERIA_DATA).sort().forEach(st=>{let o=document.createElement('option'); o.value=st; o.textContent=st; s.appendChild(o)});
}
function loadLGA(){
 let st=document.getElementById('state').value; let lgaSel=document.getElementById('lga'); lgaSel.innerHTML='<option value="">-- Select LGA --</option>';
 if(NIGERIA_DATA[st]){NIGERIA_DATA[st].forEach(l=>{let o=document.createElement('option'); o.value=l; o.textContent=l; lgaSel.appendChild(o)});}
 loadWardHint();
}
function loadWardHint(){
 let wardList=document.getElementById('wardList'); wardList.innerHTML=''; 
 let sampleWards=['Ward 01','Ward 02','Bulangu Ward','Garin Mam Ward','Central Ward','Market Ward','Fada Ward'];
 sampleWards.forEach(w=>{let o=document.createElement('option'); o.value=w; wardList.appendChild(o)});
}

let rec,chunks=[],isRec=false, lastVoiceBlob=null;
function toggleRec(){
 if(!isRec){
  navigator.mediaDevices.getUserMedia({audio:true}).then(stream=>{
   rec=new MediaRecorder(stream); chunks=[]; rec.ondataavailable=e=>chunks.push(e.data);
   rec.onstop=()=>{lastVoiceBlob=new Blob(chunks,{type:'audio/webm'}); document.getElementById('recStatus').innerText='Done - Voice saved'; document.getElementById('content').value+=' [Voice recorded - '+new Date().toLocaleTimeString()+']';};
   rec.start(); isRec=true; document.getElementById('recBtn').innerText='⏹️ Stop'; document.getElementById('recStatus').innerText='Recording...'; setTimeout(()=>{if(isRec)toggleRec()},15000);
  });
 } else { rec.stop(); isRec=false; document.getElementById('recBtn').innerText='🔴 Start Voice (15s)'; }
}

function saveData(){
 let state=document.getElementById('state').value, lga=document.getElementById('lga').value, ward=document.getElementById('ward').value, farmer=document.getElementById('farmer').value||'Mam Bulangu', category=document.getElementById('category').value, content=document.getElementById('content').value;
 if(!state){alert('Select State');return} if(!content){alert('Enter content');return}
 let imgInput=document.getElementById('imgFile'); let imgData=''; if(imgInput.files[0]){let reader=new FileReader(); reader.onload=function(e){imgData=e.target.result; sendToServer(state,lga,ward,farmer,category,content,imgData)}; reader.readAsDataURL(imgInput.files[0]); return;}
 sendToServer(state,lga,ward,farmer,category,content,'');
}
function sendToServer(state,lga,ward,farmer,category,content,imgData){
 fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({state,lga,ward,farmer,category,content,image:imgData})}).then(()=>{loadTable(); clearForm()});
}
function clearForm(){document.getElementById('content').value=''; document.getElementById('imgFile').value='';}
function loadTable(){fetch('/data').then(r=>r.json()).then(rows=>{let tb=document.getElementById('tbody'); tb.innerHTML=''; rows.forEach(row=>{tb.innerHTML+=`<tr><td>${row.date}</td><td>${row.state}/${row.lga}/${row.ward}</td><td>${row.farmer}</td><td><span class="badge cat-${row.category}">${row.category}</span></td><td>${row.content.substring(0,80)}</td><td><a href='/view/${row.id}' target='_blank'>View Link</a></td></tr>`})})}
function filterTable(){let q=document.getElementById('search').value.toLowerCase(); let tr=document.getElementById('tbody').getElementsByTagName('tr'); for(let i=0;i<tr.length;i++){tr[i].style.display=tr[i].innerText.toLowerCase().includes(q)?'':'none'}}
function downloadZip(cat){window.location='/download-zip?cat='+cat}
initStates(); loadTable();
</script>
</body></html>
"""

HTML_ADMIN = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin - Bulangu</title>
<style>body{font-family:sans-serif;margin:0;background:#f5f7fb} header{background:#2c3e50;color:white;padding:12px 18px} .container{padding:15px} .card{background:white;padding:15px;border-radius:8px;margin-bottom:12px}</style></head><body>
<header><b>Admin Panel - Founder: Mam Bulangu</b> - <a href='/dashboard' style='color:white'>Back to Dashboard</a></header>
<div class="container">
<div class="card"><h3>👑 Admin Controls</h3><p>Total Records: __COUNT__</p><button onclick="if(confirm('Delete all?'))fetch('/admin/clear',{method:'POST'}).then(()=>location.reload())">🗑️ Clear All Data</button> <button onclick="window.location='/download-zip?cat=all'">📦 Download All ZIP</button></div>
<div class="card"><h3>📋 All Data (Admin View)</h3><div id="adminData"></div></div>
</div><script>fetch('/data').then(r=>r.json()).then(d=>{document.getElementById('adminData').innerHTML='<pre>'+JSON.stringify(d,null,2)+'</pre>'})</script>
</body></html>
"""

HTML_SETTINGS = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Settings</title>
<style>body{font-family:sans-serif;margin:0;background:#f5f7fb} header{background:#1877f2;color:white;padding:12px 18px} .container{padding:15px} .card{background:white;padding:15px;border-radius:8px;margin-bottom:12px}</style></head><body>
<header><b>Settings - Bulangu AI Lab V8</b> - <a href='/dashboard' style='color:white'>Dashboard</a></header>
<div class="container">
<div class="card"><h3>⚙️ App Settings</h3><p><b>Founder:</b> Mam Bulangu</p><p><b>App Name:</b> Bulangu AI Lab V8 Global English</p><p><b>Features:</b> All 37 States + FCT, LGA list on click, Ward searchable, Voice recording, Image upload, Categories: Image/Voice/Proverb/Market, ZIP download per category, Admin, Shareable link</p><p><b>Language:</b> English (Global)</p><p><b>Version:</b> V8 FINAL</p></div>
<div class="card"><h3>🔗 Shareable Link</h3><p>When you save data, each row gets a unique link like <code>/view/ID</code> - You can send to anyone - They will see that data even without login.</p><p>Try: /view/1</p></div>
<div class="card"><h3>👤 Founder Info</h3><p>Mam Bulangu - Founder of Bulangu AI Lab - AI for Agriculture - Jigawa State - Nigeria - Global Project</p></div>
</div></body></html>
"""

@app.route('/')
@app.route('/api/index')
def home(): return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        if request.form.get('username')=='Bulangu' and request.form.get('password')=='Bulangu123':
            session['user']='Bulangu'; return redirect('/dashboard')
        return 'Wrong password <a href="/login">Back</a>'
    return HTML_LOGIN

@app.route('/dashboard')
def dash():
    if 'user' not in session: return redirect('/login')
    html = HTML_DASH.replace('__NIGERIA_DATA__', json.dumps(NIGERIA_DATA))
    return html

@app.route('/save', methods=['POST'])
def save():
    j=request.get_json()
    j['id']=len(DATA_STORE)+1
    j['date']=datetime.now().strftime('%Y-%m-%d %H:%M')
    DATA_STORE.append(j)
    return jsonify({"ok":True,"id":j['id']})

@app.route('/data')
def data(): return jsonify(DATA_STORE[::-1])

@app.route('/view/<int:vid>')
def view(vid):
    item=next((x for x in DATA_STORE if x['id']==vid),None)
    if not item: return "Not found - Share link invalid"
    return f"<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>Shared - Mam Bulangu</title></head><body style='font-family:sans-serif;padding:20px'><h2>Bulangu AI Lab - Shared Data</h2><p><b>Founder:</b> Mam Bulangu</p><p><b>State:</b> {item.get('state')} | <b>LGA:</b> {item.get('lga')} | <b>Ward:</b> {item.get('ward')}</p><p><b>Farmer:</b> {item.get('farmer')}</p><p><b>Category:</b> {item.get('category')}</p><p><b>Content:</b> {item.get('content')}</p><p><b>Date:</b> {item.get('date')}</p><hr><a href='/dashboard'>Go to Dashboard</a> | Founder: Mam Bulangu</body></html>"

@app.route('/download-excel')
def dl_excel():
    if not DATA_STORE: return "No data"
    df=pd.DataFrame(DATA_STORE); out=io.BytesIO(); df.to_excel(out,index=False); out.seek(0)
    return send_file(out, download_name='Bulangu_Global_Mam_Bulangu.xlsx', as_attachment=True)

@app.route('/download-zip')
def dl_zip():
    cat=request.args.get('cat','all')
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w') as z:
        for item in DATA_STORE:
            if cat!='all' and item.get('category')!=cat: continue
            fname=f"{item.get('category')}_{item['id']}.txt"
            content=f"State: {item.get('state')}\nLGA: {item.get('lga')}\nWard: {item.get('ward')}\nFarmer: {item.get('farmer')}\nCategory: {item.get('category')}\nContent: {item.get('content')}\nDate: {item.get('date')}\nFounder: Mam Bulangu\n"
            z.writestr(fname, content)
            if item.get('image'):
                try:
                    header, b64 = item['image'].split(',',1)
                    img_bytes = base64.b64decode(b64)
                    z.writestr(f"images/image_{item['id']}.jpg", img_bytes)
                except: pass
    mem.seek(0)
    return send_file(mem, download_name=f'Bulangu_{cat}_Mam_Bulangu.zip', as_attachment=True)

@app.route('/admin')
def admin():
    if 'user' not in session: return redirect('/login')
    return HTML_ADMIN.replace('__COUNT__', str(len(DATA_STORE)))

@app.route('/admin/clear', methods=['POST'])
def admin_clear():
    DATA_STORE.clear(); return jsonify({"ok":True})

@app.route('/settings')
def settings():
    if 'user' not in session: return redirect('/login')
    return HTML_SETTINGS

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')
