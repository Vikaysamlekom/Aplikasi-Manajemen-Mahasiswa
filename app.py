from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import json, os, re
from typing import List
import time
import os, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USERS_FILE = os.path.join(BASE_DIR, "users.json")
MAHASISWA_FILE = os.path.join(BASE_DIR, "mahasiswa.json")

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

start = time.time()
print(time.time() - start)

app = Flask(__name__)
app.secret_key = "super-secret-change-this"

# ---------- Data model ----------
JURUSAN_LIST = [
    "Teknik Informatika",
    "Manajemen",
    "Hukum",
    "Sastra Inggris",
    "PJOK",
    "PGSD",
    "Ilmu Komunikasi"
]

class ValidationError(Exception):
    pass

class Mahasiswa:
    def __init__(self, nim: str, nama: str, kelas: str, ipk: float, jurusan: str):
        self.nim = str(nim)
        self.nama = nama
        self.kelas = kelas
        self.ipk = float(ipk)
        self.jurusan = jurusan

    def to_dict(self):
        return {
            "nim": self.nim,
            "nama": self.nama,
            "kelas": self.kelas,
            "ipk": self.ipk,
            "jurusan": self.jurusan
        }

# ---------- Validation ----------
def validate_input(nim, nama, kelas, ipk, jurusan):
    if not re.match(r'^\d{12}$', str(nim)):
        raise ValidationError("NIM harus 12 digit angka.")
    if not re.match(r'^[A-Za-z ]+$', nama):
        raise ValidationError("Nama hanya boleh huruf dan spasi.")
    if not re.match(r'^[A-Za-z0-9]+$', kelas):
        raise ValidationError("Kelas hanya boleh huruf dan angka tanpa spasi.")
    try:
        ipk_f = float(ipk)
    except:
        raise ValidationError("IPK harus angka desimal.")
    if not (0.0 <= ipk_f <= 4.0):
        raise ValidationError("IPK harus antara 0.0 – 4.0.")
    if jurusan not in JURUSAN_LIST:
        raise ValidationError("Jurusan tidak valid.")
    return True

# ---------- Load & Save ----------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def load_data() -> List[Mahasiswa]:
    if not os.path.exists(MAHASISWA_FILE):
        return []
    with open(MAHASISWA_FILE, "r", encoding="utf-8") as f:
        try:
            raw = json.load(f)
            return [Mahasiswa(m["nim"], m["nama"], m["kelas"], m["ipk"], m.get("jurusan","")) for m in raw]
        except:
            return []

def save_data(mahasiswa: List[Mahasiswa]):
    with open(MAHASISWA_FILE, "w", encoding="utf-8") as f:
        json.dump([m.to_dict() for m in mahasiswa], f, indent=4, ensure_ascii=False)

# Ensure default admin exists
users = load_users()
if "admin" not in users:
    users["admin"] = generate_password_hash("12345")
    save_users(users)

# ---------- Login required ----------
def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

# ---------- Search ----------
def search_students(arr: List[Mahasiswa], keyword: str):
    k = keyword.lower()
    return [m for m in arr if k in m.nim.lower() or k in m.nama.lower() or k in m.jurusan.lower()]

def binary_search(arr: List[Mahasiswa], keyword: str):
    keyword = keyword.lower()
    arr_sorted = sorted(arr, key=lambda x: x.nama.lower())
    left, right = 0, len(arr_sorted) - 1
    result = []
    while left <= right:
        mid = (left + right) // 2
        midval = arr_sorted[mid].nama.lower()
        if keyword in midval or keyword in arr_sorted[mid].nim.lower() or keyword in arr_sorted[mid].jurusan.lower():
            i = mid
            while i >= 0 and keyword in arr_sorted[i].nama.lower():
                result.append(arr_sorted[i]); i -= 1
            i = mid+1
            while i < len(arr_sorted) and keyword in arr_sorted[i].nama.lower():
                result.append(arr_sorted[i]); i += 1
            break
        elif keyword < midval:
            right = mid - 1
        else:
            left = mid + 1
    return result

# ---------- Sorting ----------
def bubble_sort(arr: List[Mahasiswa], key: str, reverse=False):
    a = arr[:]
    for i in range(len(a)):
        for j in range(0, len(a)-i-1):
            if (getattr(a[j], key) > getattr(a[j+1], key)) ^ reverse:
                a[j], a[j+1] = a[j+1], a[j]
    return a

SORT_ALGS = {
    "bubble": bubble_sort
}

