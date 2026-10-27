import os, sqlite3, zipfile, datetime, json, io
from flask import Flask, request, render_template_string, redirect, session, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "bulangu-final-2026"
os.makedirs("data/voices", exist_ok=True)
os.makedirs("data/images", exist_ok=True)

def get_db():
    db = sqlite3.connect("bulangu_final.db")
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, created TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, type TEXT, file_path TEXT, text_content TEXT, username TEXT, state TEXT, lga TEXT, ward TEXT, age INTEGER, gender TEXT, quality TEXT, duration TEXT, status TEXT, created TEXT, consent INTEGER)")
    try:
        db.execute("INSERT INTO users (username,password,role,created) VALUES (?,?,?,?)", ("Bulangu","Bulangu123","founder", datetime.datetime.now().isoformat()))
        db.commit()
    except: pass
    db.close()
init_db()

HTML_PAGE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.tailwindcss.com"></script><title>BULANGU AI LAB</title></head>
<body class="bg-slate-50">
<nav class="bg-black text-white p-3 flex justify-between">
<b>BULANGU AI LAB - Founder Bulangu</b>
<div><a href="/admin" class="mr-3">Admin</a><a href="/logout">Fita</a></div>
</nav>
<div class="max-w-5xl mx-auto p-3">
<div class="bg-white p-4 rounded shadow mb-3 grid grid-cols-3 gap-2 text-center text-sm">
<div>Voices: <b>{{v}}</b></div><div>Images: <b>{{i}}</b></div><div>Proverbs: <b>{{p}}</b></div>
<div class="col-span-3 text-xs text-gray-600">Min Sale: Voice 500, Image 300, Proverb 100 | 1 person = 20 words different | 25 x 20 = 500 | 20 people can say same Sannu - allowed</div>
</div>
<div class="bg-white p-4 rounded shadow mb-3">
<div class="flex gap-2 mb-3">
<button onclick="show('voice')" class="bg-blue-600 text-white px-3 py-2 rounded text-sm">Murya</button>
<button onclick="show('image')" class="bg-gray-200 px-3 py-2 rounded text-sm">Hoto</button>
<button onclick="show('proverb')" class="bg-gray-200 px-3 py-2 rounded text-sm">Karin Magana</button>
<button onclick="show('setting')" class="bg-gray-200 px-3 py-2 rounded text-sm">ZIP</button>
</div>
<div id="voice">
<div class="grid md:grid-cols-2 gap-2">
<select id="state" class="border p-2 rounded"></select>
<select id="lga" class="border p-2 rounded"></select>
<select id="ward" class="border p-2 rounded"></select>
<select id="gender" class="border p-2 rounded">
<option value="female_elderly">Mace Tsohuwa 50+ - Mafi Daraja 2x</option>
<option value="male_elderly">Namiji Tsoho 60+ - Daraja</option>
<option value="child_female">Yarinya 8-15 - Daraja</option>
<option value="child_male">Yaro 8-15 - Daraja</option>
<option value="female_young">Mace Matashiya 20-40</option>
<option value="male_young">Namiji Matashi 20-40</option>
</select>
<input id="age" type="number" placeholder="Shekaru - misali 65" class="border p-2 rounded">
<select id="quality" class="border p-2 rounded">
<option>Clear Voice - Daki Shiru - 15-30cm</option>
<option>With Noise - Kasuwa - 40-50cm</option>
<option>Short Command - 3 sec - Same word many people can say</option>
<option>Long Story - 2 min Labari</option>
<option>Market Crowd - Taro</option>
</select>
<input id="duration" type="number" value="5" class="border p-2 rounded">
<input id="text" value="Sannu" class="border p-2 rounded md:col-span-2" placeholder="Kalma - Sannu, Ina kwana - 20 people can say same">
</div>
<div class="mt-2 bg-yellow-50 p-2 rounded text-xs"><input type="checkbox" id="consent" checked> Yarda - Consent | Nisa: 15-30cm clear, 40-50cm market | 5 words per person minimum ok</div>
<button id="recBtn" onclick="toggleRec()" class="bg-red-600 text-white w-full p-3 rounded font-bold mt-2">Fara Recording</button>
<p id="timer" class="text-center text-sm">00:00 / <span id="target">5</span>s</p>
<audio id="audio" controls style="display:none" class="w-full"></audio>
<button id="saveV" style="display:none" onclick="saveVoice()" class="bg-green-600 text-white w-full p-3 rounded mt-2">Ajiye - Har Abada</button>
</div>
<div id="image" style="display:none">
<input type="file" id="imgFile" accept="image/*" class="w-full border p-2 rounded">
<select id="imgCat" class="w-full border p-2 rounded mt-2"><option>Market Crowd</option><option>Farm</option><option>Shop</option><option>Face With Consent</option><option>Handwriting Hausa</option></select>
<button onclick="saveImage()" class="bg-blue-600 text-white w-full p-3 rounded mt-2">Ajiye Hoto + Metadata</button>
</div>
<div id="proverb" style="display:none">
<input id="provText" placeholder="Karin Magana - Zomo baya gudu a banza" class="w-full border p-2 rounded">
<input id="provMean" placeholder="Ma'anarsa Turanci" class="w-full border p-2 rounded mt-2">
<button onclick="saveProv()" class="bg-purple-600 text-white w-full p-3 rounded mt-2">Ajiye Karin Magana</button>
</div>
<div id="setting" style="display:none">
<p class="text-sm">Auto Save: SQLite forever. File name: gender_age_ward_text.webm + metadata.json<br>Min Sale: Voice 500, Image 300, Proverb 100</p>
<button onclick="location.href='/zip?type=all'" class="bg-black text-white w-full p-3 rounded mt-3">DOWNLOAD ALL ZIP</button>
<div class="grid grid-cols-3 gap-2 mt-2">
<button onclick="location.href='/zip?type=voice'" class="bg-gray-700 text-white p-2 rounded">Zip Voices</button>
<button onclick="location.href='/zip?type=image'" class="bg-gray-700 text-white p-2 rounded">Zip Images</button>
<button onclick="location.href='/zip?type=proverb'" class="bg-gray-700 text-white p-2 rounded">Zip Proverbs</button>
</div>
</div>
</div>
<div class="bg-white p-3 rounded shadow">
<input id="search" onkeyup="doSearch()" placeholder="Search: Dorawa, female_elderly, Sannu..." class="w-full border p-2 rounded mb-2">
<div style="max-height:350px; overflow:auto">
<table class="w-full text-xs"><tr class="bg-gray-100"><th>Time</th><th>User</th><th>Type</th><th>State/LGA/Ward/Age/Gender</th><th>Text</th><th>Status</th></tr>
{% for r in records %}<tr class="border-b"><td>{{r['created'][11:16]}}</td><td>{{r['username']}}</td><td>{{r['type']}}</td><td>{{r['state']}}/{{r['lga']}}/{{r['ward']}}<br>{{r['age']}}y {{r['gender']}}</td><td>{{r['text_content'][:20]}}</td><td>{{r['status']}}</td></tr>{% endfor %}
</table>
</div>
</div>
</div>
<script>
let naijaData=null;
async function loadNaija(){
  let res = await fetch('https://raw.githubusercontent.com/samuel871/All-Nigeria-State-Lga-Wards/master/nigeria.json');
  naijaData = await res.json();
  let st=document.getElementById('state'); st.innerHTML='';
  Object.keys(naijaData).forEach(s=>{let o=document.createElement('option'); o.value=s; o.text=s; st.add(o);});
  st.value='Jigawa'; loadLGA();
}
function loadLGA(){
  let st=document.getElementById('state').value;
  let lga=document.getElementById('lga'); lga.innerHTML='';
  if(naijaData && naijaData[st]){ Object.keys(naijaData[st]).forEach(l=>{let o=document.createElement('option'); o.value=l; o.text=l; lga.add(o);}); }
  lga.value='Babura'; loadWard();
}
function loadWard(){
  let st=document.getElementById('state').value; let lga=document.getElementById('lga').value;
  let wd=document.getElementById('ward'); wd.innerHTML='';
  if(naijaData && naijaData[st] && naijaData[st][lga]){ naijaData[st][lga].forEach(w=>{let o=document.createElement('option'); o.value=w; o.text=w; wd.add(o);}); }
  if(lga=='Babura') wd.value='Dorawa';
}
document.getElementById('state').addEventListener('change', loadLGA);
document.getElementById('lga').addEventListener('change', loadWard);
loadNaija();
let rec,chunks=[],sec=0,timer,blob;
function toggleRec(){ if(!rec || rec.state=='inactive') startRec(); else stopRec(); }
async function startRec(){
  let target=parseInt(document.getElementById('duration').value)||5;
  document.getElementById('target').innerText=target; sec=0;
  let stream=await navigator.mediaDevices.getUserMedia({audio:true});
  rec=new MediaRecorder(stream); chunks=[];
  rec.ondataavailable=e=>chunks.push(e.data);
  rec.onstop=()=>{ blob=new Blob(chunks,{type:'audio/webm'}); let a=document.getElementById('audio'); a.src=URL.createObjectURL(blob); a.style.display='block'; document.getElementById('saveV').style.display='block'; };
  rec.start(); document.getElementById('recBtn').innerText='Tsaya';
  timer=setInterval(()=>{sec++; document.getElementById('timer').innerText=`${String(Math.floor(sec/60)).padStart(2,'0')}:${String(sec%60).padStart(2,'0')} / ${target}s`; if(sec>=target) stopRec();},1000);
}
function stopRec(){ if(rec){rec.stop(); clearInterval(timer); document.getElementById('recBtn').innerText='Fara Recording';} }
function saveVoice(){
  let fd=new FormData();
  fd.append('audio', blob, 'voice.webm');
  fd.append('state', document.getElementById('state').value);
  fd.append('lga', document.getElementById('lga').value);
  fd.append('ward', document.getElementById('ward').value);
  fd.append('age', document.getElementById('age').value||'25');
  fd.append('gender', document.getElementById('gender').value);
  fd.append('quality', document.getElementById('quality').value);
  fd.append('duration', document.getElementById('duration').value);
  fd.append('text', document.getElementById('text').value);
  fd.append('consent', document.getElementById('consent').checked?1:0);
  fetch('/save_voice',{method:'POST', body:fd}).then(()=>location.reload());
}
function saveImage(){
  let f=document.getElementById('imgFile').files[0]; if(!f) return alert('Zabi hoto');
  let fd=new FormData(); fd.append('image', f);
  fd.append('category', document.getElementById('imgCat').value);
  fd.append('state', document.getElementById('state').value);
  fd.append('lga', document.getElementById('lga').value);
  fd.append('ward', document.getElementById('ward').value);
  fetch('/save_image',{method:'POST', body:fd}).then(()=>location.reload());
}
function saveProv(){
  let fd=new FormData();
  fd.append('text', document.getElementById('provText').value);
  fd.append('meaning', document.getElementById('provMean').value);
  fd.append('state', document.getElementById('state').value);
  fd.append('lga', document.getElementById('lga').value);
  fetch('/save_prov',{method:'POST', body:fd}).then(()=>location.reload());
}
function show(id){ document.querySelectorAll('#voice,#image,#proverb,#setting').forEach(d=>d.style.display='none'); document.getElementById(id).style.display='block'; }
function doSearch(){ let q=document.getElementById('search').value.toLowerCase(); document.querySelectorAll('table tr').forEach((tr,i)=>{ if(i==0) return; tr.style.display=tr.innerText.toLowerCase().includes(q)?'':'none'; }); }
</script>
</body></html>
"""

@app.route('/')
def home():
    if 'user' not in session: return redirect('/login')
    db=get_db(); recs=db.execute("SELECT * FROM records ORDER BY id DESC LIMIT 300").fetchall()
    v=db.execute("SELECT COUNT(*) FROM records WHERE type='voice'").fetchone()[0]
    i=db.execute("SELECT COUNT(*) FROM records WHERE type='image'").fetchone()[0]
    p=db.execute("SELECT COUNT(*) FROM records WHERE type='proverb'").fetchone()[0]
    return render_template_string(HTML_PAGE, records=recs, v=v, i=i, p=p)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        db=get_db(); u=db.execute("SELECT * FROM users WHERE username=? AND password=?", (request.form['username'], request.form['password'])).fetchone()
        if u: session['user']=dict(u); return redirect('/')
        return "Login kuskure - Bulangu / Bulangu123"
    return '<body style="font-family:Arial;padding:20px;max-width:400px;margin:auto"><h2>BULANGU AI LAB - Login</h2><p>Founder: Bulangu / Bulangu123</p><form method="POST"><input name="username" placeholder="Bulangu" style="width:100%;padding:10px;margin:5px 0"><input name="password" type="password" placeholder="Bulangu123" style="width:100%;padding:10px"><button style="width:100%;padding:10px;background:black;color:white">Shiga</button></form></body>'

@app.route('/save_voice', methods=['POST'])
def save_voice():
    f=request.files['audio']
    age=request.form.get('age','25'); gender=request.form.get('gender','male_young')
    ward=request.form.get('ward','Dorawa'); text=request.form.get('text','Sannu')[:10]
    fname=f"{gender}_{age}y_{ward}_{text}_{datetime.datetime.now().strftime('%H%M%S')}.webm"
    path=os.path.join("data/voices", secure_filename(fname)); f.save(path)
    db=get_db()
    db.execute("INSERT INTO records (type,file_path,text_content,username,state,lga,ward,age,gender,quality,duration,status,created,consent) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('voice', path, request.form.get('text'), session['user']['username'], request.form.get('state'), request.form.get('lga'), ward, int(age) if age.isdigit() else 25, gender, request.form.get('quality'), request.form.get('duration'), 'pending', datetime.datetime.now().isoformat(), int(request.form.get('consent',0))))
    db.commit(); return "ok"

@app.route('/save_image', methods=['POST'])
def save_image():
    f=request.files['image']
    fname=f"img_{datetime.datetime.now().strftime('%H%M%S')}_{secure_filename(f.filename)}"
    path=os.path.join("data/images", fname); f.save(path)
    db=get_db()
    db.execute("INSERT INTO records (type,file_path,text_content,username,state,lga,ward,quality,status,created) VALUES (?,?,?,?,?,?,?,?,?,?)", ('image', path, request.form.get('category'), session['user']['username'], request.form.get('state'), request.form.get('lga'), request.form.get('ward'), request.form.get('category'), 'pending', datetime.datetime.now().isoformat()))
    db.commit(); return "ok"

@app.route('/save_prov', methods=['POST'])
def save_prov():
    db=get_db()
    db.execute("INSERT INTO records (type,text_content,username,state,lga,ward,quality,status,created) VALUES (?,?,?,?,?,?,?,?)", ('proverb', f"{request.form.get('text')} | {request.form.get('meaning')}", session['user']['username'], request.form.get('state'), request.form.get('lga'), 'General', request.form.get('meaning'), 'pending', datetime.datetime.now().isoformat()))
    db.commit(); return "ok"

@app.route('/zip')
def zip_all():
    t=request.args.get('type','all')
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w') as z:
        db=get_db(); rows=db.execute("SELECT * FROM records").fetchall()
        for r in rows:
            if t=='voice' and r['type']!='voice': continue
            if t=='image' and r['type']!='image': continue
            if t=='proverb' and r['type']!='proverb': continue
            if r['file_path'] and os.path.exists(r['file_path']):
                z.write(r['file_path'], f"{r['type']}/{os.path.basename(r['file_path'])}")
            meta = {"id": r['id'], "type": r['type'], "text": r['text_content'], "state": r['state'], "lga": r['lga'], "ward": r['ward'], "age": r['age'], "gender": r['gender'], "quality": r['quality'], "duration": r['duration'], "consent": r['consent'], "created": r['created'], "username": r['username']}
            z.writestr(f"metadata/{r['id']}_{r['gender']}_{r['age']}.json", json.dumps(meta, indent=2))
    mem.seek(0)
    return send_file(mem, download_name=f"bulangu_{t}_{datetime.datetime.now().strftime('%Y%m%d')}.zip", as_attachment=True)

@app.route('/admin')
def admin():
    if 'user' not in session: return redirect('/login')
    db=get_db(); recs=db.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
    return render_template_string("<body><h2>Admin - Bulangu</h2><table border=1><tr><th>ID</th><th>User</th><th>Ward/Age/Gender</th><th>Type</th><th>Action</th></tr>{% for r in recs %}<tr><td>{{r['id']}}</td><td>{{r['username']}}</td><td>{{r['ward']}}/{{r['age']}}/{{r['gender']}}</td><td>{{r['type']}}</td><td><a href='/approve/{{r['id']}}'>Accept</a></td></tr>{% endfor %}</table></body>", recs=recs)

@app.route('/approve/<int:id>')
def approve(id): db=get_db(); db.execute("UPDATE records SET status='approved' WHERE id=?",(id,)); db.commit(); return redirect('/admin')
@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000)
