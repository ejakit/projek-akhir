import os
import shutil
from datetime import date
from typing import Optional, Any

import psycopg2
from colorama import Fore, Style, init as colorama_init
from psycopg2.extensions import connection
from pyfiglet import Figlet

# Database Connection

DB_CONFIG = {
    'host': 'localhost',
    'user': 'postgres',
    'port': '5432',
    'password': '23',
    'database': 'ejak',
}


def get_connection():
    """
    Koneksi untuk database postgresql
    :return connection:
    """
    return psycopg2.connect(
        host=DB_CONFIG['host'],
        database=DB_CONFIG['database'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
    )

# Header

colorama_init(autoreset=True)

TITLE_TEXT = "LABULIS"
SUBTITLE = "Analisis Kesesuaian Tanaman (Iklim • Tanah • Ketinggian)"


def center_line(s: str, width: int) -> str:
    s = s.rstrip("\n")
    if len(s) >= width:
        return s
    pad = (width - len(s)) // 2
    return " " * pad + s


def make_border(width: int) -> str:
    seg = "─" * max(2, width - 10)
    line = f"  9e  {seg}  9e  "
    return (line[:width]) if len(line) >= width else center_line(line, width)


def frame_block(lines, width):
    width = max(width, 20)
    top = "╭" + "─" * (width - 2) + "╮"
    bottom = "╰" + "─" * (width - 2) + "╯"
    body = []
    for ln in lines:
        ln = ln.rstrip("\n")
        pad = width - 2 - len(ln)
        body.append("│" + ln + " " * max(0, pad) + "│")
    return [top] + body + [bottom]


def render(width: int = 100) -> str:
    width = max(80, width)
    # Top decorative border (colored)
    top_border = make_border(width)
    out = [f"{Fore.GREEN}{Style.BRIGHT}{top_border}{Style.RESET_ALL}", ""]

    fig = Figlet(font="ansi_shadow")
    title = fig.renderText(TITLE_TEXT).rstrip("\n").splitlines()
    

    # cetak judul terpusat
    for ln in title:
        centered = center_line(ln, width)
        out.append(f"{Fore.YELLOW}{Style.BRIGHT}{centered}{Style.RESET_ALL}")

    # garis dekorasi tengah + subtitle
    out.append("")
    mid_border = center_line(make_border(min(width, 90)), width)
    out.append(f"{Fore.GREEN}{Style.BRIGHT}{mid_border}{Style.RESET_ALL}")
    subtitle_centered = center_line(SUBTITLE, width)
    out.append(f"{Fore.YELLOW}{Style.BRIGHT}{subtitle_centered}{Style.RESET_ALL}")
    out.append("")

    return "\n".join(out)


def header():
    try:
        width = shutil.get_terminal_size().columns
    except Exception:
        width = 100
    print(render(width))

def clear_terminal():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        print("\n" * 100)

# Dekorasi

def display(value, fallback="-"):
    return value if value is not None else fallback


def input_optional(prompt: str, default: str | None = None) -> str | None:
    """
    Input optional
    """
    val = input(prompt).strip()
    return val if val else default


def simpel_lahan_print(row_lahan):
    print("\n=== Daftar Lahan ===")
    if not row_lahan:
        print("\nMasih kosong")
    else:
        for (
            lahan_id,
            nama_petani,
            surveyor_id,
            nama_surveyor,
            ketinggian,
            nama_jalan,
            nama_kecamatan,
            nama_kota,
            nama_provinsi,
            survey_count,
        ) in row_lahan:
            if surveyor_id is None:
                status = "BELUM DIAMBIL"
            else:
                status = f"SUDAH DIAMBIL oleh {nama_surveyor}"

            print(
                f"- ID: {lahan_id} | Petani: {nama_petani} | "
                f"Ketinggian: {display(ketinggian)} | Alamat: {nama_jalan}, "
                f"{nama_kecamatan}, {nama_kota}, {nama_provinsi} | Status Survey: {status} | "
                f"Sudah disurvey selama: {survey_count} hari"
            )


# Alamat

ALAMAT_MASTER_CONFIG = {
    "provinsi":  ("provinsi",  "provinsi_id",  "nama_provinsi"),
    "kota":      ("kota",      "kota_id",      "nama_kota"),
    "kecamatan": ("kecamatan", "kecamatan_id", "nama_kecamatan"),
}


def add_alamat( conn, nama_jalan: str, id_kota: int | None, id_kecamatan: int | None, id_provinsi: int | None, ) -> int | None:
    """ Insert ke tabel alamat  """
    with conn.cursor() as cur:
        cur.execute( """ 
                    INSERT INTO alamat (nama_jalan, id_kota, id_kecamatan, id_provinsi)
                    VALUES (%s, %s, %s, %s) RETURNING alamat_id; """,
                     (nama_jalan, id_kota, id_kecamatan, id_provinsi), )
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None


def pilih_alamat(
    conn,
    table: str,
    id_col: str,
    nama_col: str,
    label: str,
) -> int | None:
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {id_col}, {nama_col} FROM {table} ORDER BY {nama_col};"
        )
        rows = cur.fetchall()

    if not rows:
        print(f"Belum ada data {label}.")
        return None

    print(f"\n=== Daftar {label.capitalize()} ===")
    for rid, nama in rows:
        print(f"{rid}. {nama}")

    pilih = input(f"Pilih ID {label} (kosong = skip): ").strip()
    if not pilih:
        return None

    try:
        pilih_id = int(pilih)
    except ValueError:
        print("Input harus angka.")
        return None

    valid_ids = {r[0] for r in rows}
    if pilih_id not in valid_ids:
        print(f"ID {label} tidak valid.")
        return None

    return pilih_id


def kelola_input_lokasi(conn, jenis_tabel: str, label_tampilan: str) -> int | None:
    """
    Fungsi untuk memilih dan membuat lokasi
    """
    # 1. Ambil data dari database
    config = ALAMAT_MASTER_CONFIG.get(jenis_tabel)
    if not config:
        print(f"Error: Jenis tabel '{jenis_tabel}' tidak dikenal.")
        return None
        
    table, id_col, nama_col = config
    data_list = ambil_semua_data_di_alamat(conn, table, id_col, nama_col)

    # 2. Tampilkan daftar ke user
    print(f"\n--- Pilih {label_tampilan} ---")
    if not data_list:
        print(f"  (Belum ada data {label_tampilan}, silakan ketik nama baru)")
    else:
        for id_val, nama_val in data_list:
            print(f"  [{id_val}] {nama_val}")

    # 3. Minta input user
    while True:
        print(f"\nWajib memilih {label_tampilan} atau buat {label_tampilan} baru")
        inp = input(f"Input {label_tampilan}: ").strip()

        if not inp:
            print(f"{label_tampilan} wajib diisi, tidak boleh kosong.")
            continue

        # Cek apakah input berupa angka (ID)
        if inp.isdigit():
            pilihan_id = int(inp)
            # Cek apakah ID ada di daftar
            ketemu = False
            for id_val, _ in data_list:
                if id_val == pilihan_id:
                    ketemu = True
                    break
            
            if ketemu:
                return pilihan_id
            else:
                print(f"ID {pilihan_id} tidak ditemukan di daftar.")
                konfirmasi = input(f"Apakah anda ingin menggunakan angka '{inp}' sebagai NAMA {label_tampilan} baru? (y/n): ").lower().strip()
                if konfirmasi != 'y':
                    continue
        
        id_baru = cari_atau_buat_alamat(conn, jenis_tabel, inp)
        return id_baru


