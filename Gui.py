import io
import tkinter as tk
import unittest
from datetime import date
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from keuangan.fileio import baca_data, baca_teks, tambah_data, tulis_laporan
from keuangan.processing import AnalisisPengeluaran, buat_record, format_rupiah, susun_laporan
from keuangan.testing import TestKeuangan
from keuangan.validasi import DataTidakValidError
from main import PATH_DATA, PATH_LAPORAN, siapkan_file

# ---------- Tema warna dan font ----------
BG = "#F4F6FA"       
CARD = "#FFFFFF"      
NAVY = "#1F3A5F"     
ACCENT = "#2F6FDE"    
TEXT = "#1B2430"
MUTED = "#6B7685"
STRIPE = "#F3F6FB"    
WARNA_BAR = ["#2F6FDE", "#16A085", "#E67E22", "#8E44AD", "#C0392B", "#7F8C8D"]
FONT = ("Segoe UI", 10)
FONT_KECIL = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 10, "bold")

KATEGORI_DEFAULT = ["Makanan", "Transport", "Belanja", "Hiburan", "Lainnya"]
JUDUL_KOLOM = {"tanggal": "Tanggal", "kategori": "Kategori",
               "keterangan": "Keterangan", "jumlah": "Jumlah"}


class AplikasiKeuangan(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Pencatat Pengeluaran Harian")
        self.geometry("1150x760")
        self.minsize(1000, 680)
        self.configure(bg=BG)

        self.daftar = []                   
        self.urut_kolom = "tanggal"        
        self.urut_menurun = False

        self._buat_gaya()
        self._buat_tampilan()
        self.muat_data()

    
    # Tampilan
    def _buat_gaya(self):
        gaya = ttk.Style(self)
        gaya.theme_use("clam")
        gaya.configure(".", font=FONT, background=BG, foreground=TEXT)
        gaya.configure("TLabel", background=BG)
        gaya.configure("Card.TFrame", background=CARD)
        gaya.configure("Card.TLabel", background=CARD)
        gaya.configure("Judul.TLabel", font=("Segoe UI", 18, "bold"), foreground=NAVY)
        gaya.configure("Sub.TLabel", foreground=MUTED)
        gaya.configure("Seksi.TLabel", font=("Segoe UI", 11, "bold"), foreground=NAVY, background=CARD)
        gaya.configure("Ket.TLabel", font=FONT_KECIL, foreground=MUTED, background=CARD)
        gaya.configure("Angka.TLabel", font=("Segoe UI", 16, "bold"), foreground=NAVY, background=CARD)
        gaya.configure("TButton", padding=(10, 6))
        gaya.configure("Accent.TButton", background=ACCENT, foreground="white", padding=(10, 8),
                       font=FONT_BOLD)
        gaya.map("Accent.TButton", background=[("active", "#2559B5")])
        gaya.configure("Treeview", rowheight=27, background=CARD, fieldbackground=CARD, borderwidth=0)
        gaya.configure("Treeview.Heading", font=FONT_BOLD, background=NAVY, foreground="white",
                       padding=(6, 6))
        gaya.map("Treeview.Heading", background=[("active", "#2D4F7E")])
        gaya.map("Treeview", background=[("selected", "#CFE0FA")], foreground=[("selected", TEXT)])

    def _buat_tampilan(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # Header
        header = ttk.Frame(self, padding=(20, 14, 20, 6))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(header, text="Pencatat Pengeluaran Harian", style="Judul.TLabel").pack(anchor="w")
        ttk.Label(header, text="Catat, cari, dan analisis pengeluaran Anda", style="Sub.TLabel").pack(anchor="w")

        self._buat_form()
        self._buat_panel_utama()

        # Status bar
        self.var_status = tk.StringVar(value="Siap.")
        ttk.Label(self, textvariable=self.var_status, style="Sub.TLabel",
                  padding=(20, 4)).grid(row=2, column=0, columnspan=2, sticky="ew")

    def _buat_form(self):
        kartu = ttk.Frame(self, style="Card.TFrame", padding=18)
        kartu.grid(row=1, column=0, sticky="ns", padx=(20, 10), pady=10)
        ttk.Label(kartu, text="Tambah Pengeluaran", style="Seksi.TLabel").pack(anchor="w", pady=(0, 10))

        self.var_tanggal = tk.StringVar(value=date.today().isoformat())
        self.var_kategori = tk.StringVar()
        self.var_ket = tk.StringVar()
        self.var_jumlah = tk.StringVar()

        def baris(teks, widget):
            ttk.Label(kartu, text=teks, style="Ket.TLabel").pack(anchor="w", pady=(8, 2))
            widget.pack(fill="x")
            return widget

        baris("Tanggal (YYYY-MM-DD)", ttk.Entry(kartu, textvariable=self.var_tanggal, width=28))
        self.cmb_kategori = baris("Kategori", ttk.Combobox(kartu, textvariable=self.var_kategori, width=26))
        baris("Keterangan", ttk.Entry(kartu, textvariable=self.var_ket))
        self.ent_jumlah = baris("Jumlah (Rp)", ttk.Entry(kartu, textvariable=self.var_jumlah))
        self.ent_jumlah.bind("<Return>", lambda _e: self.simpan())

        ttk.Label(kartu, text="Contoh jumlah: 15000 atau 15.000", style="Ket.TLabel").pack(anchor="w", pady=(4, 12))
        ttk.Button(kartu, text="Simpan", style="Accent.TButton", command=self.simpan).pack(fill="x")
        ttk.Button(kartu, text="Bersihkan Form", command=self.bersihkan).pack(fill="x", pady=(8, 0))

    def _buat_panel_utama(self):
        panel = ttk.Frame(self)
        panel.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=10)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        # Toolbar: filter, pencarian, dan tombol aksi
        bar = ttk.Frame(panel)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(bar, text="Kategori").pack(side="left")
        self.var_filter = tk.StringVar(value="Semua")
        self.cmb_filter = ttk.Combobox(bar, textvariable=self.var_filter, state="readonly", width=14)
        self.cmb_filter.pack(side="left", padx=(6, 14))
        self.cmb_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        ttk.Label(bar, text="Cari").pack(side="left")
        self.var_cari = tk.StringVar()
        self.var_cari.trace_add("write", lambda *_a: self.refresh())
        ttk.Entry(bar, textvariable=self.var_cari, width=16).pack(side="left", padx=6)
        ttk.Button(bar, text="Pengujian", command=self.jalankan_pengujian).pack(side="right")
        ttk.Button(bar, text="Buat Laporan", command=self.buat_laporan).pack(side="right", padx=6)
        ttk.Button(bar, text="Hapus", command=self.hapus).pack(side="right")

        #Tabel data
        isi = ttk.Frame(panel, style="Card.TFrame")
        isi.grid(row=1, column=0, sticky="nsew")
        isi.columnconfigure(0, weight=1)
        isi.rowconfigure(0, weight=1)
        kolom = ("no", "tanggal", "kategori", "keterangan", "jumlah")
        self.tabel = ttk.Treeview(isi, columns=kolom, show="headings", selectmode="extended")
        self.tabel.heading("no", text="No")
        for k, judul in JUDUL_KOLOM.items():
            self.tabel.heading(k, text=judul, command=lambda kol=k: self.urutkan(kol))
        self.tabel.column("no", width=45, anchor="center", stretch=False)
        self.tabel.column("tanggal", width=110, anchor="center", stretch=False)
        self.tabel.column("kategori", width=120, stretch=False)
        self.tabel.column("keterangan", width=300)
        self.tabel.column("jumlah", width=120, anchor="e", stretch=False)
        self.tabel.tag_configure("ganjil", background=STRIPE)
        gulung = ttk.Scrollbar(isi, orient="vertical", command=self.tabel.yview)
        self.tabel.configure(yscrollcommand=gulung.set)
        self.tabel.grid(row=0, column=0, sticky="nsew")
        gulung.grid(row=0, column=1, sticky="ns")
        self.tabel.bind("<Delete>", lambda _e: self.hapus())

        #Kartu ringkasan
        ringkas = ttk.Frame(panel)
        ringkas.grid(row=2, column=0, sticky="ew", pady=10)
        self.var_ringkasan = {}
        for i, (kunci, teks) in enumerate([("total", "Total pengeluaran"), ("rata", "Rata-rata per hari"),
                                           ("boros", "Kategori terboros"), ("jumlah", "Jumlah catatan")]):
            ringkas.columnconfigure(i, weight=1, uniform="kartu")
            kartu = ttk.Frame(ringkas, style="Card.TFrame", padding=(14, 10))
            kartu.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
            ttk.Label(kartu, text=teks, style="Ket.TLabel").pack(anchor="w")
            var = tk.StringVar(value="-")
            ttk.Label(kartu, textvariable=var, style="Angka.TLabel").pack(anchor="w")
            self.var_ringkasan[kunci] = var

        #Grafik batang per kategori
        kartu_grafik = ttk.Frame(panel, style="Card.TFrame", padding=(14, 10))
        kartu_grafik.grid(row=3, column=0, sticky="ew")
        ttk.Label(kartu_grafik, text="Pengeluaran per Kategori", style="Seksi.TLabel").pack(anchor="w")
        self.kanvas = tk.Canvas(kartu_grafik, height=180, bg=CARD, highlightthickness=0)
        self.kanvas.pack(fill="x", pady=(6, 0))
        self.kanvas.bind("<Configure>", lambda _e: self.gambar_grafik(self.analisis_tampil))
        self.analisis_tampil = AnalisisPengeluaran([])

    # Data
    def muat_data(self):
        self.daftar = baca_data(PATH_DATA)
        kategori = sorted(set(KATEGORI_DEFAULT) | {p.kategori for p in self.daftar})
        self.cmb_kategori["values"] = kategori
        ada = sorted({p.kategori for p in self.daftar})
        self.cmb_filter["values"] = ["Semua"] + ada
        if self.var_filter.get() not in self.cmb_filter["values"]:
            self.var_filter.set("Semua")
        self.refresh()

    def data_terfilter(self):
        hasil = list(enumerate(self.daftar))
        kategori = self.var_filter.get()
        kata = self.var_cari.get().strip().lower()
        if kategori != "Semua":
            hasil = [ip for ip in hasil if ip[1].kategori == kategori]
        if kata:
            hasil = list(filter(lambda ip: kata in ip[1].keterangan.lower(), hasil))
        kunci = {"tanggal": lambda ip: ip[1].tanggal,
                 "kategori": lambda ip: ip[1].kategori.lower(),
                 "keterangan": lambda ip: ip[1].keterangan.lower(),
                 "jumlah": lambda ip: ip[1].jumlah}[self.urut_kolom]
        return sorted(hasil, key=kunci, reverse=self.urut_menurun)

    def refresh(self):
        terfilter = self.data_terfilter()
        self.tabel.delete(*self.tabel.get_children())
        for nomor, (indeks, p) in enumerate(terfilter, start=1):
            self.tabel.insert("", "end", iid=str(indeks),
                              values=(nomor, p.tanggal, p.kategori, p.keterangan, format_rupiah(p.jumlah)),
                              tags=("ganjil",) if nomor % 2 == 0 else ())
        # tanda panah pada judul kolom yang dipakai mengurutkan
        for k, judul in JUDUL_KOLOM.items():
            panah = (" \u25BC" if self.urut_menurun else " \u25B2") if k == self.urut_kolom else ""
            self.tabel.heading(k, text=judul + panah)

        analisis = AnalisisPengeluaran([p for _, p in terfilter])
        self.analisis_tampil = analisis
        terboros = analisis.kategori_terboros()
        self.var_ringkasan["total"].set(format_rupiah(analisis.total()))
        self.var_ringkasan["rata"].set(format_rupiah(analisis.rata_rata_harian()))
        self.var_ringkasan["boros"].set(terboros[0] if terboros else "-")
        self.var_ringkasan["jumlah"].set(str(len(terfilter)))
        self.gambar_grafik(analisis)
        self.status(f"Menampilkan {len(terfilter)} dari {len(self.daftar)} catatan.")

    def gambar_grafik(self, analisis):
        c = self.kanvas
        c.delete("all")
        rekap = sorted(analisis.rekap_per_kategori().items(), key=lambda it: it[1], reverse=True)[:6]
        lebar = max(c.winfo_width(), 500)
        if not rekap:
            c.create_text(lebar / 2, 80, text="Belum ada data untuk ditampilkan", fill=MUTED, font=FONT)
            return
        terbesar = rekap[0][1] or 1
        x0, x1 = 100, lebar - 130
        for i, (kategori, jumlah) in enumerate(rekap):
            y = 8 + i * 28
            panjang = max(3, (x1 - x0) * jumlah / terbesar)
            c.create_text(4, y + 10, text=kategori, anchor="w", fill=TEXT, font=FONT)
            c.create_rectangle(x0, y, x0 + panjang, y + 20, fill=WARNA_BAR[i % len(WARNA_BAR)], outline="")
            c.create_text(x0 + panjang + 8, y + 10, text=format_rupiah(jumlah), anchor="w", fill=TEXT, font=FONT_KECIL)

    # Aksi pengguna
    def status(self, teks):
        self.var_status.set(teks)

    def urutkan(self, kolom):
        if kolom == self.urut_kolom:
            self.urut_menurun = not self.urut_menurun
        else:
            self.urut_kolom, self.urut_menurun = kolom, False
        self.refresh()

    def bersihkan(self):
        self.var_tanggal.set(date.today().isoformat())
        self.var_kategori.set("")
        self.var_ket.set("")
        self.var_jumlah.set("")

    def simpan(self):
        jumlah = self.var_jumlah.get().replace("Rp", "").replace(".", "").strip()
        try:
            catatan = buat_record(tanggal=self.var_tanggal.get().strip(), kategori=self.var_kategori.get(),
                                  keterangan=self.var_ket.get(), jumlah=jumlah)
        except DataTidakValidError as err:
            messagebox.showwarning("Data tidak valid", str(err), parent=self)
            return
        tambah_data(PATH_DATA, catatan)
        self.bersihkan()
        self.muat_data()
        self.status(f"Tersimpan: {catatan.keterangan} ({format_rupiah(catatan.jumlah)})")

    def hapus(self):
        terpilih = {int(iid) for iid in self.tabel.selection()}
        if not terpilih:
            messagebox.showinfo("Hapus data", "Pilih baris yang ingin dihapus terlebih dahulu.", parent=self)
            return
        if not messagebox.askyesno("Konfirmasi", f"Hapus {len(terpilih)} catatan terpilih?", parent=self):
            return
        sisa = [p for i, p in enumerate(self.daftar) if i not in terpilih]
        tulis_laporan(PATH_DATA, "".join(p.ke_baris() + "\n" for p in sisa))
        self.muat_data()
        self.status(f"{len(terpilih)} catatan dihapus.")

    def buat_laporan(self):
        teks = susun_laporan(AnalisisPengeluaran(self.daftar))
        tulis_laporan(PATH_LAPORAN, teks)
        self.tampilkan_teks("Laporan Pengeluaran", baca_teks(PATH_LAPORAN))
        self.status("Laporan disimpan di " + PATH_LAPORAN)

    def jalankan_pengujian(self):
        aliran = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestKeuangan)
        hasil = unittest.TextTestRunner(stream=aliran, verbosity=2).run(suite)
        self.tampilkan_teks("Hasil Pengujian", aliran.getvalue())
        self.status("Pengujian selesai: " + ("semua lulus." if hasil.wasSuccessful() else "ada yang gagal."))

    def tampilkan_teks(self, judul, isi):
        jendela = tk.Toplevel(self)
        jendela.title(judul)
        jendela.geometry("680x520")
        jendela.configure(bg=BG)
        area = ScrolledText(jendela, font=("Consolas", 10), wrap="none", bg=CARD, relief="flat", padx=12, pady=10)
        area.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        area.insert("1.0", isi)
        area.configure(state="disabled")
        ttk.Button(jendela, text="Tutup", command=jendela.destroy).pack(pady=(0, 12))


def main():
    siapkan_file()                  
    AplikasiKeuangan().mainloop()


if __name__ == "__main__":
    main()
