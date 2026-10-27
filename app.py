import os, sqlite3, zipfile, datetime, json
from flask import Flask, request, render_template_string, redirect, session, send_file
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.secret_key = "bulangu-v5-final-2026"
DB = "bulangu_v5.db"
os.makedirs("data/voices", exist_ok=True)
os.makedirs("data/images", exist_ok=True)

def get_db():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, created TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, type TEXT, text TEXT, meaning TEXT, file_path TEXT, user TEXT, state TEXT, lga TEXT, ward TEXT, age TEXT, gender TEXT, quality TEXT, created TEXT)")
    try:
        db.execute("INSERT INTO users (username,password,role,created) VALUES (?,?,?,?)", ("Bulangu","Bulangu123","founder", datetime.datetime.now().isoformat()))
        db.commit()
    except: pass
    db.close()
init()

HTML = """
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.tailwindcss.com"></script><title>BULANGU AI LAB V5</title></head>
<body class="bg-gray-100">
<nav class="bg-black text-white p-3 flex justify-between"><b>🌍 BULANGU AI LAB V5 - Founder Bulangu</b><a href="/logout" class="bg-white text-black px-3 py-1 rounded">Fita</a></nav>
<div class="max-w-2xl mx-auto p-3">
<div class="bg-white p-3 rounded shadow text-center mb-3">
🎙️ Voices: <b>{{v}}</b> | 🖼️ Images: <b>{{i}}</b> | 📜 Proverbs: <b>{{p}}</b><br>
<small>Target: 500 Voices / 300 Images / 100 Proverbs | Founder: Dorawa Babura Jigawa</small>
</div>

<div class="bg-white p-4 rounded shadow">
<div class="flex gap-2 mb-4">
<button onclick="show('m')" class="bg-blue-600 text-white px-4 py-2 rounded">Murya</button>
<button onclick="show('h')" class="bg-gray-300 px-4 py-2 rounded">Hoto</button>
<button onclick="show('k')" class="bg-gray-300 px-4 py-2 rounded">Karin Magana</button>
<button onclick="show('z')" class="bg-gray-300 px-4 py-2 rounded">ZIP</button>
</div>

<div id="m">
<h3 class="font-bold mb-2">Tara Murya - Don Google/Meta</h3>
<select id="state" class="w-full border p-2 mb-2 rounded"><option>Jigawa</option><option>Kano</option><option>Kaduna</option><option>Lagos</option><option>FCT</option></select>
<select id="lga" class="w-full border p-2 mb-2 rounded"><option>Babura</option><option>Auyo</option><option>Dutse</option><option>Gumel</option><option>Hadejia</option></select>
<select id="ward" class="w-full border p-2 mb-2 rounded"><option>Dorawa</option><option>Arewa</option><option>Battali</option><option>Garu</option><option>Kyambo</option></select>
<select id="gender" class="w-full border p-2 mb-2 rounded"><option>Mace Tsohuwa 50+ - Mafi Daraja</option><option>Namiji Tsoho 50+</option><option>Mace 20-49</option><option>Namiji 20-49</option></select>
<input id="age" value="65" class="w-full border p-2 mb-2 rounded" placeholder="Shekaru">
<select id="quality" class="w-full border p-2 mb-2 rounded"><option>Clear Voice - Daki Shiru 15cm</option><option>With Noise - Kasuwa 50cm</option><option>Short - 2-5 seconds</option><option>Long - 60-180 seconds</option></select>
<input id="text" value="Sannu da zuwa Dorawa" class="w-full border p-2 mb-2 rounded" placeholder="Abin da za a fada">
<button id="recBtn" onclick="recToggle()" class="bg-red-600 text-white w-full p-3 rounded font-bold">🔴 Fara Recording</button>
<p id="timer" class="text-center">00:00 / 15s</p>
<audio id="audio" controls style="display:none" class="w-full"></audio>
<button id="saveVoice" style="display:none" onclick="saveVoice()" class="bg-green-600 text-white w-full p-3 rounded mt-2">💾 Ajiye Murya</button>
</div>

<div id="h" style="display:none">
<h3 class="font-bold mb-2">Tara Hoto</h3>
<input type="file" id="img" class="w-full border p-2 mb-2 rounded">
<select id="icat" class="w-full border p-2 mb-2 rounded"><option>Market Crowd</option><option>Farm - Gona</option><option>Shop</option><option>Handwriting - Rubutu</option></select>
<button onclick="saveImage()" class="bg-blue-600 text-white w-full p-3 rounded">📤 Ajiye Hoto</button>
</div>

<div id="k" style="display:none">
<h3 class="font-bold mb-2">Karin Magana</h3>
<input id="prov" placeholder="Zomo baya gudu a banza" class="w-full border p-2 mb-2 rounded">
<input id="mean" placeholder="Ma'anarsa Turanci - A hare does not run in vain" class="w-full border p-2 mb-2 rounded">
<button onclick="saveProv()" class="bg-purple-600 text-white w-full p-3 rounded">Ajiye Karin Magana</button>
</div>

<div id="z" style="display:none">
<h3 class="font-bold">ZIP Download - Domin Siyarwa</h3>
<p class="text-sm">File suna: Gender_Age_Ward_Text.webm<br>Auto Save: SQLite Har Abada</p>
<button onclick="location.href='/zip?type=all'" class="bg-black text-white w-full p-3 rounded mt-3">⬇️ DOWNLOAD ALL ZIP</button>
<div class="grid grid-cols-3 gap-2 mt-2">
<button onclick="location.href='/zip?type=voice'" class="bg-gray-700 text-white p-2 rounded">Voices</button>
<button onclick="location.href='/zip?type=image'" class="bg-gray-700 text-white p-2 rounded">Images</button>
<button onclick="location.href='/zip?type=proverb'" class="bg-gray-700 text-white p-2 rounded">Proverbs</button>
</div>
</div>

</div>

<div class="bg-white p-3 rounded shadow mt-3">
<input id="s" onkeyup="search()" placeholder="Search Dorawa, Sannu, Mace..." class="w-full border p-2 rounded mb-2">
<div class="overflow-auto text-xs">
<table class="w-full"><tr class="bg-gray-100"><th>Time</th><th>Type</th><th>Wuri</th><th>Text</th></tr>
{% for r in recs %}<tr class="border-b"><td>{{r['created'][11:16]}}</td><td>{{r['type']}}</td><td>{{r['lga']}}/{{r['ward']}}/{{r['age']}}</td><td>{{r['text']}}</td></tr>{% endfor %}
</table>
</div>
</div>

</div>
<script>
function show(id){['m','h','k','z'].forEach(x=>document.getElementById(x).style.display='none'); document.getElementById(id).style.display='block';}
let rec,chunks=[],t,sec=0,blob;
function recToggle(){if(!rec||rec.state=='inactive'){startR()}else{stopR()}}
async function startR(){sec=0; let s=await navigator.mediaDevices.getUserMedia({audio:true}); rec=new MediaRecorder(s); chunks=[]; rec.ondataavailable=e=>chunks.push(e.data); rec.onstop=()=>{blob=new Blob(chunks,{type:'audio/webm'}); document.getElementById('audio').src=URL.createObjectURL(blob); document.getElementById('audio').style.display='block'; document.getElementById('saveVoice').style.display='block';}; rec.start(); document.getElementById('recBtn').innerText='⏹️ Tsaya'; t=setInterval(()=>{sec++; document.getElementById('timer').innerText=`00:${sec} / 15s`; if(sec>=15) stopR();},1000);}
function stopR(){if(rec){rec.stop(); clearInterval(t); document.getElementById('recBtn').innerText='🔴 Fara Recording';}}
async function saveVoice(){let fd=new FormData(); fd.append('audio',blob,'a.webm'); fd.append('state',state.value); fd.append('lga',lga.value); fd.append('ward',ward.value); fd.append('gender',gender.value); fd.append('age',age.value); fd.append('quality',quality.value); fd.append('text',text.value); fetch('/save_voice',{method:'POST',body:fd}).then(()=>location.reload());}
async function saveImage(){let f=document.getElementById('img').files[0]; if(!f) return alert('Zabi hoto'); let fd=new FormData(); fd.append('image',f); fd.append('cat',icat.value); fd.append('state',state.value); fd.append('lga',lga.value); fd.append('ward',ward.value); fetch('/save_image',{method:'POST',body:fd}).then(()=>location.reload());}
async function saveProv(){let fd=new FormData(); fd.append('text',prov.value); fd.append('meaning',mean.value); fd.append('state',state.value); fd.append('lga',lga.value); fd.append('ward',ward.value); fetch('/save_proverb',{method:'POST',body:fd}).then(()=>location.reload());}
function search(){let q=s.value.toLowerCase(); document.querySelectorAll('table tr').forEach((tr,i)=>{if(i==0) return; tr.style.display=tr.innerText.toLowerCase().includes(q)?'':'none';});}
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
        db=get_db(); r=db.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone(); db.close()
        if r: session['user']=dict(r); return redirect('/dashboard')
        return "Login kuskure"
    return render_template_string(HTML.replace('{{v}}','0').replace('{{i}}','0').replace('{{p}}','0').replace('{% for r in recs %}','').replace('{% endfor %}','') + """<div class="max-w-md mx-auto p-6 bg-white rounded shadow mt-10"><h2 class="font-bold">Login Founder</h2><form method="POST" class="mt-4"><input name="username" placeholder="Bulangu" class="w-full border p-2 mb-2 rounded"><input name="password" type="password" placeholder="Bulangu123" class="w-full border p-2 mb-2 rounded"><button class="bg-black text-white w-full p-3 rounded">Shiga</button></form></div></div></body></html>""")

@app.route('/dashboard')
def dash():
    if 'user' not in session: return redirect('/login')
    db=get_db(); recs=db.execute("SELECT * FROM records ORDER BY id DESC LIMIT 100").fetchall()
    v=db.execute("SELECT COUNT(*) FROM records WHERE type='voice'").fetchone()[0]
    i=db.execute("SELECT COUNT(*) FROM records WHERE type='image'").fetchone()[0]
    p=db.execute("SELECT COUNT(*) FROM records WHERE type='proverb'").fetchone()[0]
    db.close()
    return render_template_string(HTML, v=v, i=i, p=p, recs=recs)

@app.route('/save_voice', methods=['POST'])
def sv():
    f=request.files['audio']
    name=f"{request.form.get('gender')}_{request.form.get('age')}y_{request.form.get('ward')}_{request.form.get('text')}.webm".replace(' ','_')[:50]
    path=os.path.join("data/voices", secure_filename(name)); f.save(path)
    db=get_db(); db.execute("INSERT INTO records (type,text,file_path,user,state,lga,ward,age,gender,quality,created) VALUES (?,?,?,?,?,?,?,?,?,?,?)", ('voice',request.form.get('text'),path,session['user']['username'],request.form.get('state'),request.form.get('lga'),request.form.get('ward'),request.form.get('age'),request.form.get('gender'),request.form.get('quality'),datetime.datetime.now().isoformat())); db.commit(); db.close(); return "ok"

@app.route('/save_image', methods=['POST'])
def si():
    f=request.files['image']; path=os.path.join("data/images", secure_filename(f.filename)); f.save(path)
    db=get_db(); db.execute("INSERT INTO records (type,text,file_path,user,state,lga,ward,created) VALUES (?,?,?,?,?,?,?,?)", ('image',request.form.get('cat'),path,session['user']['username'],request.form.get('state'),request.form.get('lga'),request.form.get('ward'),datetime.datetime.now().isoformat())); db.commit(); db.close(); return "ok"

@app.route('/save_proverb', methods=['POST'])
def sp():
    db=get_db(); db.execute("INSERT INTO records (type,text,meaning,user,state,lga,ward,created) VALUES (?,?,?,?,?,?,?,?)", ('proverb',request.form.get('text'),request.form.get('meaning'),session['user']['username'],request.form.get('state'),request.form.get('lga'),request.form.get('ward'),datetime.datetime.now().isoformat())); db.commit(); db.close(); return "ok"

@app.route('/zip')
def z():
    t=request.args.get('type','all'); mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w') as zf:
        db=get_db(); rows=db.execute("SELECT * FROM records").fetchall(); db.close()
        for r in rows:
            if t!='all' and t not in r['type']: continue
            if r['file_path'] and os.path.exists(r['file_path']): zf.write(r['file_path'])
            zf.writestr(f"metadata/{r['id']}.json", json.dumps(dict(r), indent=2, default=str))
    mem.seek(0); return send_file(mem, download_name=f"bulangu_v5_{t}.zip", as_attachment=True)

@app.route('/logout')
def lo(): session.clear(); return redirect('/login')

if __name__=='__main__': app.run(host='0.0.0.0', port=5000)