def buat_alamat(conn) -> int | None:
    """
    Buat dan pilih alamat yang ada
    """
    while True:
    # 1. Provinsi
        id_provinsi = kelola_input_lokasi(conn, "provinsi", "Provinsi")
        if not id_provinsi:
            print("Wajib memilih provinsi atau input nama provinsi baru")
            break
            
        # 2. Kota
        id_kota = kelola_input_lokasi(conn, "kota", "Kota")
        if not id_kota:
            print("Wajib memilih kota atau input nama kota baru")
            break
            
        # 3. Kecamatan
        id_kecamatan = kelola_input_lokasi(conn, "kecamatan", "Kecamatan")
        if not id_kecamatan:
            print("Wajib memilih kecamatan atau input nama kecamatan baru")
            break
            
        # 4. Jalan
    
        nama_jalan = input("Masukkan Nama Jalan: ").strip()
        if nama_jalan:
            break
        print("Nama jalan tidak boleh kosong.")
        
    return add_alamat(conn, nama_jalan, id_kota, id_kecamatan, id_provinsi)


def cari_atau_buat_tabel_alamat(
    conn,
    table: str,
    id_col: str,
    nama_col: str,
    nama: str,
) -> int | None:
    nama = nama.strip()
    if not nama:
        return None

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {id_col} FROM {table} WHERE LOWER({nama_col}) = LOWER(%s)",
            (nama,),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute(
            f"INSERT INTO {table} ({nama_col}) VALUES (%s) RETURNING {id_col};",
            (nama,),
        )
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None

def cari_atau_buat_alamat(conn, jenis: str, nama: str) -> int | None:
    jenis = jenis.lower()
    if jenis not in ALAMAT_MASTER_CONFIG:
        print(f"Jenis '{jenis}' tidak dikenal.")
        return None

    table, id_col, nama_col = ALAMAT_MASTER_CONFIG[jenis]
    return cari_atau_buat_tabel_alamat(conn, table, id_col, nama_col, nama)

def ambil_semua_data_di_alamat(
    conn,
    table: str,
    id_col: str,
    nama_col: str,
) -> list[tuple[int, str]]:
    """
    Ambil semua data dari tabel alamat 
    :return: list of tuple (id, nama)
    """
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {id_col}, {nama_col}
            FROM {table}
            ORDER BY {nama_col};
            """
        )
        return cur.fetchall()


def get_all_alamat_master(conn, jenis: str) -> list[tuple[int, str]]:
    jenis = jenis.lower()
    if jenis not in ALAMAT_MASTER_CONFIG:
        print(f"Jenis '{jenis}' tidak dikenal")
        return []

    table, id_col, nama_col = ALAMAT_MASTER_CONFIG[jenis]
    return ambil_semua_data_di_alamat(conn, table, id_col, nama_col)

# Fungsi admin

def get_user_by_id(conn: psycopg2.extensions.connection, user_id: int) -> Optional[dict[str, Any]]:
    """
        Ambil data user dari tabel users berdasarkan user_id.
        """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, name, username, email, no_telp, id_alamat
            FROM users
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cur.fetchone()

    if not row:
        return None

    return {
        "user_id": row[0],
        "name": row[1],
        "username": row[2],
        "email": row[3],
        "no_telp": row[4],
        "id_alamat": row[5],
    }


def delete_user(
        conn,
        username: str,
        role_name: str | None = None,
) -> Optional[int]:
    """
    Hapus user berdasarkan username.
    Jika role_name diisi, pastikan user punya role tsb dulu.
    Return: user_id yang terhapus atau None.
    """
    with conn.cursor() as cur:
        if role_name:
            cur.execute(
                """
                SELECT u.user_id
                FROM users u
                JOIN user_roles ur ON ur.id_user = u.user_id
                JOIN roles r       ON r.role_id = ur.id_role
                WHERE u.username = %s
                AND LOWER(r.nama_role) = LOWER(%s)
                """,
                (username, role_name),
            )
        else:
            cur.execute(
                "SELECT user_id FROM users WHERE username = %s",
                (username,),
            )

        row = cur.fetchone()
        if not row:
            print(f"User '{username}' tidak ditemukan.")
            return None

        user_id = row[0]

        cur.execute("DELETE FROM user_roles WHERE id_user = %s", (user_id,))
        # Hapus dari users
        cur.execute(
            "DELETE FROM users WHERE user_id = %s RETURNING user_id;",
            (user_id,),
        )
        deleted = cur.fetchone()
        conn.commit()
        print(f"User '{username}' terhapus.")
        return deleted[0] if deleted else None


def read_all_users(conn: psycopg2.extensions.connection) -> dict[str, list[tuple[Any, ...]]]:
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT r.nama_role, u.user_id, u.name, u.username
            FROM users u
            JOIN user_roles ur ON ur.id_user = u.user_id
            JOIN roles r       ON r.role_id = ur.id_role
            ORDER BY r.nama_role, u.user_id;
            """)
        rows = cursor.fetchall()

    result = {}
    for nama_role, user_id, name, username in rows:
        key = nama_role.lower()
        result.setdefault(key, []).append((user_id, name, username))
    return result

def update_user_profile(
    conn: psycopg2.extensions.connection,
    user_id: int,
    *,
    name: Optional[str] = None,
    email: Optional[str] = None,
    no_telp: Optional[str] = None,
    password: Optional[str] = None,
    id_alamat: Optional[int] = None,
) -> bool:
    """
    Update profil user di tabel users
    """
    fields = []
    values: list[Any] = []

    if name is not None:
        fields.append("name = %s")
        values.append(name)

    if email is not None:
        fields.append("email = %s")
        values.append(email)

    if no_telp is not None:
        fields.append("no_telp = %s")
        values.append(no_telp)

    if password is not None:
        fields.append("password = %s")
        values.append(password)

    if id_alamat is not None:
        fields.append("id_alamat = %s")
        values.append(id_alamat)

    if not fields:
        print("Tidak ada data yang diubah.")
        return False

    values.append(user_id)

    query = f"""
        UPDATE users
        SET {", ".join(fields)}
        WHERE user_id = %s
    """

    with conn.cursor() as cur:
        cur.execute(query, tuple(values))
        conn.commit()
        return cur.rowcount > 0


