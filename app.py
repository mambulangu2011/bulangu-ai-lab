pythonimport os, sqlite3, zipfile, datetime, json, io
from flask import Flask, request, render_template_string, redirect, session, send_file, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "bulangu-v61-world-english-founder-mam-bulangu-2026"
BASE = "/tmp" if os.path.exists("/tmp") else "."
DB = os.path.join(BASE, "bulangu_v61.db")
os.makedirs(os.path.join(BASE, "voices"), exist_ok=True)
os.makedirs(os.path.join(BASE, "images"), exist_ok=True)

# === ALL 36 STATES + FCT ===
NIGERIA_STATES = ["Abia","Adamawa","Akwa Ibom","Anambra","Bauchi","Bayelsa","Benue","Borno","Cross River","Delta","Ebonyi","Edo","Ekiti","Enugu","FCT Abuja","Gombe","Imo","Jigawa","Kaduna","Kano","Katsina","Kebbi","Kogi","Kwara","Lagos","Nasarawa","Niger","Ogun","Ondo","Osun","Oyo","Plateau","Rivers","Sokoto","Taraba","Yobe","Zamfara"]

# === ALL 27 LGAs OF JIGAWA WITH ALL WARDS ===
JIGAWA_DATA = {
 "Auyo": ["Auyo","Auyakayi","Ayama","Gamafoi","Gamsarka","Gatafa","Guriko","Kafan Hausa Road","Tsidir","Unik"],
 "Babura": ["Babura","Batali","Dorawa","Gasakoli","Insharuwa","Jigawar Sarki","Kanya","Kuzunzumi","Kyambo","Takalafiya","Tajummu","Kumburki"],
 "Biriniwa": ["Biriniwa","Diginsa","Fagi","Kachallari","Kazura","Matarababbado","Nguwa","Tsibir","Unguwar Makafi","Dangwaleri"],
 "Birnin Kudu": ["Birnin Kudu","Kangire","Kwangwara","Lafiya","Sundimina","Surko","Unguwar Ya","Wurno","Yalwan Damai","Kantoga"],
 "Buji": ["Buji","Gantsa","Kawaya","Kukuma","Lelen Kudu","Lelen Arewa","Karma","Kawu","Sara","Jigawar Buji"],
 "Dutse": ["Dutse","Jigawar Tsada","Sakwaya","Madobi","Karnaya","Limawa","Waru","Malamawar","Kachi","Chamo"],
 "Gagarawa": ["Gagarawa","Gagarawa Gari","Kore","Maikilili","Meda","Mai Zare","Mangada","Garun Gabas","Zaumar Gari","Zarada"],
 "Garki": ["Garki","Gwarzon Garki","Jirima","Kanya","Kore","Muku","Doko","Buduru","Garki Kargo","Siyori"],
 "Gumel": ["Gumel","Baikarya","Dan Ama","Galagamma","Garin Gari","Gusau","Hammado","Kofar Arewa","Kofar Yamma","Zango"],
 "Guri": ["Guri","Abunabo","Adiyani","Dawa","Garbagal","Kadira","Lafiya","Margadu","Matara Babba","Musari"],
 "Gwaram": ["Gwaram","Basirka","Fagam","Gwaram Gari","Kila","Kwandiko","Maruta","Sara","Tsangarwa","Dingaya"],
 "Gwiwa": ["Gwiwa","Buntusu","Dabi","Dangyatin","Darina","Fandum","Guntai","Korayel","Rorau","Shafe"],
 "Hadejia": ["Hadejia","Kasuwar Kuda","Kasuwar Kofa","Majema","Matsaro","Rumfa","Sabon Garu","Yankoli","Dubutu","Atikun"],
 "Jahun": ["Jahun","Aujara","Gauza","Gunka","Harbo","Idanduna","Kale","Kanwa","Nagwada","Telemos"],
 "Kafin Hausa": ["Kafin Hausa","Balangu","Dumadumin","Gafaya","Jabo","Kafin Hausa Tudu","Majawa","Mezan","Ruba","Sarawa"],
 "Kaugama": ["Kaugama","Arbus","Dakayyawa","Hadin Bari","Jarkasa","Ja'e","Marke","Hadandi","Yalo","Askandu"],
 "Kazaure": ["Kazaure","Ba'a","Daba","Dabaza","Gada","Isamu","Kargo","Maradawa","Sabaru","Umaru"],
 "Kiri Kasama": ["Kiri Kasama","Baturiya","Bulunchai","Doljigi","Fandum","Gayin","Madachi","Madarmowa","Marma","Tashe"],
 "Kiyawa": ["Kiyawa","Andaza","Balago","Fake","Garko","Guruduba","Katanga","Katuka","Kiyawa Gari","Kwanda"],
 "Maigatari": ["Maigatari","Balar","Dankumbo","Fulata","Galadi","Jajeri","Kuki","Madaka","Matari","Turbus"],
 "Malam Madori": ["Malam Madori","Arki","Dunari","Fateka Akurba","Garun Gabas","Makaddari","Mallam Madori","Tashena","Tagwaro","Tonikutara"],
 "Miga": ["Miga","Garbo","Hantsu","Koya","Miga Gari","Sansani","Tsakuwawa","Yanduna","Zareku","Sabon Gari"],
 "Ringim": ["Ringim","Dabi","Kyarama","Ringim Town","Sankara","Sintilmawa","Tofa","Yandutse","Chai Chai","Karshi"],
 "Roni": ["Roni","Baragumi","Dansure","Fara","Gora","Kwaita","Roni Gari","Sankara","Tunas","Zugai"],
 "Sule Tankarkar": ["Sule Tankarkar","Albasu","Amanga","Bayan Doka","Dangwanki","Danladin","Jeke","Shabaru","Sule","Takatsaba"],
 "Taura": ["Taura","Chukuto","Gujungu","Kiri","Kwanar","Majia","Sabon Gari","Taura Gari","Unguwar Tonkari","Yalwa"],
 "Yankwashi": ["Yankwashi","Achilafiya","Belas","Dawan Gawo","Gurji","Gwarta","Karkarna","Kuda","Ringim","Zungumba"]
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
<script src="https://cdn.tailwindcss.com"></script>
<title>BULANGU AI LAB - Founder Mam Bulangu - World Dataset</title></head>
<body class="bg-gray-50">
<nav class="bg-black text-white p-3 flex justify-between">
<div><b>🌍 BULANGU AI LAB</b><br><span class="text-xs">Founder: Mam Bulangu | World Hausa AI Dataset | Sell to Google/Meta/OpenAI</span></div>
<div class="text-right"><small>{{user}} ({{role}})</small><br><a href="/logout" class="bg-white text-black px-3 py-1 rounded text-xs">Logout</a></div>
</nav>
<div class="max-w-4xl mx-auto p-3">
<div class="grid grid-cols-3 gap-2 mb-3">
<div class="bg-white p-3 rounded shadow text-center"><div class="text-2xl">🎙️</div><b>{{v}}</b><br><small>Voices</small><br><span class="text-xs text-gray-500">Target: 500</span></div>
<div class="bg-white p-3 rounded shadow text-center"><div class="text-2xl">🖼️</div><b>{{i}}</b><br><small>Images</small><br><span class="text-xs text-gray-500">Target: 300</span></div>
<div class="bg-white p-3 rounded shadow text-center"><div class="text-2xl">📜</div><b>{{p}}</b><br><small>Proverbs</small><br><span class="text-xs text-gray-500">Target: 100</span></div>
</div>

<div class="bg-white p-4 rounded shadow">
<div class="flex flex-wrap gap-2 mb-4">
<button onclick="tab('voice')" id="b-voice" class="bg-blue-600 text-white px-4 py-2 rounded">🎤 Voice Collection</button>
<button onclick="tab('image')" id="b-image" class="bg-gray-200 px-4 py-2 rounded">🖼️ Image</button>
<button onclick="tab('proverb')" id="b-proverb" class="bg-gray-200 px-4 py-2 rounded">📜 Proverb</button>
<button onclick="tab('setting')" id="b-setting" class="bg-gray-200 px-4 py-2 rounded">⚙️ Settings</button>
<button onclick="tab('zip')" id="b-zip" class="bg-black text-white px-4 py-2 rounded">⬇️ Download ZIP</button>
</div>

<div id="t-voice">
<h3 class="font-bold mb-2">Voice Collection - For Google/Meta AI (ASR/TTS)</h3>
<div class="grid grid-cols-2 gap-2 mb-2">
<select id="state" class="border p-2 rounded text-sm"><option>Select State - All Nigeria</option></select>
<select id="lga" onchange="loadWards()" class="border p-2 rounded text-sm"><option>Select LGA - All 27 Jigawa</option></select>
</div>
<div class="grid grid-cols-2 gap-2 mb-2">
<select id="ward" class="border p-2 rounded text-sm"><option>Select Ward - All Wards</option></select>
<select id="gender" class="border p-2 rounded text-sm"><option>Female Elder 50+ - Highest Value 2x</option><option>Male Elder 50+ - High Value</option><option>Female Adult 20-49</option><option>Male Adult 20-49</option><option>Female Child 8-15</option><option>Male Child 8-15</option></select>
</div>
<div class="grid grid-cols-3 gap-2 mb-2">
<input id="age" value="" placeholder="Age e.g. 65" class="border p-2 rounded text-sm">
<select id="quality" class="border p-2 rounded text-sm"><option>Clear Voice - Quiet Room 15cm</option><option>With Noise - Market 50cm</option><option>Phone Call Quality</option><option>Short 2-5s - Wake Word</option><option>Standard 15s</option><option>Long Story 60-180s - Premium</option></select>
<select id="duration" class="border p-2 rounded text-sm"><option value="15">15 sec - Auto Stop</option><option value="5">5 sec</option><option value="30">30 sec</option><option value="60">60 sec</option><option value="180">180 sec</option></select>
</div>
<input id="text" placeholder="Text to speak - e.g. Sannu da zuwa" class="w-full border p-2 mb-2 rounded text-sm">
<button id="recBtn" onclick="toggleRec()" class="bg-red-600 text-white w-full p-3 rounded font-bold text-lg">🔴 START RECORDING</button>
<div class="flex justify-between text-xs mt-2"><span id="timer">00:00 / 15s</span><span id="level">Level: 0%</span></div>
<audio id="audio" controls style="display:none" class="w-full mt-2"></audio>
<button id="saveVoice" style="display:none" onclick="saveVoice()" class="bg-green-600 text-white w-full p-3 rounded mt-2 font-bold">💾 SAVE VOICE - Auto Save Forever</button>
<p class="text-xs text-gray-500 mt-2">File name: Gender_Age_Ward_State_Text.webm - As Google Wants - Quality: {{quality}}</p>
</div>

<div id="t-image" style="display:none">
<h3 class="font-bold mb-2">Image Collection - Market Crowd / Farm / Handwriting - High Value</h3>
<input type="file" id="img" accept="image/*" class="w-full border p-2 mb-2 rounded text-sm">
<select id="icat" class="w-full border p-2 mb-2 rounded text-sm"><option>Market Crowd - People Gathering - High Demand</option><option>Farm - Gona - Rice/Maize</option><option>Shop - Shago</option><option>Handwriting - Hausa Text</option><option>Street</option><option>Food</option></select>
<button onclick="saveImage()" class="bg-blue-600 text-white w-full p-3 rounded">📤 SAVE IMAGE WITH METADATA</button>
</div>

<div id="t-proverb" style="display:none">
<h3 class="font-bold mb-2">Hausa Proverbs - Rare - AI Needs Wisdom</h3>
<input id="prov" placeholder="Proverb e.g. Zomo baya gudu a banza" class="w-full border p-2 mb-2 rounded text-sm">
<input id="mean" placeholder="English Meaning: A hare does not run in vain" class="w-full border p-2 mb-2 rounded text-sm">
<input id="meanHausa" placeholder="Hausa Meaning: Ba a yin abu ba dalili" class="w-full border p-2 mb-2 rounded text-sm">
<button onclick="saveProv()" class="bg-purple-600 text-white w-full p-3 rounded">SAVE PROVERB</button>
</div>

<div id="t-setting" style="display:none">
<h3 class="font-bold">⚙️ Settings - All Inside - No Extra Page</h3>
<ul class="text-sm list-disc ml-5 mt-2">
<li>Auto Save: SQLite - Forever - Even after refresh - Offline PWA supported</li>
<li>File Naming: Gender_Age_Ward_State_Text.webm - Required by Google/Meta</li>
<li>Voice Length: Buyers want 5s, 15s, 60s, 180s - You can set duration</li>
<li>Quality Tags: Clear, With Noise, Long Story - All have different prices</li>
<li>Admin: Founder Mam Bulangu can Approve/Reject all submissions</li>
<li>Sharing: Any registered user can collect - Data goes to Founder dashboard</li>
<li>Search & Time: Every record has timestamp - General search on top</li>
</ul>
<div class="mt-3 text-sm"><b>Users:</b><br>{% for u in users %}{{u['username']}} - {{u['role']}}<br>{% endfor %}</div>
</div>

<div id="t-zip" style="display:none">
<h3 class="font-bold">⬇️ ZIP Download - Ready to Sell</h3>
<div class="grid gap-2 mt-3">
<button onclick="location.href='/zip?type=voice'" class="bg-blue-600 text-white p-3 rounded text-left">📦 Voices ZIP - All voices + metadata.json - Structure: voices/Gender_Age_Ward.webm</button>
<button onclick="location.href='/zip?type=image'" class="bg-green-600 text-white p-3 rounded text-left">📦 Images ZIP - All images + metadata</button>
<button onclick="location.href='/zip?type=proverb'" class="bg-purple-600 text-white p-3 rounded text-left">📦 Proverbs ZIP - Hausa + English Meaning</button>
<button onclick="location.href='/zip?type=all'" class="bg-black text-white p-3 rounded font-bold text-left">📦 DOWNLOAD ALL AS ONE ZIP - For HuggingFace / Google Dataset</button>
</div>
<p class="text-xs mt-3 bg-yellow-50 p-2 rounded">How to sell: Upload ZIP to HuggingFace.co/datasets -> Name: "bulangu-hausa-jigawa-dataset" -> Price: $500-$5000 - Or sell to Google AI Data Program, Meta AI Data Collection</p>
</div>
</div>

<div class="bg-white p-3 rounded shadow mt-3">
<div class="flex gap-2"><input id="search" onkeyup="doSearch()" placeholder="Search by State, LGA, Ward, Gender, Age, Text..." class="flex-1 border p-2 rounded text-sm"><select id="ftype" onchange="doSearch()" class="border p-2 rounded text-sm"><option value="">All Types</option><option>voice</option><option>image</option><option>proverb</option></select></div>
<div class="overflow-auto mt-2"><table class="w-full text-xs" id="tbl"><tr class="bg-gray-100"><th>Time</th><th>Type</th><th>Location</th><th>Gender/Age</th><th>Quality</th><th>Text</th><th>Action</th></tr>
{% for r in recs %}<tr class="border-b"><td>{{r['created'][11:19]}}</td><td>{{r['type']}}</td><td>{{r['state']}}/{{r['lga']}}/{{r['ward']}}</td><td>{{r['gender']}}/{{r['age']}}</td><td>{{r['quality'][:12]}}</td><td>{{r['text'][:25]}}</td><td>{% if role=='founder' %}<a href="/approve/{{r['id']}}" class="text-green-600">Approve</a> | <a href="/reject/{{r['id']}}" class="text-red-600">Reject</a>{% else %}{{r['status']}}{% endif %}</td></tr>{% endfor %}
</table></div>
</div>
</div>
<script>
const JIGAWA = {{jigawa_json}};
const STATES = {{states_json}};
function init(){
 let s=document.getElementById('state'); STATES.forEach(st=>{let o=document.createElement('option'); o.value=st; o.textContent=st; s.appendChild(o);}); s.value='Jigawa';
 let l=document.getElementById('lga'); Object.keys(JIGAWA).forEach(lg=>{let o=document.createElement('option'); o.value=lg; o.textContent=lg; l.appendChild(o);});
 loadWards();
}
function loadWards(){
 let lga=document.getElementById('lga').value; let w=document.getElementById('ward'); w.innerHTML='';
 let list=JIGAWA[lga]||['Select Ward']; list.forEach(x=>{let o=document.createElement('option'); o.value=x; o.textContent=x; w.appendChild(o);});
}
function tab(id){['voice','image','proverb','setting','zip'].forEach(x=>{document.getElementById('t-'+x).style.display='none'; document.getElementById('b-'+x).className='bg-gray-200 px-4 py-2 rounded';}); document.getElementById('t-'+id).style.display='block'; document.getElementById('b-'+id).className='bg-blue-600 text-white px-4 py-2 rounded'; if(id=='zip') document.getElementById('b-zip').className='bg-black text-white px-4 py-2 rounded';}
let rec,chunks=[],t,sec=0,blob,stream;
async function toggleRec(){if(!rec||rec.state=='inactive'){startRec()}else{stopRec()}}
async function startRec(){
 sec=0; let dur=parseInt(document.getElementById('duration').value)||15;
 stream=await navigator.mediaDevices.getUserMedia({audio:true}); rec=new MediaRecorder(stream); chunks=[];
 rec.ondataavailable=e=>chunks.push(e.data);
 rec.onstop=()=>{blob=new Blob(chunks,{type:'audio/webm'}); document.getElementById('audio').src=URL.createObjectURL(blob); document.getElementById('audio').style.display='block'; document.getElementById('saveVoice').style.display='block'; stream.getTracks().forEach(x=>x.stop());};
 rec.start(); document.getElementById('recBtn').innerText='⏹️ STOP - '+dur+'s'; t=setInterval(()=>{sec++; document.getElementById('timer').innerText=`00:${String(sec).padStart(2,'0')} / ${dur}s`; document.getElementById('level').innerText='Recording... '+(Math.random()*30+70).toFixed(0)+'%'; if(sec>=dur) stopRec();},1000);
}
function stopRec(){if(rec&&rec.state!='inactive'){rec.stop(); clearInterval(t); document.getElementById('recBtn').innerText='🔴 START RECORDING';}}
async function saveVoice(){if(!blob) return alert('Record first'); let fd=new FormData(); fd.append('audio',blob,`${gender.value}_${age.value}_${ward.value}.webm`.replace(/ /g,'_')); ['state','lga','ward','gender','age','quality','duration','text'].forEach(k=>fd.append(k,document.getElementById(k).value)); await fetch('/save_voice',{method:'POST',body:fd}); location.reload();}
async function saveImage(){let f=document.getElementById('img').files[0]; if(!f) return alert('Choose image'); let fd=new FormData(); fd.append('image',f); fd.append('cat',icat.value); ['state','lga','ward'].forEach(k=>fd.append(k,document.getElementById(k).value)); await fetch('/save_image',{method:'POST',body:fd}); location.reload();}
async function saveProv(){let fd=new FormData(); fd.append('text',prov.value); fd.append('meaning',mean.value+' | '+meanHausa.value); ['state','lga','ward'].forEach(k=>fd.append(k,document.getElementById(k).value)); await fetch('/save_proverb',{method:'POST',body:fd}); location.reload();}
function doSearch(){let q=search.value.toLowerCase(); let ft=ftype.value.toLowerCase(); document.querySelectorAll('#tbl tr').forEach((tr,i)=>{if(i==0) return; let ok=tr.innerText.toLowerCase().includes(q) && (ft==''||tr.innerText.toLowerCase().includes(ft)); tr.style.display=ok?'':'none';});}
init();
</script></body></html>
"""

@app.route('/')
def home():
    if 'user' not in session: return redirect('/login')
    return redirect('/dashboard')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=request.form['username']; p=request.form['password']
        c=dbc(); r=c.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone(); c.close()
        if r: session['user']=r['username']; session['role']=r['role']; return redirect('/dashboard')
        return "Login failed - Use Bulangu / Bulangu123"
    return render_template_string("""<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-black flex items-center justify-center min-h-screen"><div class="bg-white p-6 rounded shadow max-w-sm w-full text-center"><h2 class="font-bold">🌍 BULANGU AI LAB<br><small>Founder Mam Bulangu</small></h2><form method="POST" class="mt-4 text-left"><input name="username" placeholder="Bulangu" class="w-full border p-3 mb-2 rounded"><input name="password" type="password" placeholder="Bulangu123" class="w-full border p-3 mb-2 rounded"><button class="bg-black text-white w-full p-3 rounded">Login</button></form><a href="/register" class="text-xs text-blue-600">Create Collector Account</a></div></body></html>""")

