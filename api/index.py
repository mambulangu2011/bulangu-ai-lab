import os, sqlite3, zipfile, datetime, json, io
from flask import Flask, request, render_template_string, redirect, session, send_file, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "bulangu-v6-world-class-founder-2026"
BASE = "/tmp" if os.path.exists("/tmp") else "."
DB = os.path.join(BASE, "bulangu_v6.db")
os.makedirs(os.path.join(BASE, "voices"), exist_ok=True)
os.makedirs(os.path.join(BASE, "images"), exist_ok=True)

NIGERIA_STATES = ["Abia","Adamawa","Akwa Ibom","Anambra","Bauchi","Bayelsa","Benue","Borno","Cross River","Delta","Ebonyi","Edo","Ekiti","Enugu","FCT","Gombe","Imo","Jigawa","Kaduna","Kano","Katsina","Kebbi","Kogi","Kwara","Lagos","Nasarawa","Niger","Ogun","Ondo","Osun","Oyo","Plateau","Rivers","Sokoto","Taraba","Yobe","Zamfara"]

JIGAWA_LGAS = {
 "Auyo":["Auyo","Auyakayi","Ayama","Gamafoi","Gamsarka","Gatafa","Guriko","Kafin Hausa Road","Tsidir","Unik"],
 "Babura":["Babura","Batali","Dorawa","Gasakoli","Insharuwa","Jigawar Sarki","Kanya","Kuzunzumi","Kyambo","Takalafiya","Tajummu","Kyambar Gari"],
 "Biriniwa":["Biriniwa","Diginsa","Fagi","Kachallari","Kazura","Matarababbado","Nguwa","Tsibir","Unguwar Makafi","Dangwaleri"],
 "Birnin Kudu":["Birnin Kudu","Kangire","Kwangwara","Lafiya","Sundimina","Surko","Unguwar Ya","Wurno","Yalwan Damai","Kantoga"],
 "Buji":["Buji","Gantsa","Kawaya","Kukuma","Lelen Kudu","Lelen Arewa","Karma","Kawu","Sara","Jigawar Buji"],
 "Dutse":["Dutse","Jigawar Tsada","Sakwaya","Madobi","Karnaya","Limawa","Waru","Malamawar","Kachi","Chamo"],
 "Gagarawa":["Gagarawa","Gagarawa Gari","Kore","Maikilili","Meda","Mai Zare","Mangada","Garun Gabas","Zaumar Gari","Zarada"],
 "Garki":["Garki","Gwarzon Garki","Jirima","Kanya","Kore","Muku","Doko","Buduru","Garki Kargo","Siyori"],
 "Gumel":["Gumel","Baikarya","Dan Ama","Galagamma","Garin Gari","Gusau","Hammado","Kofar Arewa","Kofar Yamma","Zango"],
 "Guri":["Guri","Abunabo","Adiyani","Dawa","Garbagal","Kadira","Lafiya","Margadu","Matara Babba","Musari"],
 "Gwaram":["Gwaram","Basirka","Fagam","Gwaram Gari","Kila","Kwandiko","Maruta","Sara","Tsangarwa","Dingaya"],
 "Gwiwa":["Gwiwa","Buntusu","Dabi","Dangyatin","Darina","Fandum","Guntai","Korayel","Rorau","Shafe"],
 "Hadejia":["Hadejia","Kasuwar Kuda","Kasuwar Kofa","Majema","Matsaro","Rumfa","Sabon Garu","Yankoli","Dubutu","Atikun"],
 "Jahun":["Jahun","Aujara","Gauza","Gunka","Harbo","Idanduna","Kale","Kanwa","Nagwada","Telemos"],
 "Kafin Hausa":["Kafin Hausa","Balangu","Dumadumin","Gafaya","Jabo","Kafin Hausa Tudu","Majawa","Mezan","Ruba","Sarawa"],
 "Kaugama":["Kaugama","Arbus","Dakayyawa","Hadin Bari","Jarkasa","Ja'e","Marke","Hadandi","Yalo","Askandu"],
 "Kazaure":["Kazaure","Ba'a","Daba","Dabaza","Gada","Isamu","Kargo","Maradawa","Sabaru","Umaru"],
 "Kiri Kasama":["Kiri Kasama","Baturiya","Bulunchai","Doljigi","Fandum","Gayin","Madachi","Madarmowa","Marma","Tashe"],
 "Kiyawa":["Kiyawa","Andaza","Balago","Fake","Garko","Guruduba","Katanga","Katuka","Kiyawa Gari","Kwanda"],
 "Maigatari":["Maigatari","Balar","Dankumbo","Fulata","Galadi","Jajeri","Kuki","Madaka","Matari","Turbus"],
 "Malam Madori":["Malam Madori","Arki","Dunari","Fateka Akurba","Garun Gabas","Makaddari","Mallam Madori","Tashena","Tagwaro","Tonikutara"],
 "Miga":["Miga","Garbo","Hantsu","Koya","Miga Gari","Sansani","Tsakuwawa","Yanduna","Zareku","Sabon Gari"],
 "Ringim":["Ringim","Dabi","Kyarama","Ringim","Sankara","Sintilmawa","Tofa","Yandutse","Chai Chai","Karshi"],
 "Roni":["Roni","Baragumi","Dansure","Fara","Gora","Kwaita","Roni Gari","Sankara","Tunas","Zugai"],
 "Sule Tankarkar":["Sule Tankarkar","Albasu","Amanga","Bayan Doka","Dangwanki","Danladin","Jeke","Shabaru","Sule","Takatsaba"],
 "Taura":["Taura","Chukuto","Gujungu","Kiri","Kwanar","Majia","Sabon Gari","Taura Gari","Unguwar Tonkari","Yalwa"],
 "Yankwashi":["Yankwashi","Achilafiya","Belas","Dawan Gawo","Gurji","Gwarta","Karkarna","Kuda","Ringim","Zungumba"]
}