def lihat_data_lahan(conn) -> dict[str, Any]:
    """
    Ambil overview data
    """
    cursor = conn.cursor()

    # 1. Ambil semua user yang punya role 'petani'
    cursor.execute(
        """
        SELECT
            u.user_id,
            u.name,
            u.username,
            u.email,
            u.no_telp
        FROM users u
        JOIN user_roles ur ON ur.id_user = u.user_id
        JOIN roles r       ON r.role_id = ur.id_role
        WHERE LOWER(r.nama_role) = 'petani'
        ORDER BY u.user_id;
        """
    )
    petani = cursor.fetchall()

    # 2. Ambil semua lahan + petani + surveyor + alamat
    cursor.execute(
        """
        SELECT
            l.lahan_id,
            l.ketinggian,

            u_p.user_id        AS petani_id,
            u_p.name           AS nama_petani,

            u_s.user_id        AS surveyor_id,
            u_s.name           AS nama_surveyor,

            a.alamat_id,
            a.nama_jalan,
            kc.nama_kecamatan,
            k.nama_kota,
            p.nama_provinsi
        FROM lahan l
        LEFT JOIN users u_p       ON u_p.user_id    = l.id_user_petani
        LEFT JOIN users u_s       ON u_s.user_id    = l.id_user_surveyor
        LEFT JOIN alamat a        ON a.alamat_id    = l.id_alamat
        LEFT JOIN kecamatan kc    ON kc.kecamatan_id = a.id_kecamatan
        LEFT JOIN kota k          ON k.kota_id      = a.id_kota
        LEFT JOIN provinsi p      ON p.provinsi_id  = a.id_provinsi
        ORDER BY l.lahan_id;
        """
    )
    lahan = cursor.fetchall()

    # 3. Ambil semua survey_data + iklim + tanah + tanaman + petani (via lahan)
    cursor.execute(
        """
        SELECT
            sd.survey_id,
            sd.id_lahan,

            sd.id_user_surveyor,
            us.name               AS nama_surveyor,

            sd.status_survey,
            sd.tanggal_survey,

            sd.id_iklim,
            ik.jenis_cuaca,

            sd.id_tanah,
            kt.kondisi_tanah,
            kt.ph,
            kt.kandungan_nutrisi,
            kt.kelembapan,

            sd.id_tanaman,
            t.nama                AS nama_tanaman,

            u_p.user_id           AS petani_id,
            u_p.name              AS nama_petani
        FROM survey_data sd
        LEFT JOIN users us          ON us.user_id = sd.id_user_surveyor
        LEFT JOIN iklim ik          ON ik.iklim_id = sd.id_iklim
        LEFT JOIN kondisi_tanah kt  ON kt.kondisi_tanah_id = sd.id_tanah
        LEFT JOIN tanaman t         ON t.tanaman_id = sd.id_tanaman
        LEFT JOIN lahan l           ON l.lahan_id = sd.id_lahan
        LEFT JOIN users u_p         ON u_p.user_id = l.id_user_petani
        ORDER BY sd.survey_id;
        """
    )
    survey_data = cursor.fetchall()

    cursor.close()

    return {
        "petani": petani,
        "lahan": lahan,
        "survey_data": survey_data,
    }

# Analysis

def delete_lahan(conn, lahan_id: int) -> bool:
    """
    Hapus lahan berdasarkan lahan_id.
    Hapus dulu survey_data yang terkait, baru hapus lahan.
    """
    with conn.cursor() as cur:
        # Cek keberadaan lahan
        cur.execute("SELECT 1 FROM lahan WHERE lahan_id = %s", (lahan_id,))
        if not cur.fetchone():
            print(f"Lahan ID {lahan_id} tidak ditemukan.")
            return False

        # Hapus survey_data terkait
        cur.execute("DELETE FROM survey_data WHERE id_lahan = %s", (lahan_id,))
        
        # Hapus lahan
        cur.execute("DELETE FROM lahan WHERE lahan_id = %s", (lahan_id,))
        conn.commit()
        return True


def add_lahan(
    conn,
    id_user_petani: int | None,
    id_user_surveyor: int | None,
    id_alamat: int | None,
    ketinggian: float | None,
) -> Optional[int]:
    """
    Tambah data lahan.
    :return: lahan_id atau None.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO lahan (id_user_petani, id_user_surveyor, id_alamat, ketinggian)
            VALUES (%s, %s, %s, %s)
            RETURNING lahan_id;
            """,
            (id_user_petani, id_user_surveyor, id_alamat, ketinggian),
        )
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None


def lihat_lahan_universal(conn, user: dict[str, Any]) -> list[tuple[Any, ...]]:
    role = user["role"].lower()
    user_id = user["id"]

    with conn.cursor() as cur:
        if role == "surveyor":
            cur.execute(
                """
                SELECT
                    l.lahan_id,
                    u_p.name        AS nama_petani,
                    u_s.user_id     AS surveyor_id,
                    u_s.name        AS nama_surveyor,
                    l.ketinggian,
                    a.nama_jalan,
                    kc.nama_kecamatan,
                    kt.nama_kota,
                    p.nama_provinsi,
                    (SELECT COUNT(*) FROM survey_data sd WHERE sd.id_lahan = l.lahan_id) AS survey_count
                FROM lahan l
                LEFT JOIN users u_p       ON u_p.user_id      = l.id_user_petani
                LEFT JOIN users u_s       ON u_s.user_id      = l.id_user_surveyor
                LEFT JOIN alamat a        ON a.alamat_id      = l.id_alamat
                LEFT JOIN kecamatan kc    ON kc.kecamatan_id  = a.id_kecamatan
                LEFT JOIN kota kt         ON kt.kota_id       = a.id_kota
                LEFT JOIN provinsi p      ON p.provinsi_id    = a.id_provinsi
                ORDER BY l.lahan_id;
                """
            )
        elif role == "petani":
            cur.execute(
                """
                SELECT
                    l.lahan_id,
                    u_p.name        AS nama_petani,
                    u_s.user_id     AS surveyor_id,
                    u_s.name        AS nama_surveyor,
                    l.ketinggian,
                    a.nama_jalan,
                    kc.nama_kecamatan,
                    kt.nama_kota,
                    p.nama_provinsi,
                    (SELECT COUNT(*) FROM survey_data sd WHERE sd.id_lahan = l.lahan_id) AS survey_count
                FROM lahan l
                LEFT JOIN users u_p       ON u_p.user_id      = l.id_user_petani
                LEFT JOIN users u_s       ON u_s.user_id      = l.id_user_surveyor
                LEFT JOIN alamat a        ON a.alamat_id      = l.id_alamat
                LEFT JOIN kecamatan kc    ON kc.kecamatan_id  = a.id_kecamatan
                LEFT JOIN kota kt         ON kt.kota_id       = a.id_kota
                LEFT JOIN provinsi p      ON p.provinsi_id    = a.id_provinsi
                WHERE l.id_user_petani = %s
                ORDER BY l.lahan_id;
                """,
                (user_id,),
            )
        else:  # admin
            cur.execute(
                """
                SELECT
                    l.lahan_id,
                    u_p.name        AS nama_petani,
                    u_s.user_id     AS surveyor_id,
                    u_s.name        AS nama_surveyor,
                    l.ketinggian,
                    a.nama_jalan,
                    kc.nama_kecamatan,
                    kt.nama_kota,
                    p.nama_provinsi,
                    (SELECT COUNT(*) FROM survey_data sd WHERE sd.id_lahan = l.lahan_id) AS survey_count
                FROM lahan l
                LEFT JOIN users u_p       ON u_p.user_id      = l.id_user_petani
                LEFT JOIN users u_s       ON u_s.user_id      = l.id_user_surveyor
                LEFT JOIN alamat a        ON a.alamat_id      = l.id_alamat
                LEFT JOIN kecamatan kc    ON kc.kecamatan_id  = a.id_kecamatan
                LEFT JOIN kota kt         ON kt.kota_id       = a.id_kota
                LEFT JOIN provinsi p      ON p.provinsi_id    = a.id_provinsi
                ORDER BY l.lahan_id;
                """
            )

        rows = cur.fetchall()

    return rows


