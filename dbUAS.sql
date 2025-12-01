CREATE TABLE provinsi (
    provinsi_id   SERIAL PRIMARY KEY,
    nama_provinsi VARCHAR(150) NOT NULL
);

CREATE TABLE kota (
    kota_id   SERIAL PRIMARY KEY,
    nama_kota VARCHAR(100)
);

CREATE TABLE kecamatan (
    kecamatan_id   SERIAL PRIMARY KEY,
    nama_kecamatan VARCHAR(200)
);

CREATE TABLE alamat (
    alamat_id     SERIAL PRIMARY KEY,
    nama_jalan    VARCHAR(100) NOT NULL,
    id_kota       INTEGER REFERENCES kota(kota_id),
    id_kecamatan  INTEGER REFERENCES kecamatan(kecamatan_id),
    id_provinsi   INTEGER REFERENCES provinsi(provinsi_id)
);

CREATE TABLE IF NOT EXISTS users(
    user_id SERIAL PRIMARY KEY NOT NULL,
    name VARCHAR(200) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(20) NOT NULL,
    email VARCHAR(50) UNIQUE NULL,
    no_telp VARCHAR(13) UNIQUE NULL,
    id_alamat INTEGER REFERENCES alamat(alamat_id),
    pembuatan TIMESTAMP default now()::DATE
);

CREATE TABLE IF NOT EXISTS roles(
    role_id SERIAL PRIMARY KEY NOT NULL,
    nama_role VARCHAR(100) NOT NULL,
    pembuatan TIMESTAMP default now()::DATE
);

CREATE TABLE IF NOT EXISTS user_roles(
    user_role_id SERIAL PRIMARY KEY NOT NULL,
    id_user INTEGER REFERENCES users(user_id),
    id_role INTEGER REFERENCES roles(role_id)
);

CREATE TABLE IF NOT EXISTS iklim(
    iklim_id SERIAL PRIMARY KEY,
    jenis_cuaca VARCHAR(20) NOT NULL
);

INSERT INTO iklim(jenis_cuaca) VALUES ('kemarau');
INSERT INTO iklim(jenis_cuaca) VALUES ('penghujan');

CREATE TABLE IF NOT EXISTS kondisi_tanah(
    kondisi_tanah_id SERIAL PRIMARY KEY,
    kondisi_tanah VARCHAR(20) NOT NULL,
    ph FLOAT NOT NULL,
    kandungan_nutrisi FLOAT NOT NULL,
    kelembapan FLOAT NOT NULL
);

INSERT INTO users (name, username, password) VALUES
('Admin Ejak', 'ejak', '23'),
('Petani Divo', 'divo', '23'),
('Surveyor Zera', 'zera', '23');

-- Insert roles
INSERT INTO roles (nama_role) VALUES ('admin'), ('petani'), ('surveyor');

-- Admin Ejak
INSERT INTO user_roles (id_user, id_role)
VALUES (
    (SELECT user_id FROM users WHERE username = 'ejak'),
    (SELECT role_id FROM roles WHERE nama_role = 'admin')
);

-- Petani Divo
INSERT INTO user_roles (id_user, id_role)
VALUES (
    (SELECT user_id FROM users WHERE username = 'divo'),
    (SELECT role_id FROM roles WHERE nama_role = 'petani')
);

-- Surveyor Zera
INSERT INTO user_roles (id_user, id_role)
VALUES (
    (SELECT user_id FROM users WHERE username = 'zera'),
    (SELECT role_id FROM roles WHERE nama_role = 'surveyor')
);

CREATE TABLE IF NOT EXISTS lahan (
    lahan_id SERIAL PRIMARY KEY,
    id_user_surveyor INTEGER REFERENCES users(user_id),
    id_user_petani INTEGER REFERENCES  users(user_id),
    id_alamat INTEGER REFERENCES alamat(alamat_id),
    ketinggian REAL NULL
);