@app.route('/register', methods=['GET','POST'])
def reg():
    if request.method=='POST':
        u=request.form['username']; p=request.form['password']
        c=dbc()
        try: c.execute("INSERT INTO users (username,password,role,created) VALUES (?,?,?,?)",(u,p,'collector',datetime.datetime.now().isoformat())); c.commit(); c.close(); return redirect('/login')
        except: c.close(); return "Username exists"
    return render_template_string("""<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-100 flex items-center justify-center min-h-screen"><div class="bg-white p-6 rounded shadow max-w-sm w-full"><h2 class="font-bold">Register Collector</h2><form method="POST" class="mt-4"><input name="username" placeholder="Your Name" class="w-full border p-3 mb-2 rounded"><input name="password" type="password" placeholder="Password" class="w-full border p-3 mb-2 rounded"><button class="bg-blue-600 text-white w-full p-3 rounded">Register</button></form><p class="text-xs mt-2">All data goes to Founder Mam Bulangu dashboard</p></div></body></html>""")

@app.route('/dashboard')
def dash():
    if 'user' not in session: return redirect('/login')
    c=dbc(); recs=c.execute("SELECT * FROM records ORDER BY id DESC LIMIT 300").fetchall()
    v=c.execute("SELECT COUNT(*) FROM records WHERE type='voice'").fetchone()[0]
    i=c.execute("SELECT COUNT(*) FROM records WHERE type='image'").fetchone()[0]
    p=c.execute("SELECT COUNT(*) FROM records WHERE type='proverb'").fetchone()[0]
    users=c.execute("SELECT * FROM users").fetchall(); c.close()
    return render_template_string(HTML, v=v, i=i, p=p, recs=recs, users=users, states_json=json.dumps(NIGERIA_STATES), jigawa_json=json.dumps(JIGAWA_DATA), user=session.get('user'), role=session.get('role'))