def add_tanaman(
    conn,
    id_tipe_tanaman: int,
    nama_tanaman: str,
    ketinggian: float,
    ph: float,
    kandungan_nutrisi: float,
    kondisi_tanah: str,
    iklim_id: int,
    kelembapan: float,  
) -> Optional[int]:
    """
    Tambah tanaman
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM tanaman
            WHERE LOWER(nama) = LOWER(%s)
              AND id_tipe_tanaman = %s
            """,
            (nama_tanaman, id_tipe_tanaman),
        )
        if cur.fetchone():
            print(
                f"Nama tanaman '{nama_tanaman}' sudah ada untuk tipe {id_tipe_tanaman}."
            )
            return None

        cur.execute(
            """
            INSERT INTO tanaman (
                id_tipe_tanaman, nama, ketinggian, ph, 
                kandungan_nutrisi, kondisi_tanah, iklim_id, kelembapan
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING tanaman_id;
            """,
            (
                id_tipe_tanaman, nama_tanaman, ketinggian, ph, 
                kandungan_nutrisi, kondisi_tanah, iklim_id, kelembapan
            ),
        )
        row = cur.fetchone()
        conn.commit()

        tanaman_id = row[0] if row else None
        if tanaman_id is not None:
            print(f"Tanaman '{nama_tanaman}' (ID {tanaman_id}) berhasil disimpan.")
        return tanaman_id


def delete_tanaman(conn, tanaman_id: int) -> bool:
    """
    Hapus tanaman berdasarkan tanaman_id
    """
    with conn.cursor() as cur:
        # Cek apakah dipakai
        cur.execute("SELECT 1 FROM survey_data WHERE id_tanaman = %s", (tanaman_id,))
        if cur.fetchone():
            print(f"Tanaman ID {tanaman_id} sedang digunakan dalam data survey. Tidak bisa dihapus.")
            return False

        cur.execute("DELETE FROM tanaman WHERE tanaman_id = %s", (tanaman_id,))
        if cur.rowcount > 0:
            conn.commit()
            return True
        else:
            print(f"Tanaman ID {tanaman_id} tidak ditemukan.")
            return False


def hitung_survey(conn, lahan_id: int) -> int:
    """
    Hitung berapa kali surveyor melakukan survey
    """
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM survey_data WHERE id_lahan = %s", (lahan_id,))
        row = cur.fetchone()
        return row[0] if row else 0


def add_survey_data(
    conn,
    id_lahan: int,
    id_user_surveyor: int,
    id_iklim: int,
    id_tanah: int,
    id_tanaman: Optional[int] = None,
    status_survey: str = "waiting",
) -> Optional[int]:
    """
    Tambah record ke survey_data
    """
    tanggal = date.today()

    query = """
        INSERT INTO survey_data (
            id_user_surveyor,
            id_lahan,
            id_iklim,
            id_tanah,
            status_survey,
            id_tanaman,
            tanggal_survey
        ) VALUES (%s,%s,%s,%s,%s,%s,%s)
        RETURNING survey_id;
    """

    with conn.cursor() as cur:
        cur.execute(
            query,
            (
                id_user_surveyor,
                id_lahan,
                id_iklim,
                id_tanah,
                status_survey,
                id_tanaman,
                tanggal,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None


def claim_lahan_for_surveyor(
    conn: connection,
    lahan_id: int,
    surveyor_id: int,
) -> bool:
    """
    Coba klaim lahan untuk surveyor
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id_user_surveyor
            FROM lahan
            WHERE lahan_id = %s
            """,
            (lahan_id,),
        )
        
        row = cur.fetchone()
        if row is None:
            conn.rollback()
            return False
        
        current_surveyor_id = row[0]

        if current_surveyor_id is None:
            cur.execute(
                """
                UPDATE lahan
                SET id_user_surveyor = %s
                WHERE lahan_id = %s
                """,
                (surveyor_id, lahan_id),
            )
            conn.commit()
            return True
        
        if current_surveyor_id == surveyor_id:
            return True

        return False


def hitung_rata_tanah_3_hari_terakhir(conn, lahan_id: int):
    query = """
        SELECT 
            AVG(ph)                AS ph_avg,
            AVG(kandungan_nutrisi) AS nutrisi_avg,
            AVG(kelembapan)        AS kelembapan_avg
        FROM (
            SELECT 
                kt.ph,
                kt.kandungan_nutrisi,
                kt.kelembapan
            FROM survey_data sd
            JOIN kondisi_tanah kt ON kt.kondisi_tanah_id = sd.id_tanah
            WHERE sd.id_lahan = %s
            ORDER BY sd.tanggal_survey DESC
            LIMIT 3
        ) t;
    """
    with conn.cursor() as cur:
        cur.execute(query, (lahan_id,))
        row = cur.fetchone()

    if not row or row[0] is None:
        print("Belum ada data")
        return None

    return {
        "ph": row[0],
        "nutrisi": row[1],
        "kelembapan": row[2],
    }


def lihat_hasil_survey_petani(conn, user: dict[str, Any]) -> list[tuple[Any, ...]]:
    """
    Tampilkan hasil analisis (survey) untuk semua lahan milik petani yang login.
    Fokus ke data yang DISURVEY oleh surveyor (tabel survey_data).
    """
    user_id = user["id"]

    query = """
        SELECT
            l.lahan_id,
            l.ketinggian,

            u_petani.user_id      AS petani_id,
            u_petani.name         AS nama_petani,

            u_surveyor.user_id    AS surveyor_id,
            u_surveyor.name       AS nama_surveyor,

            a.nama_jalan,
            kc.nama_kecamatan,
            k.nama_kota,
            p.nama_provinsi,

            sd.survey_id,
            sd.tanggal_survey,
            sd.status_survey,

            ik.jenis_cuaca,
            ktan.kondisi_tanah,
            ktan.ph,
            ktan.kandungan_nutrisi,
            ktan.kelembapan,

            t.tanaman_id,
            t.nama              AS nama_tanaman_master
            
        FROM lahan l
        JOIN users u_petani          ON u_petani.user_id      = l.id_user_petani
        JOIN survey_data sd          ON sd.id_lahan           = l.lahan_id
        LEFT JOIN users u_surveyor   ON u_surveyor.user_id    = sd.id_user_surveyor

        LEFT JOIN alamat a           ON a.alamat_id           = l.id_alamat
        LEFT JOIN kecamatan kc       ON kc.kecamatan_id       = a.id_kecamatan
        LEFT JOIN kota k             ON k.kota_id             = a.id_kota
        LEFT JOIN provinsi p         ON p.provinsi_id         = a.id_provinsi

        LEFT JOIN iklim ik           ON ik.iklim_id           = sd.id_iklim
        LEFT JOIN kondisi_tanah ktan ON ktan.kondisi_tanah_id = sd.id_tanah
        LEFT JOIN tanaman t          ON t.tanaman_id          = sd.id_tanaman

        WHERE l.id_user_petani = %s
        ORDER BY l.lahan_id, sd.survey_id DESC
        LIMIT 3;
    """

    with conn.cursor() as cur:
        cur.execute(query, (user_id,))
        rows = cur.fetchall()

    if not rows:
        print("\nBelum ada hasil survey untuk lahan kamu.")
        return rows

    print("\n=== HASIL SURVEY SELAMA 3 HARI TERAKHIR LAHAN SAYA ===")
    current_lahan = None
    for row in rows:
        (
            lahan_id,
            ketinggian,
            petani_id,
            nama_petani,
            surveyor_id,
            nama_surveyor,
            nama_jalan,
            nama_kecamatan,
            nama_kota,
            nama_provinsi,
            survey_id,
            tanggal_survey,
            status_survey,
            jenis_cuaca,
            kondisi_tanah,
            ph,
            kandungan_nutrisi,
            kelembapan,
            tanaman_id,
            nama_tanaman_master
        ) = row

        if current_lahan != lahan_id:
            current_lahan = lahan_id
            print("\n----------------------------------------")
            print(f"Lahan ID   : {lahan_id}")
            print(f"  Pemilik  : {nama_petani} (ID {petani_id})")
            print(f"  Ketinggian : {ketinggian}")
            print(
                f"  Alamat   : {nama_jalan}, {nama_kecamatan}, "
                f"{nama_kota}, {nama_provinsi}"
            )
            print("  Survey:")

        if nama_tanaman_master:
            rekom_tanaman = f"{nama_tanaman_master} (ID {tanaman_id})"
        else:
            rekom_tanaman = "-"
        print("-" * 50)
        print(f"    • Survey ID    : {survey_id}")
        print(f"      Oleh         : {nama_surveyor} (ID {surveyor_id})")
        print(f"      Tgl Survey   : {tanggal_survey}")
        print(f"      Alamat       : {nama_jalan}, {nama_kecamatan}, {nama_kota}, {nama_provinsi}")
        print(f"      Status       : {status_survey}")
        print(f"      Iklim        : {jenis_cuaca}")
        print(
            f"      Tanah        : {kondisi_tanah} | pH={ph} | "
            f"Nutrisi={kandungan_nutrisi} | Kelembapan={kelembapan}"
        )
        print(f"      Rekom Tanaman: {rekom_tanaman}")
        print("-" * 50)

    return rows


def get_all_tipe_tanaman(conn) -> list[tuple[int, str]]:
    """
    Ambil semua baris dari tabel tipe_tanaman
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT tipe_tanaman_id, jenis_tanaman "
            "FROM tipe_tanaman "
            "ORDER BY tipe_tanaman_id;"
        )
        return cur.fetchall()


def get_tanaman_by_tipe(conn, tipe_id: int) -> list[tuple[int, str]]:
    """
    Ambil semua tanaman berdasarkan id_tipe_tanaman
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tanaman_id, nama
            FROM tanaman
            WHERE id_tipe_tanaman = %s
            ORDER BY nama;
            """,
            (tipe_id,),
        )
        return cur.fetchall()


def get_all_iklim(conn) -> list[tuple[int, str]]:
    """
    Ambil semua data dari tabel iklim
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT iklim_id, jenis_cuaca "
            "FROM iklim "
            "ORDER BY iklim_id;"
        )
        return cur.fetchall()


