CREATE TABLE users (
    user_id   SERIAL PRIMARY KEY,
    name      VARCHAR(200) NOT NULL,
    username  VARCHAR(100) UNIQUE NOT NULL,
    password  VARCHAR(100) NOT NULL,
    email     VARCHAR(100),
    no_telp   VARCHAR(20),
    alamat VARCHAR(200) NULL,
    role VARCHAR(50) NOT NULL,
    pembuatan TIMESTAMP default now()::DATE
);

CREATE TABLE lahan (
    lahan_id         SERIAL PRIMARY KEY,
    id_user_petani   INTEGER REFERENCES users(user_id),
    id_user_surveyor INTEGER REFERENCES users(user_id),
    lokasi           VARCHAR(200),
    ketinggian       REAL,
    ph FLOAT,
    kandungan_nutrisi FLOAT,
    kelembapan FLOAT,
    pembuatan TIMESTAMP default now()::DATE
);

CREATE TABLE tanaman (
    tanaman_id      SERIAL PRIMARY KEY,
    nama            VARCHAR(100) NOT NULL,
    tipe_tanaman    VARCHAR(100) NOT NULL
);

CREATE TABLE survey_data (
    survey_id        SERIAL PRIMARY KEY,
    id_lahan         INTEGER REFERENCES lahan(lahan_id),
    id_user_surveyor INTEGER REFERENCES users(user_id),
    status_survey    VARCHAR(20) DEFAULT 'waiting',
    tanggal_survey   DATE,
    hasil_survey     TEXT
);

CREATE TABLE penanaman (
    penanaman_id      SERIAL PRIMARY KEY,
    id_lahan          INTEGER REFERENCES lahan(lahan_id),
    id_tanaman        INTEGER REFERENCES tanaman(tanaman_id),
    tanggal_penanaman DATE
);