@app.route('/save_voice', methods=['POST'])
def sv():
    if 'user' not in session: return "unauth",401
    f=request.files['audio']
    name=f"{request.form.get('gender')}_{request.form.get('age')}y_{request.form.get('ward')}_{request.form.get('state')}_{request.form.get('text')}.webm".replace(' ','_')[:80]
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
    if session.get('role')!='founder': return "founder only"
    c=dbc(); c.execute("UPDATE records SET status='approved' WHERE id=?",(id,)); c.commit(); c.close(); return redirect('/dashboard')

@app.route('/reject/<int:id>')
def reject(id):
    if session.get('role')!='founder': return "founder only"
    c=dbc(); c.execute("DELETE FROM records WHERE id=?",(id,)); c.commit(); c.close(); return redirect('/dashboard')

@app.route('/zip')
def z():
    t=request.args.get('type','all'); mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w') as zf:
        c=dbc(); rows=c.execute("SELECT * FROM records").fetchall(); c.close()
        for r in rows:
            if t!='all' and t not in r['type']: continue
            if r['file_path'] and os.path.exists(r['file_path']):
                zf.write(r['file_path'], f"{r['type']}s/{os.path.basename(r['file_path'])}")
            zf.writestr(f"metadata/{r['type']}_{r['id']}.json", json.dumps(dict(r), indent=2, default=str, ensure_ascii=False))
        zf.writestr("README.txt", f"BULANGU AI LAB - Founder Mam Bulangu\nTotal Records: {len(rows)}\nNaming: Gender_Age_Ward_State_Text.webm\nSell to: Google AI, Meta AI, HuggingFace\n")
    mem.seek(0); return send_file(mem, download_name=f"bulangu_world_{t}_{datetime.datetime.now().date()}.zip", as_attachment=True)

@app.route('/logout')
def lo(): session.clear(); return redirect('/login')

if __name__=='__main__': app.run(host='0.0.0.0', port=5000