def get_all_kondisi_tanah(conn) -> list[tuple[Any, ...]]:
    """
    Ambil semua data dari tabel kondisi_tanah
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT kondisi_tanah_id, kondisi_tanah, ph, kandungan_nutrisi, kelembapan
            FROM kondisi_tanah
            ORDER BY kondisi_tanah_id;
            """
        )
        return cur.fetchall()

# Menu menu

def enter_break():
    input("\nTekan Enter untuk lanjut...")


def menu_admin(conn, user):
    """
    Menu untuk role admin
    """

    while True:
        clear_terminal()
        header()
        print(f"\n=== MENU ADMIN (Login sebagai: {user['username']}) ===")
        print("1. Hapus user")
        print("2. Lihat user")
        print("3. Lihat data lahan")
        print("4. Hapus lahan")
        print("5. Input tanaman")
        print("6. Hapus tanaman")
        print("0. Logout")

        pilihan = input("Pilih menu: ").strip()

        if pilihan == "1":
            print("\n=== Hapus user ===")
            username = input("Username: ")
            role = str(input("Role: ")).strip().lower()

            try:
                user_id = delete_user(conn, username, role)
                if user_id is None:
                    print(f"User '{username}' dengan role '{role}' tidak ditemukan atau tidak dihapus.")
                else:
                    print(f"User dengan ID {user_id} dari {role} berhasil dihapus")
            except Exception as error:
                print(f"Ada error: {error}")
            enter_break()

        elif pilihan == "2":
            all_users = read_all_users(conn)
            print("\n=== Daftar user ===")
            petani_list = all_users.get("petani", [])
            surveyor_list = all_users.get("surveyor", [])

            print(f"\nPetani ({len(petani_list)}):")
            if not petani_list:
                print("  (belum ada petani)")
            else:
                for user_id, name, username in petani_list:
                    print(f"  - ID: {user_id} | Nama: {name} | Username: {username}")

            print(f"\nSurveyor ({len(surveyor_list)}):")
            if not surveyor_list:
                print("  (belum ada surveyor)")
            else:
                for user_id, name, username in surveyor_list:
                    print(f"  - ID: {user_id} | Nama: {name} | Username: {username}")

            enter_break()

        elif pilihan == "3":
            data = lihat_data_lahan(conn)
            petani_list = data.get("petani", [])
            data_lahan = data.get("lahan", [])
            data_survey = data.get("survey_data", [])

            print("\n=== Data Petani ===")
            for user_id, name, username, email, no_telp in petani_list:
                print(
                    f"  - ID: {user_id} | Nama: {name} | Username: {username} | "
                    f"Email: {display(email)} | No Telp: {display(no_telp)}"
                )

            print("\n=== Data Lahan ===")
            for (
                    lahan_id,
                    ketinggian,
                    petani_id,
                    nama_petani,
                    surveyor_id,
                    nama_surveyor,
                    alamat_id,
                    nama_jalan,
                    nama_kecamatan,
                    nama_kota,
                    nama_provinsi,
            ) in data_lahan:
                print(
                    f"- Lahan {lahan_id} | Petani: {display(nama_petani)} (ID {display(petani_id)}) | "
                    f"Surveyor: {display(nama_surveyor)} (ID {display(surveyor_id)}) | "
                    f"Ketinggian: {ketinggian} | Alamat: {nama_jalan}, "
                    f"{nama_kecamatan}, {nama_kota}, {nama_provinsi}"
                )

            print("\n=== Data Survey ===")
            for (
                    survey_id,
                    id_lahan,
                    id_user_surveyor,
                    nama_surveyor,
                    status_survey,
                    tanggal_survey,
                    id_iklim,
                    jenis_cuaca,
                    id_tanah,
                    kondisi_tanah,
                    ph,
                    kandungan_nutrisi,
                    kelembapan,
                    id_tanaman,
                    nama_tanaman,
                    petani_id,
                    nama_petani,
            ) in data_survey:
                print(f"- Survey {survey_id} | Lahan {id_lahan} | Petani: {nama_petani} (ID {petani_id})")
                print(
                    f"  Surveyor : {display(nama_surveyor)} (ID {display(id_user_surveyor)})"
                )
                print(
                    f"  Status   : {status_survey} | Tanggal: {tanggal_survey}"
                )
                print(
                    f"  Iklim    : {jenis_cuaca} | Tanah: {kondisi_tanah} "
                    f"(pH={ph}, Nutrisi={kandungan_nutrisi}, Kelembapan={kelembapan})"
                )
                if id_tanaman:
                    print(f"  Tanaman  : {nama_tanaman} (ID {id_tanaman})")
                else:
                    print("  Tanaman  : -")
            enter_break()

        elif pilihan == "4":
            print("\n=== Hapus Lahan ===")
            try:
                lahan_id = int(input("Masukkan ID Lahan yang akan dihapus: "))
                yakin = input(f"Yakin hapus lahan {lahan_id}? (y/n): ").lower()
                if yakin == 'y':
                    if delete_lahan(conn, lahan_id):
                        print(f"Lahan {lahan_id} berhasil dihapus.")
                    else:
                        print("Gagal menghapus lahan.")
                else:
                    print("Batal.")
            except ValueError:
                print("ID harus angka.")
            enter_break()

        elif pilihan == "5":
            print("\n=== Input Tanaman Baru ===")
            print("Panduan Range:")
            print("- Ketinggian: 0-3000 mdpl")
            print("- pH: 0-14")
            print("- Nutrisi: 0-100")
            print("- Kelembapan: 0-100")

            tipe_list = get_all_tipe_tanaman(conn)
            if not tipe_list:
                print("Belum ada data tipe_tanaman.")
            else:
                print("\nTipe Tanaman:")
                for tipe_id, jenis in tipe_list:
                    print(f"  {tipe_id}. {jenis}")

                try:
                    id_tipe = int(input("ID Tipe Tanaman: ").strip())
                    nama_tanaman = input("Nama tanaman: ").strip()
                    
                    if not nama_tanaman:
                        print("Nama tanaman tidak boleh kosong.")
                        enter_break()
                        continue

                    # Input data lingkungan
                    ketinggian = float(input("Ketinggian (mdpl): ").strip())
                    ph = float(input("pH (0-14): ").strip())
                    nutrisi = float(input("Nutrisi (0-100): ").strip())
                    kelembapan = float(input("Kelembapan (0-100): ").strip())
                    
                    # Pilih iklim
                    iklim_list = get_all_iklim(conn)
                    print("\nPilih Iklim:")
                    for i_id, i_jenis in iklim_list:
                        print(f"  {i_id}. {i_jenis}")
                    iklim_id = int(input("ID Iklim: ").strip())

                    # Kondisi tanah (string bebas atau enum, di sini string)
                    kondisi_tanah = input("Kondisi Tanah (Gembur/Lumpur/dll): ").strip()

                    res = add_tanaman(
                        conn, 
                        id_tipe_tanaman=id_tipe, 
                        nama_tanaman=nama_tanaman,
                        ketinggian=ketinggian,
                        ph=ph,
                        kandungan_nutrisi=nutrisi,
                        kondisi_tanah=kondisi_tanah,
                        iklim_id=iklim_id,
                        kelembapan=kelembapan
                    )
                    
                    if res:
                        print(f"Tanaman '{nama_tanaman}' berhasil ditambahkan.")
                    else:
                        print("Gagal menambahkan tanaman.")
                        
                except ValueError:
                    print("Input harus angka (untuk ID/Nilai).")
            enter_break()

        elif pilihan == "6":
            print("\n=== Hapus Tanaman ===")
            try:
                tanaman_id = int(input("Masukkan ID Tanaman yang akan dihapus: "))
                yakin = input(f"Yakin hapus tanaman {tanaman_id}? (y/n): ").lower()
                if yakin == 'y':
                    if delete_tanaman(conn, tanaman_id):
                        print(f"Tanaman {tanaman_id} berhasil dihapus.")
                    else:
                        print("Gagal menghapus tanaman (mungkin sedang dipakai).")
                else:
                    print("Batal.")
            except ValueError:
                print("ID harus angka.")
            enter_break()

        elif pilihan == "0":
            print("Logout dari admin.")
            break
        else:
            print("Pilihan tidak valid, coba lagi.")
            enter_break()