def dbc():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    c=dbc()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, created TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, type TEXT, text TEXT, meaning TEXT, file_path TEXT, user TEXT, state TEXT, lga TEXT, ward TEXT, age TEXT, gender TEXT, quality TEXT, duration TEXT, status TEXT, created TEXT)")
    try:
        c.execute("INSERT INTO users VALUES (NULL,'Bulangu','Bulangu123','founder',?)", (datetime.datetime.now().isoformat(),))
        c.commit()
    except: pass
    c.close()
init()

HTML = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="manifest" href="/manifest.json">
<script src="https://cdn.tailwindcss.com"></script>
<title>BULANGU AI LAB V6</title></head>
<body class="bg-gray-100">
<nav class="bg-black text-white p-3 flex justify-between items-center">
<b>🌍 BULANGU AI LAB V6</b><div><span class="text-xs">Founder: Mam Bulangu | {{session_user}}</span> <a href="/logout" class="ml-2 bg-white text-black px-2 py-1 rounded text-xs">Fita</a></div>
</nav>
<div class="max-w-3xl mx-auto p-2">
<div class="grid grid-cols-3 gap-2 mb-3">
<div class="bg-white p-2 rounded shadow text-center">🎙️<br><b>{{v}}</b><br><small>Voices</small></div>
<div class="bg-white p-2 rounded shadow text-center">🖼️<br><b>{{i}}</b><br><small>Images</small></div>
<div class="bg-white p-2 rounded shadow text-center">📜<br><b>{{p}}</b><br><small>Proverbs</small></div>
</div>
<div class="bg-white p-3 rounded shadow">
<div class="flex flex-wrap gap-1 mb-3">
<button onclick="tab('m')" id="btn-m" class="bg-blue-600 text-white px-3 py-2 rounded text-sm">🎤 Murya</button>
<button onclick="tab('h')" id="btn-h" class="bg-gray-200 px-3 py-2 rounded text-sm">🖼️ Hoto</button>
<button onclick="tab('k')" id="btn-k" class="bg-gray-200 px-3 py-2 rounded text-sm">📜 Karin Magana</button>
<button onclick="tab('s')" id="btn-s" class="bg-gray-200 px-3 py-2 rounded text-sm">⚙️ Setting</button>
<button onclick="tab('z')" id="btn-z" class="bg-black text-white px-3 py-2 rounded text-sm">⬇️ ZIP</button>
</div>
<div id="tab-m">
<div class="grid grid-cols-2 gap-2 mb-2">
<select id="state" class="border p-2 rounded text-sm"><option value="">State</option>{% for s in states %}<option>{{s}}</option>{% endfor %}</select>
<select id="lga" onchange="loadWards()" class="border p-2 rounded text-sm"><option>LGA</option></select>
</div>
<div class="grid grid-cols-2 gap-2 mb-2">
<select id="ward" class="border p-2 rounded text-sm"><option>Ward</option></select>
<select id="gender" class="border p-2 rounded text-sm"><option>Mace Tsohuwa 50+ - $2x</option><option>Namiji Tsoho 50+</option><option>Mace 20-49</option><option>Namiji 20-49</option><option>Yaro</option><option>Yarinya</option></select>
</div>
<div class="grid grid-cols-3 gap-2 mb-2">
<input id="age" value="65" class="border p-2 rounded text-sm" placeholder="Age">
<select id="quality" class="border p-2 rounded text-sm"><option>Clear Voice - Daki Shiru 15cm</option><option>With Noise - Kasuwa 50cm</option><option>Phone Call</option><option>Short 2-5s</option><option>Long 60-180s</option></select>
<select id="duration" class="border p-2 rounded text-sm"><option value="15">15 sec</option><option value="5">5 sec</option><option value="60">60 sec</option><option value="180">180 sec</option></select>
</div>
<input id="text" value="Sannu da zuwa Dorawa Babura" class="w-full border p-2 mb-2 rounded text-sm">
<button id="recBtn" onclick="toggleRec()" class="bg-red-600 text-white w-full p-3 rounded font-bold">🔴 FARA RECORDING</button>
<div class="flex justify-between text-xs mt-1"><span id="timer">00:00 / 15s</span><span id="level">🔊 Level: 0%</span></div>
<audio id="audio" controls style="display:none" class="w-full mt-2"></audio>
<button id="saveVoice" style="display:none" onclick="saveVoice()" class="bg-green-600 text-white w-full p-3 rounded mt-2 font-bold">💾 AJIYE MURYA</button>
</div>
<div id="tab-h" style="display:none">
<input type="file" id="img" accept="image/*" class="w-full border p-2 mb-2 rounded text-sm">
<select id="icat" class="w-full border p-2 mb-2 rounded text-sm"><option>Market Crowd</option><option>Farm</option><option>Shop</option><option>Handwriting</option><option>Street</option><option>Food</option></select>
<button onclick="saveImage()" class="bg-blue-600 text-white w-full p-3 rounded">📤 AJIYE HOTO</button>
</div>
<div id="tab-k" style="display:none">
<input id="prov" placeholder="Karin Magana: Zomo baya gudu a banza" class="w-full border p-2 mb-2 rounded text-sm">
<input id="mean" placeholder="Meaning English" class="w-full border p-2 mb-2 rounded text-sm">
<button onclick="saveProv()" class="bg-purple-600 text-white w-full p-3 rounded">AJIYE KARIN MAGANA</button>
</div>
<div id="tab-s" style="display:none"><p class="text-xs">Auto Save - LocalStorage - Har Abada<br>Format: Gender_Age_Ward_Text.webm<br>Offline PWA - Yana aiki ba da internet</p></div>
<div id="tab-z" style="display:none">
<button onclick="location.href='/zip?type=voice'" class="bg-blue-600 text-white w-full p-3 rounded mb-2">⬇️ Voices ZIP</button>
<button onclick="location.href='/zip?type=image'" class="bg-green-600 text-white w-full p-3 rounded mb-2">⬇️ Images ZIP</button>
<button onclick="location.href='/zip?type=proverb'" class="bg-purple-600 text-white w-full p-3 rounded mb-2">⬇️ Proverbs ZIP</button>
<button onclick="location.href='/zip?type=all'" class="bg-black text-white w-full p-3 rounded font-bold">⬇️ DOWNLOAD ALL ZIP</button>
</div>
</div>
<div class="bg-white p-3 rounded shadow mt-3">
<div class="flex gap-2"><input id="search" onkeyup="doSearch()" placeholder="Search Dorawa..." class="flex-1 border p-2 rounded text-sm"><select id="filter" onchange="doSearch()" class="border p-2 rounded text-sm"><option value="">All</option><option>voice</option><option>image</option><option>proverb</option></select></div>
<div class="overflow-auto text-xs mt-2"><table class="w-full" id="dataTable"><tr class="bg-gray-100"><th>Time</th><th>Type</th><th>Wuri</th><th>Text</th><th>Status</th></tr>
{% for r in recs %}<tr class="border-b"><td>{{r['created'][11:16]}}</td><td>{{r['type']}}</td><td>{{r['lga']}}/{{r['ward']}}</td><td>{{r['text'][:20]}}</td><td>{% if session_role=='founder' %}<a href="/approve/{{r['id']}}">✔️</a> <a href="/reject/{{r['id']}}">❌</a>{% else %}{{r['status']}}{% endif %}</td></tr>{% endfor %}
</table></div>
</div>
</div>
<script>
const LGA_WARDS = {{lgas_json}};
function loadStates(){
 let lgaSel=document.getElementById('lga');
 lgaSel.innerHTML='<option>Jigawa LGA 27</option>';
 Object.keys(LGA_WARDS).forEach(l=>{let o=document.createElement('option'); o.value=l; o.textContent=l; lgaSel.appendChild(o);});
 lgaSel.value='Babura'; loadWards();
}
function loadWards(){
 let l=document.getElementById('lga').value;
 let w=document.getElementById('ward');
 w.innerHTML='';
 let wards=LGA_WARDS[l]||['Dorawa'];
 wards.forEach(x=>{let o=document.createElement('option'); o.value=x; o.textContent=x; w.appendChild(o);});
}
function tab(id){
 ['m','h','k','s','z'].forEach(x=>{document.getElementById('tab-'+x).style.display='none'; document.getElementById('btn-'+x).className='bg-gray-200 px-3 py-2 rounded text-sm';});
 document.getElementById('tab-'+id).style.display='block';
 document.getElementById('btn-'+id).className='bg-blue-600 text-white px-3 py-2 rounded text-sm';
 if(id=='z') document.getElementById('btn-z').className='bg-black text-white px-3 py-2 rounded text-sm';
}
let rec,chunks=[],t,sec=0,blob,stream;
async function toggleRec(){ if(!rec||rec.state=='inactive'){startRec()}else{stopRec()} }
async function startRec(){
 sec=0; 
 let dur=parseInt(document.getElementById('duration').value)||15;
 try{
  stream=await navigator.mediaDevices.getUserMedia({audio:true});
  rec=new MediaRecorder(stream); chunks=[];
  rec.ondataavailable=e=>chunks.push(e.data);
  rec.onstop=()=>{
   blob=new Blob(chunks,{type:'audio/webm'});
   let url=URL.createObjectURL(blob);
   document.getElementById('audio').src=url;
   document.getElementById('audio').style.display='block';
   document.getElementById('saveVoice').style.display='block';
   stream.getTracks().forEach(tr=>tr.stop());
  };
  rec.start();
  document.getElementById('recBtn').innerText='⏹️ TSAYA - '+dur+'s';
  t=setInterval(()=>{ sec++; document.getElementById('timer').innerText=`00:${String(sec).padStart(2,'0')} / ${dur}s`; if(sec>=dur) stopRec(); },1000);
 }catch(e){alert('Mic error: '+e);}
}
function stopRec(){ if(rec&&rec.state!='inactive'){rec.stop(); clearInterval(t); document.getElementById('recBtn').innerText='🔴 FARA RECORDING';} }
async function saveVoice(){
 if(!blob) return alert('Yi recording da farko');
 let fd=new FormData(); fd.append('audio',blob,'voice.webm');
 fd.append('state',state.value); fd.append('lga',lga.value); fd.append('ward',ward.value); fd.append('gender',gender.value); fd.append('age',age.value); fd.append('quality',quality.value); fd.append('duration',duration.value); fd.append('text',text.value);
 let r=await fetch('/save_voice',{method:'POST',body:fd}); if(r.ok) location.reload(); else alert('Error');
}
async function saveImage(){
 let f=document.getElementById('img').files[0]; if(!f) return alert('Zabi hoto');
 let fd=new FormData(); fd.append('image',f); fd.append('cat',icat.value); fd.append('state',state.value); fd.append('lga',lga.value); fd.append('ward',ward.value);
 await fetch('/save_image',{method:'POST',body:fd}); location.reload();
}
async function saveProv(){
 let fd=new FormData(); fd.append('text',prov.value); fd.append('meaning',mean.value); fd.append('state',state.value); fd.append('lga',lga.value); fd.append('ward',ward.value);
 await fetch('/save_proverb',{method:'POST',body:fd}); location.reload();
}
function doSearch(){
 let q=document.getElementById('search').value.toLowerCase();
 let f=document.getElementById('filter').value.toLowerCase();
 document.querySelectorAll('#dataTable tr').forEach((tr,i)=>{if(i==0) return; let txt=tr.innerText.toLowerCase(); tr.style.display=txt.includes(q) && (f==''||txt.includes(f))?'':'none';});
}
loadStates();
</script></body></html>
"""

@app.route('/manifest.json')
def manifest(): return jsonify({"name":"Bulangu AI Lab V6","short_name":"BulanguLab","start_url":"/","display":"standalone","background_color":"#000000","theme_color":"#000000"})
@app.route('/sw.js')
def sw(): return """self.addEventListener('install',e=>{self.skipWaiting()});self.addEventListener('fetch',e=>{e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)))})""", 200, {'Content-Type':'application/javascript'}
@app.route('/')
def home(): 
    if 'user' not in session: return redirect('/login')
    return redirect('/dashboard')
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=request.form['username']; p=request.form['password']
        c=dbc(); r=c.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone(); c.close()
        if r:
            session['user']=r['username']; session['role']=r['role']; session['uid']=r['id']
            return redirect('/dashboard')
        return "Login kuskure - Bulangu / Bulangu123"
    return render_template_string("""<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-black text-white flex items-center justify-center min-h-screen"><div class="bg-white text-black p-6 rounded shadow max-w-sm w-full"><h2 class="font-bold text-center">🌍 BULANGU AI LAB V6<br><small>Founder Login</small></h2><form method="POST" class="mt-4"><input name="username" placeholder="Bulangu" class="w-full border p-3 mb-2 rounded"><input name="password" type="password" placeholder="Bulangu123" class="w-full border p-3 mb-2 rounded"><button class="bg-black text-white w-full p-3 rounded">Shiga</button></form></div></body></html>""")
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        u=request.form['username']; p=request.form['password']
        c=dbc()
        try:
            c.execute("INSERT INTO users (username,password,role,created) VALUES (?,?,?,?)",(u,p,'collector',datetime.datetime.now().isoformat()))
            c.commit(); c.close(); return redirect('/login')
        except: c.close(); return "Username ya wanzu"
    return render_template_string("""<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-100 flex items-center justify-center min-h-screen"><div class="bg-white p-6 rounded shadow max-w-sm w-full"><h2 class="font-bold">Register</h2><form method="POST" class="mt-4"><input name="username" placeholder="Sunanka" class="w-full border p-3 mb-2 rounded"><input name="password" type="password" placeholder="Password" class="w-full border p-3 mb-2 rounded"><button class="bg-blue-600 text-white w-full p-3 rounded">Register</button></form></div></body></html>""")
