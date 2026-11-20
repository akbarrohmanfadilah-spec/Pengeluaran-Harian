from .processing import Pengeluaran
from .validasi import DataTidakValidError


def buat_file_data(path, isi_awal=""):
    try:
        with open(path, "x", encoding="utf-8") as file:
            file.write(isi_awal)
        return True
    except FileExistsError:
        print(f"Info: file {path} sudah ada, tidak dibuat ulang")
        return False


def tambah_data(path, pengeluaran):
    with open(path, "a", encoding="utf-8") as file:
        file.write(pengeluaran.ke_baris() + "\n")


def baca_data(path):
    daftar = []
    try:
        with open(path, "r", encoding="utf-8") as file:
            for nomor, baris in enumerate(file, start=1):  # pembacaan iteratif
                if not baris.strip():
                    continue  # lewati baris kosong
                try:
                    daftar.append(Pengeluaran.dari_baris(baris))
                except DataTidakValidError as err:
                    print(f"Peringatan: baris {nomor} dilewati ({err})")
    except FileNotFoundError:
        print(f"Error: file data '{path}' belum ada. Buat dulu file datanya.")
    return daftar


def tulis_laporan(path, teks):
    with open(path, "w", encoding="utf-8") as file:
        file.write(teks)


def baca_teks(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"File '{path}' belum ada."