def menu_petani(conn, user):
    """
    Menu untuk role petani
    """
    petani_id = user["id"]

    while True:
        clear_terminal()
        header()
        print(f"\n=== MENU PETANI (Login sebagai: {user['username']}) ===")
        print("1. Input lahan milik saya")
        print("2. Lihat lahan saya")
        print("3. Lihat hasil analisis di lahan saya")
        print("4. Update profile saya")
        print("0. Logout")

        pilihan = input("Pilih menu: ").strip()

        if pilihan == "1":
            print("\n=== Input Data Lahan milik Saya ===")

            id_alamat = buat_alamat(conn)

            if id_alamat is None:
                print("Alamat nya masih kosong")
                enter_break()
                continue

            lahan_id = add_lahan(
                conn,
                id_user_petani=petani_id,
                id_user_surveyor=None,
                id_alamat=id_alamat,
                ketinggian=None,
            )
            
            if lahan_id is not None:
                print(f"Lahan dengan ID {lahan_id} berhasil ditambahkan.")
            else:
                print("Gagal menambahkan lahan.")
            enter_break()

        elif pilihan == "2":
            simpel_lahan_print(lihat_lahan_universal(conn, user))
            enter_break()
            clear_terminal()

        elif pilihan == "3":
            lihat_hasil_survey_petani(conn, user)
            enter_break()
            clear_terminal()

        elif pilihan == "4":
            menu_update_profile(conn, user)
            enter_break()
            clear_terminal()

        elif pilihan == "0":
            print("Logout dari petani.")
            break
        else:
            print("Pilihan tidak valid, coba lagi.")
            enter_break()



def update_lahan_ketinggian(conn, lahan_id: int, ketinggian: float) -> bool:
    """
    Update ketinggian lahan dari petani
    """
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE lahan SET ketinggian = %s WHERE lahan_id = %s",
            (ketinggian, lahan_id),
        )
        conn.commit()
        return cur.rowcount > 0


def get_iklim_by_id(conn, id_iklim):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM iklim WHERE iklim_id = %s", (id_iklim,))
        result = cur.fetchone()
    return result