# ---------- ROUTES ----------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"].strip()
        p = request.form["password"].strip()
        users = load_users()
        if u in users and check_password_hash(users[u], p):
            session["user"] = u
            return redirect(url_for("index"))
        flash("Login gagal")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"].strip()
        p = request.form["password"].strip()
        users = load_users()
        if u in users:
            flash("Username sudah ada")
            return redirect(url_for("register"))
        users[u] = generate_password_hash(p)
        save_users(users)
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- APLIKASI UTAMA ----------
@app.route("/index")
@login_required
def index():
    data = load_data()
    q = request.args.get("q","").strip()
    jurusan_filter = request.args.get("jurusan","")
    method = request.args.get("method","linear")
    sort_alg = request.args.get("sort_alg", "")
    sort_field = request.args.get("sort_field", "nama")
    order = request.args.get("order", "asc")

    if jurusan_filter:
        data = [m for m in data if m.jurusan == jurusan_filter]

    if q:
        if method in ["linear", "sequential"]:
            data = search_students(data, q)
        elif method == "binary":
            data = binary_search(data, q)

    reverse = (order == "desc")
    if sort_alg:
        alg = SORT_ALGS.get(sort_alg)
        if alg:
            data = alg(data, sort_field, reverse=reverse)
    else:
        data = sorted(data, key=lambda x: getattr(x, sort_field), reverse=reverse)

    complexity_info = ""

    if q:
        if method in ["linear", "sequential"]:
            complexity_info += "Search: Linear Search → O(n)\n"
        elif method == "binary":
            complexity_info += "Search: Binary Search → O(log n)\n"
    else:
        complexity_info += "Search: Tidak digunakan.\n"

    if sort_alg:
        complexity_info += f"Sort: {sort_alg.title()} Sort → O(n²)\n"
    else:
        complexity_info += "Sort: Python Timsort → O(n log n)\n"

    return render_template(
        "index.html",
        data=data,
        jurusan_list=JURUSAN_LIST,
        q=q,
        jurusan_filter=jurusan_filter,
        method=method,
        sort_alg=sort_alg,
        sort_field=sort_field,
        order=order,
        complexity_info=complexity_info
    )



@app.route("/dashboard")
@login_required
def dashboard():
    data = load_data()
    total = len(data)
    avg_ipk = round(sum(m.ipk for m in data) / total, 2) if total else 0

    # ===== HITUNG JUMLAH PER JURUSAN =====
    per_jurusan = {}
    for m in data:
        per_jurusan[m.jurusan] = per_jurusan.get(m.jurusan, 0) + 1

    # ===== CARI JURUSAN TERBANYAK =====
    top_jurusan = "-"
    if per_jurusan:
        top_jurusan = max(per_jurusan, key=per_jurusan.get)

    return render_template(
        "dashboard.html",
        total=total,
        avg_ipk=avg_ipk,
        top_jurusan=top_jurusan,
        per_jurusan=per_jurusan
    )



@app.route("/mahasiswa")
@login_required
def mahasiswa_page():
    return render_template("mahasiswa.html", data=load_data())

@app.route("/tambah", methods=["GET","POST"])
@login_required
def tambah():
    if request.method == "POST":
        nim = request.form["nim"]
        nama = request.form["nama"]
        kelas = request.form["kelas"].upper()
        ipk = request.form["ipk"]
        jurusan = request.form["jurusan"]
        validate_input(nim, nama, kelas, ipk, jurusan)
        data = load_data()
        data.append(Mahasiswa(nim, nama, kelas, float(ipk), jurusan))
        save_data(data)
        return redirect(url_for("index"))
    return render_template("tambah.html", jurusan_list=JURUSAN_LIST)

@app.route("/edit/<nim>", methods=["GET", "POST"])
@login_required
def edit(nim):
    data = load_data()
    mhs = next((m for m in data if m.nim == nim), None)

    if not mhs:
        flash("Data mahasiswa tidak ditemukan")
        return redirect(url_for("index"))

    if request.method == "POST":
        nama = request.form["nama"]
        kelas = request.form["kelas"].upper()
        ipk = request.form["ipk"]
        jurusan = request.form["jurusan"]

        validate_input(nim, nama, kelas, ipk, jurusan)

        mhs.nama = nama
        mhs.kelas = kelas
        mhs.ipk = float(ipk)
        mhs.jurusan = jurusan

        save_data(data)
        return redirect(url_for("index"))

    return render_template(
    "edit.html",
    mhs=mhs,
    jurusan_list=JURUSAN_LIST
)


    
@app.route("/delete/<nim>")
@login_required
def delete(nim):
    data = load_data()
    data_baru = [m for m in data if m.nim != nim]

    if len(data) == len(data_baru):
        flash("Data mahasiswa tidak ditemukan", "error")
    else:
        save_data(data_baru)
        flash("Data mahasiswa berhasil dihapus", "success")

    return redirect(url_for("index"))
    


# ---------- RUN ----------
if __name__ == "__main__":
    if not os.path.exists(MAHASISWA_FILE):
        with open(MAHASISWA_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(USERS_FILE):
        save_users({"admin": generate_password_hash("12345")})
    app.run(debug=True)
