# Smart Asset Monitoring berbasis IoT + GIS

Studi kasus kegiatan **Informatics Practitioner Lecture Series 2026**
(tema: *Career and Competition in Industrial Era with GIS*, pemateri Bapak Widi Prima Depa,
Asset Management GIS Analyst).

## 1. Latar belakang
Pemateri menjelaskan bahwa GIS banyak dipakai untuk **pengelolaan aset**, dan bahwa data yang
terorganisasi serta terintegrasi membantu analisis dan pengambilan keputusan. Di sisi lain,
kondisi aset (pompa, genset, trafo, lampu jalan) di lapangan biasanya baru diketahui setelah rusak.

Studi kasus ini menggabungkan keduanya: **sensor IoT** mengirim kondisi aset secara berkala,
lalu **analisis spasial** menentukan aset mana yang harus ditangani lebih dulu dan tim teknisi
mana yang paling dekat.

## 2. Keterkaitan dengan materi
| Poin dari materi | Wujud di proyek ini |
|---|---|
| Pengelolaan aset & integrasi data | Data sensor (IoT) digabung dengan data lokasi aset (`data/assets.csv`) |
| Analisis spasial | Jarak haversine & pemilihan tim terdekat (`iotgis/geo.py`) |
| SQL, Python, basis data | SQLite + Python (Flask, folium) |
| QGIS / open source | Output GeoJSON (`outputs/assets_status.geojson`) bisa dibuka langsung di QGIS |
| Portofolio & proyek nyata | Repositori ini |

## 3. Arsitektur
```
ESP32 (suhu, getaran, baterai) --HTTP/JSON--> Flask API --> SQLite
                                                    |
                                   report.py (analisis spasial)
                                                    |
                        map.html  |  assets_status.geojson  |  work_orders.csv
```

## 4. Aturan status aset
| Status | Kondisi |
|---|---|
| CRITICAL | suhu >= 80 C atau getaran >= 7 mm/s |
| WARNING | suhu >= 65 C, getaran >= 4 mm/s, atau baterai < 20% |
| NORMAL | selainnya |

Ambang batas ada di `iotgis/rules.py` dan bersifat contoh; sesuaikan dengan spesifikasi
aset yang sebenarnya.

## 5. Cara menjalankan (tanpa perangkat keras)
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Terminal 1: server penerima data
python -m iotgis.server

# Terminal 2: simulator node IoT, lalu analisis
python -m iotgis.simulator --rounds 3
python -m iotgis.report

# Uji unit
pytest
```
Hasil ada di folder `outputs/`: buka `map.html` di browser, atau tarik
`assets_status.geojson` ke QGIS.

## 6. Menggunakan ESP32 sungguhan
Buka `firmware/esp32_asset_node/esp32_asset_node.ino` di Arduino IDE, isi SSID, password,
IP server, dan `ASSET_ID`, lalu unggah. Sensor yang dipakai: DS18B20, MPU6050, dan pembagi
tegangan untuk baterai. Server dan ESP32 harus berada di jaringan yang sama.

## 7. Contoh hasil
```
Ringkasan status: {'NORMAL': 6, 'WARNING': 2, 'CRITICAL': 2}
  P1 TRF-03 CRITICAL -> Tim Teknisi Selatan (2.79 km)
  P1 PMP-02 CRITICAL -> Tim Teknisi Pusat (3.12 km)
  P2 LMP-02 WARNING  -> Tim Teknisi Selatan (1.12 km)
  P2 GEN-02 WARNING  -> Tim Teknisi Selatan (1.74 km)
```
Koordinat aset dan tim adalah data fiktif di sekitar Kota Bengkulu untuk demonstrasi.

## 8. Pengembangan lanjutan
- Ganti HTTP dengan MQTT (broker Mosquitto) untuk node berdaya rendah.
- Jarak tempuh nyata lewat routing jalan (OSRM) menggantikan jarak garis lurus.
- Deteksi anomali dengan model machine learning dari riwayat telemetry.
- Dasbor web real-time dan notifikasi Telegram untuk status CRITICAL.