def cocokin_tanaman(
    conn,
    ketinggian: float,
    ph: float,
    nutrisi: float,
    kelembapan: float,
    iklim_id: int
) -> tuple[list[tuple], list[tuple]]:
    """
    Cari tanaman yang cocok berdasarkan kriterianya
    """
    # Ambil semua tanaman
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                tanaman_id, 
                nama, 
                ketinggian, 
                ph, 
                kandungan_nutrisi, 
                kelembapan, 
                iklim_id
            FROM tanaman
        """)
        all_plants = cur.fetchall()

    recommended_scored: list[tuple[float, int, str]] = []
    others_scored: list[tuple[float, int, str]] = []

    for p in all_plants:
        t_id, t_nama, t_h, t_ph, t_nut, t_hum, t_iklim = p

        # Kalau ada nilai yang kosong, masuk kategori lain
        if any(v is None for v in (t_h, t_ph, t_nut, t_hum, t_iklim)):
            others_scored.append((0.0, t_id, t_nama))
            continue

        # Toleransi
        match_h   = abs(ketinggian - t_h) <= 200       # mdpl
        match_ph  = abs(ph - t_ph) <= 1.0              # pH
        match_nut = abs(nutrisi - t_nut) <= 20         # persen/indeks
        match_hum = abs(kelembapan - t_hum) <= 15      # persen
        match_ik  = (iklim_id == t_iklim)

        # Scoring tiap kolom
        score = 0.0
        if match_ik:
            score += 3.0
        if match_h:
            score += 2.0
        if match_ph:
            score += 2.0
        if match_nut:
            score += 1.0
        if match_hum:
            score += 1.0

        if match_ik and score >= 5.0:
            recommended_scored.append((score, t_id, t_nama))
        else:
            others_scored.append((score, t_id, t_nama))

    recommended_scored.sort(reverse=True)
    others_scored.sort(reverse=True)

    recommended = [(t_id, t_nama) for score, t_id, t_nama in recommended_scored]
    others = [(t_id, t_nama) for score, t_id, t_nama in others_scored]

    return recommended, others 


def menu_surveyor(conn, user):
    """
    Menu untuk role surveyor
    """
    surveyor_id = user["id"]

    while True:
        clear_terminal()
        header()
        print(f"\n=== MENU SURVEYOR (Login sebagai: {user['username']}) ===")
        print("1. Survey lahan yang sudah ada")
        print("2. Update profile saya")
        print("0. Logout")

        pilihan = input("Pilih menu: ").strip()

        if pilihan == "1":
            simpel_lahan_print(lihat_lahan_universal(conn, user))

            print("\n=== Input survey data ===")
            try:
                lahan_id = int(input("ID lahan yang disurvey: ").strip())
            except ValueError:
                print("ID lahan harus angka.")
                enter_break()
                clear_terminal()
                continue

            claim = claim_lahan_for_surveyor(conn, lahan_id, surveyor_id)
            if not claim:
                print("Lahan ini sudah diambil surveyor lain atau tidak ada.")
                enter_break()
                clear_terminal()
                continue

            print("- Ketinggian (0-3000)")
            print("- pH (0-14)")
            print("- Nutrisi (0-100)")
            print("- Kelembapan (0-100)")
            print("- Iklim")
            
            try:
                real_ketinggian = int(input("Ketinggian Real Lahan (meter): ").strip())
                if real_ketinggian > 3000:
                    print("Ketinggian tidak boleh lebih dari 3000.")
                    enter_break()
                    clear_terminal()
                    continue
                update_lahan_ketinggian(conn, lahan_id, real_ketinggian)
            except ValueError:
                print("Ketinggian harus angka.")
                enter_break()
                clear_terminal()
                continue

            iklim_list = get_all_iklim(conn)
            if not iklim_list:
                print("Belum ada data iklim, isi dulu tabel iklim.")
                enter_break()
                clear_terminal()
                continue

            print("\nPilih Iklim:")
            for iklim_id, jenis_cuaca in iklim_list:
                print(f"  {iklim_id}. {jenis_cuaca}")

            try:
                id_iklim = int(input("ID Iklim: ").strip())
            except ValueError:
                print("ID iklim harus angka.")
                enter_break()
                clear_terminal()
                continue

            kondisi_tanah = str(input("Kondisi tanah (gembur/lumpur/subur): ").strip())
            ph = float(input("pH (misal: 6.0): ").strip())
            if ph > 14:
                print("pH tidak boleh lebih dari 14.")
                enter_break()
                clear_terminal()
                continue
            nutrisi = float(input("Nutrisi (misal: 7.0): ").strip())
            if nutrisi > 100:
                print("Nutrisi tidak boleh lebih dari 100.")
                enter_break()
                clear_terminal()
                continue
            kelembapan = float(input("Kelembapan (misal: 6.0): ").strip())
            if kelembapan > 100:
                print("Kelembapan tidak boleh lebih dari 100.")
                enter_break()
                clear_terminal()
                continue

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO kondisi_tanah (kondisi_tanah, ph, kandungan_nutrisi, kelembapan)
                    VALUES (%s, %s, %s, %s)
                    RETURNING kondisi_tanah_id
                    """,
                    (kondisi_tanah, ph, nutrisi, kelembapan),
                )
                row = cur.fetchone()

            if not row or row[0] is None:
                print("Gagal menambahkan kondisi tanah.")
                enter_break()
                clear_terminal()
                continue

            id_tanah = row[0]
            jumlah_survey = hitung_survey(conn, lahan_id)

            if jumlah_survey < 2:
                survey_id = add_survey_data(
                        conn=conn,
                        id_lahan=lahan_id,
                        id_user_surveyor=surveyor_id,
                        id_iklim=id_iklim,
                        id_tanah=id_tanah,
                        id_tanaman=None,
                        status_survey="waiting"
                    )
                print(
                    f"Data survey ke-{jumlah_survey + 1} tersimpan. "
                    "Rekomendasi tanaman akan muncul setelah 3 kali survey."
                )
                enter_break()
                clear_terminal()
                continue
            
            print("\n=== HASIL ANALISIS & REKOMENDASI ===")
            recom, others = cocokin_tanaman(conn, real_ketinggian, ph, nutrisi, kelembapan, id_iklim)
            cuaca = get_iklim_by_id(conn, id_iklim)
            
            print(f"Kriteria: Alt={real_ketinggian}, pH={ph}, Nut={nutrisi}, Hum={kelembapan}, Iklim={cuaca[1]}")
            
            if recom:
                print(f"\nTanaman yang direkomendasikan ({len(recom)}):")
                for r_id, r_nama in recom:
                    print(f"  - ID {r_id}: {r_nama}")
            else:
                print("\nTidak ada tanaman yang pas dengan kriteria.")

            print(f"\nTanaman Lainnya ({len(others)}):")
            # Nampilin 5 rekomendasi lainnya
            for o_id, o_nama in others[:5]:
                print(f"  - ID {o_id}: {o_nama}")
            if len(others) > 5:
                print(f"  ... dan {len(others)-5} lainnya.")

            id_tanaman = None
            
            print("\nOpsi:")
            print("1. Pilih dari Rekomendasi")
            print("2. Kosongkan (Tidak merekomendasikan)")
            
            sub_pilih = input("Pilih (1-2): ").strip()

            if sub_pilih == "1" and recom:
                try:
                    id_tanaman = int(input("Masukkan ID Tanaman Rekomendasi: "))
                except ValueError: pass
            elif sub_pilih == "2":
                tipe_list = get_all_tipe_tanaman(conn)
                print("\nTipe Tanaman:")
                for tipe_id, jenis in tipe_list:
                    print(f"  {tipe_id}. {jenis}")
                try:
                    id_tipe = int(input("ID Tipe: "))
                    t_list = get_tanaman_by_tipe(conn, id_tipe)
                    for t_id, t_nama in t_list:
                        print(f"  {t_id}. {t_nama}")
                    id_tanaman = int(input("ID Tanaman: "))
                except ValueError: pass
            
            # simpan ke survey_data
            survey_id = add_survey_data(
                conn=conn,
                id_lahan=lahan_id,
                id_user_surveyor=surveyor_id,
                id_iklim=id_iklim,
                id_tanah=id_tanah,
                id_tanaman=id_tanaman,
                status_survey="selesai",
            )

            if survey_id is not None:
                print(
                    f"Survey baru dengan ID {survey_id} berhasil ditambahkan "
                    f"untuk lahan {lahan_id}."
                )
                
            else:
                print("Gagal menambahkan survey.")
            enter_break()

        elif pilihan == "2":
            menu_update_profile(conn, user)
            enter_break()

        elif pilihan == "0":
            print("Logout dari surveyor.")
            break
        else:
            print("Pilihan tidak valid, coba lagi.")
            enter_break()