CREATE TABLE IF NOT EXISTS tipe_tanaman(
    tipe_tanaman_id SERIAL PRIMARY KEY,
    jenis_tanaman VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS tanaman(
    tanaman_id SERIAL PRIMARY KEY,
    id_tipe_tanaman INTEGER REFERENCES tipe_tanaman(tipe_tanaman_id),
    nama VARCHAR(100) NOT NULL,
    ketinggian float NOT NULL,
    ph float NOT NULL,
    kandungan_nutrisi float NOT NULL,
    kondisi_tanah VARCHAR(50) NOT NULL,
    iklim_id INTEGER REFERENCES iklim(iklim_id),
    kelembapan float NOT NULL
);

INSERT INTO tipe_tanaman(jenis_tanaman) VALUES
    ('Holticultura'),
    ('Agrivultura'),
    ('Umbi-Umbian');

INSERT INTO tanaman (
    id_tipe_tanaman,
    nama,
    ketinggian,
    ph,
    kandungan_nutrisi,
    kondisi_tanah,
    iklim_id,
    kelembapan
) VALUES
    (1, 'Cabai',      400, 6.0, 70, 'Gembur', 1, 65),
    (1, 'Tomat',      600, 6.5, 75, 'Gembur', 2, 70),
    (1, 'Kol',       1000, 6.8, 80, 'Lempung', 2, 75),
    (1, 'Sawi',       500, 6.5, 72, 'Gembur', 2, 70),
    (1, 'Selada',     900, 6.7, 78, 'Gembur', 2, 80);

INSERT INTO tanaman (
    id_tipe_tanaman,
    nama,
    ketinggian,
    ph,
    kandungan_nutrisi,
    kondisi_tanah,
    iklim_id,
    kelembapan
) VALUES
    (2, 'Padi',       100, 5.5, 85, 'Lumpur', 2, 90),
    (2, 'Jagung',     200, 6.0, 70, 'Lempung', 1, 60),
    (2, 'Gandum',     500, 6.5, 75, 'Lempung', 1, 55),
    (2, 'Kedelai',    300, 6.2, 72, 'Gembur', 1, 65);

INSERT INTO tanaman (
    id_tipe_tanaman,
    nama,
    ketinggian,
    ph,
    kandungan_nutrisi,
    kondisi_tanah,
    iklim_id,
    kelembapan
) VALUES
    (3, 'Kentang',    900, 5.8, 80, 'Lempung', 2, 75),
    (3, 'Singkong',   100, 5.5, 60, 'Berpasir', 1, 55),
    (3, 'Ubi Jalar',  200, 5.6, 65, 'Gembur', 1, 60),
    (3, 'Talas',      150, 5.4, 70, 'Lumpur', 2, 85);

INSERT INTO
    tanaman (
        id_tipe_tanaman,
        nama,
        ketinggian,
        ph,
        kandungan_nutrisi,
        kondisi_tanah,
        kelembapan,
        iklim_id
    )
VALUES
    (1, 'Padi Gogo', 500, 6.0, 70, 'Gembur', 60, 1),
    (1, 'Padi Sawah Irigasi', 100, 7.0, 80, 'Lumpur', 80, 1);

INSERT INTO
    tanaman (
        id_tipe_tanaman,
        nama,
        ketinggian,
        ph,
        kandungan_nutrisi,
        kondisi_tanah,
        kelembapan,
        iklim_id
    )
VALUES
    (2, 'Jagung Manis', 300, 6.5, 75, 'Lumpur', 70, 1),
    (2, 'Jagung Hibrida', 200, 6.0, 80, 'Lumpur', 65, 1);

INSERT INTO
    tanaman (
        id_tipe_tanaman,
        nama,
        ketinggian,
        ph,
        kandungan_nutrisi,
        kondisi_tanah,
        kelembapan,
        iklim_id
    )
VALUES
    (3, 'Wortel', 1200, 6.0, 80, 'Gembur', 85, 2),
    (3, 'Kentang', 1500, 5.5, 85, 'Lumpur', 90, 2),
    (3, 'Kubis', 1000, 6.5, 75, 'Gembur', 80, 2),
    (3, 'Bayam', 100, 7.0, 60, 'Gembur', 70, 1);

CREATE TABLE IF NOT EXISTS survey_data (
    survey_id SERIAL PRIMARY KEY,
    id_user_surveyor INTEGER REFERENCES users(user_id),
    id_lahan INTEGER REFERENCES lahan(lahan_id),
    id_iklim INTEGER REFERENCES iklim(iklim_id),
    id_tanah INTEGER REFERENCES  kondisi_tanah(kondisi_tanah_id),
    status_survey VARCHAR(15) default 'waiting',
    id_tanaman INTEGER REFERENCES tanaman(tanaman_id),
    tanggal_survey DATE DEFAULT now()::DATE
);

CREATE TABLE IF NOT EXISTS penanaman (
    penanaman_id SERIAL PRIMARY KEY,
    id_survey INTEGER REFERENCES survey_data(survey_id),
    tanggal_penanaman DATE
);