@app.route('/dashboard')
def dash():
    if 'user' not in session: return redirect('/login')
    c=dbc()
    recs=c.execute("SELECT * FROM records ORDER BY id DESC LIMIT 200").fetchall()
    v=c.execute("SELECT COUNT(*) FROM records WHERE type='voice'").fetchone()[0]
    i=c.execute("SELECT COUNT(*) FROM records WHERE type='image'").fetchone()[0]
    p=c.execute("SELECT COUNT(*) FROM records WHERE type='proverb'").fetchone()[0]
    users=c.execute("SELECT * FROM users").fetchall()
    c.close()
    return render_template_string(HTML, v=v, i=i, p=p, recs=recs, users=users, states=NIGERIA_STATES, lgas_json=json.dumps(JIGAWA_LGAS), session_user=session.get('user'), session_role=session.get('role'))
@app.route('/save_voice', methods=['POST'])
def sv():
    if 'user' not in session: return "unauth",401
    f=request.files['audio']
    name=f"{request.form.get('gender','Mace')}_{request.form.get('age','65')}y_{request.form.get('ward','Dorawa')}_{request.form.get('text','Sannu')}.webm".replace(' ','_')[:50]
    path=os.path.join(BASE, "voices", secure_filename(name)); f.save(path)
    c=dbc(); c.execute("INSERT INTO records (type,text,file_path,user,state,lga,ward,age,gender,quality,duration,status,created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ('voice',request.form.get('text'),path,session['user'],request.form.get('state'),request.form.get('lga'),request.form.get('ward'),request.form.get('age'),request.form.get('gender'),request.form.get('quality'),request.form.get('duration'),'pending',datetime.datetime.now().isoformat())); c.commit(); c.close(); return "ok"
@app.route('/save_image', methods=['POST'])
def si():
    if 'user' not in session: return "unauth",401
    f=request.files['image']; path=os.path.join(BASE, "images", secure_filename(f.filename)); f.save(path)
    c=dbc(); c.execute("INSERT INTO records (type,text,file_path,user,state,lga,ward,status,created) VALUES (?,?,?,?,?,?,?,?)", ('image',request.form.get('cat'),path,session['user'],request.form.get('state'),request.form.get('lga'),request.form.get('ward'),'pending',datetime.datetime.now().isoformat())); c.commit(); c.close(); return "ok"
@app.route('/save_proverb', methods=['POST'])
def sp():
    if 'user' not in session: return "unauth",401
    c=dbc(); c.execute("INSERT INTO records (type,text,meaning,user,state,lga,ward,status,created) VALUES (?,?,?,?,?,?,?,?)", ('proverb',request.form.get('text'),request.form.get('meaning'),session['user'],request.form.get('state'),request.form.get('lga'),request.form.get('ward'),'pending',datetime.datetime.now().isoformat())); c.commit(); c.close(); return "ok"
@app.route('/approve/<int:id>')
def approve(id):
    if session.get('role')!='founder': return "admin only"
    c=dbc(); c.execute("UPDATE records SET status='approved' WHERE id=?",(id,)); c.commit(); c.close(); return redirect('/dashboard')
@app.route('/reject/<int:id>')
def reject(id):
    if session.get('role')!='founder': return "admin only"
    c=dbc(); c.execute("DELETE FROM records WHERE id=?",(id,)); c.commit(); c.close(); return redirect('/dashboard')
@app.route('/clear')
def clear():
    if session.get('role')!='founder': return "admin only"
    c=dbc(); c.execute("DELETE FROM records"); c.commit(); c.close(); return redirect('/dashboard')
@app.route('/zip')
def z():
    t=request.args.get('type','all'); mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w') as zf:
        c=dbc(); rows=c.execute("SELECT * FROM records").fetchall(); c.close()
        for r in rows:
            if t!='all' and t not in r['type']: continue
            if r['file_path'] and os.path.exists(r['file_path']):
                arc=f"{r['type']}s/{os.path.basename(r['file_path'])}"
                zf.write(r['file_path'], arc)
            meta=json.dumps(dict(r), indent=2, default=str, ensure_ascii=False)
            zf.writestr(f"metadata/{r['type']}_{r['id']}.json", meta)
        zf.writestr("README.txt", f"BULANGU AI LAB V6 - Founder Mam Bulangu - Dorawa\nTotal: {len(rows)}")
    mem.seek(0); return send_file(mem, download_name=f"bulangu_v6_{t}.zip", as_attachment=True)
@app.route('/logout')
def lo(): session.clear(); return redirect('/login')