def menu_update_profile(conn, user: dict[str, str | int]) -> None:
    """
    Menu update profil untuk user
    """
    user_id = user["id"]
    current = get_user_by_id(conn, user_id)

    if not current:
        print("Data user tidak ditemukan.")
        return

    print("\n=== Update Profil Saya ===")
    print(f"Username (tidak bisa diubah): {current['username']}")
    print(f"Nama sekarang     : {display(current['name'])}")
    print(f"Email sekarang    : {display(current['email'])}")
    print(f"No. Telp sekarang : {display(current['no_telp'])}")
    print(f"ID Alamat sekarang: {display(current['id_alamat'])}")

    print("\nKosongkan (Enter) jika tidak ingin mengubah field tertentu.\n")

    new_name = input_optional(f"Nama baru [{current['name']}]: ", current["name"])
    new_email = input_optional(f"Email baru [{current['email']}]: ", current["email"])
    new_no_telp = input_optional(f"No. Telp baru [{current['no_telp']}]: ", current["no_telp"])

    pw_raw = input("Password baru (kosongkan jika tidak diubah): ").strip()
    new_password = pw_raw or None

    ubah_alamat = input("Ingin mengubah alamat? (y/n): ").strip().lower()
    id_alamat_baru = current["id_alamat"]

    if ubah_alamat == "y":
        id_alamat_baru = buat_alamat(conn)


    updated = update_user_profile(
        conn,
        user_id=user_id,
        name=new_name,
        email=new_email,
        no_telp=new_no_telp,
        password=new_password,
        id_alamat=id_alamat_baru,
    )

    if updated:
        print("Profil berhasil diperbarui.")
        user["username"] = current["username"]
    else:
        print("Tidak ada perubahan pada profil.")

# Authentikasi

def signup(conn: psycopg2.extensions.connection) -> None:
    """
    Registrasi user baru
    """
    print("Mendaftar user baru...")
    role = None
    while role not in ["surveyor", "petani"]:
        role = input("Daftar sebagai (surveyor/petani): ").strip().lower()
        if role not in ["surveyor", "petani"]:
            print("Role harus 'surveyor' atau 'petani'.")

    name = input("Nama lengkap: ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    email = input("Email (boleh kosong): ").strip() or None
    no_telp = input("No. Telp (boleh kosong): ").strip() or None
    isi_alamat = input("Input alamat mu sekarang? (y/n): ").strip().lower()
    id_alamat = None
    if isi_alamat == "y":
        id_alamat = buat_alamat(conn)

    cur = conn.cursor()

    # Cek username 
    cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        print("Username sudah terdaftar, coba username lain.")
        cur.close()
        return

    # Ambil id_roles
    cur.execute(
        "SELECT role_id FROM roles WHERE LOWER(nama_role) = LOWER(%s)",
        (role,),
    )
    row = cur.fetchone()
    if not row:
        print(f"Role '{role}' belum ada di tabel roles.")
        cur.close()
        return
    role_id = row[0]

    cur.execute(
        """
        INSERT INTO users (name, username, password, email, no_telp, id_alamat)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING user_id;
        """,
        (name, username, password, email, no_telp, id_alamat),
    )
    user_row = cur.fetchone()
    if not user_row:
        conn.rollback()
        cur.close()
        print("Gagal membuat user.")
        return

    user_id = user_row[0]

    cur.execute(
        """
        INSERT INTO user_roles (id_user, id_role)
        VALUES (%s, %s)
        """,
        (user_id, role_id),
    )

    conn.commit()
    cur.close()
    print(f"User {username} berhasil didaftarkan sebagai {role}.")

    if input("Mau lanjut ke login? (y/n): ").strip().lower() == "y":
        user = login(conn)
        if user:
            role = user["role"]
            if role == "admin":
                menu_admin(conn, user)
            elif role == "petani":
                menu_petani(conn, user)
            elif role == "surveyor":
                menu_surveyor(conn, user)

def login(conn: psycopg2.extensions.connection) -> Optional[dict[str, str | int]]:
    """
    Login user baru
    """
    print("Logging in...")
    role = None
    while role not in ["admin", "surveyor", "petani"]:
        role = input("Login sebagai (admin/surveyor/petani): ").strip().lower()
        if role not in ["admin", "surveyor", "petani"]:
            print("Role harus salah satu dari: admin, surveyor, petani")

    username = input("Username: ").strip()
    password = input("Password: ").strip()

    cur = conn.cursor()
    # Cek user password role
    cur.execute(
        """
        SELECT
            u.user_id,
            u.username,
            u.name,
            r.nama_role
        FROM users u
        JOIN user_roles ur ON ur.id_user = u.user_id
        JOIN roles r       ON r.role_id = ur.id_role
        WHERE u.username = %s
        AND u.password = %s
        AND LOWER(r.nama_role) = LOWER(%s);
        """,
        (username, password, role),
    )

    row = cur.fetchone()
    cur.close()

    if row:
        user_id, username_db, name_db, role_db = row
        user = {
            "id": user_id,
            "username": username_db,
            "name": name_db,
            "role": role_db.lower(),
        }
        print(f"Login berhasil! Anda masuk sebagai {role_db}: {username_db}")
        return user
    else:
        print("Login gagal! Username/password/role tidak cocok.")
        return None

# Main

if __name__ == '__main__':
    conn = get_connection()
    clear_terminal()
    try:
        while True:
            clear_terminal()
            header()
            print("1. Login")
            print("2. Registrasi user baru")
            print("0. Keluar")

            pilihan = input("Pilih menu: ").strip()

            if pilihan == "1":
                user = login(conn)
                if not user:
                    # Login gagal, kembali ke menu utama
                    continue
                role = user.get('role')
                if role == "admin":
                    menu_admin(conn, user)
                elif role == "petani":
                    menu_petani(conn, user)
                elif role == "surveyor":
                    menu_surveyor(conn, user)
                else:
                    print("Role tidak dikenali.")


            elif pilihan == "2":
                signup(conn)
            elif pilihan == "0":
                print("Keluar dari program")
                clear_terminal()
                break
            else:
                print("Pilihan tidak valid, coba lagi")
    except KeyboardInterrupt:
        conn.close()
        print("\nKeluar dari program secara paksa")
        exit(0)
    finally:
        conn.close()
