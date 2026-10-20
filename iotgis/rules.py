"""Aturan klasifikasi kondisi aset dari data sensor."""

TEMP_WARN, TEMP_CRIT = 65.0, 80.0          # derajat Celsius
VIB_WARN, VIB_CRIT = 4.0, 7.0              # mm/s (RMS)
BATTERY_WARN = 20.0                        # persen

REQUIRED_FIELDS = ("asset_id", "temperature", "vibration", "battery")


def classify(temperature: float, vibration: float, battery: float) -> str:
    """Kembalikan NORMAL, WARNING, atau CRITICAL."""
    if temperature >= TEMP_CRIT or vibration >= VIB_CRIT:
        return "CRITICAL"
    if temperature >= TEMP_WARN or vibration >= VIB_WARN or battery < BATTERY_WARN:
        return "WARNING"
    return "NORMAL"


def validate(payload: dict) -> list:
    """Kembalikan daftar masalah pada payload (kosong jika valid)."""
    problems = [f"field '{f}' wajib ada" for f in REQUIRED_FIELDS if f not in payload]
    if problems:
        return problems
    for f in ("temperature", "vibration", "battery"):
        if not isinstance(payload[f], (int, float)) or isinstance(payload[f], bool):
            problems.append(f"field '{f}' harus angka")
    if not problems and not 0 <= payload["battery"] <= 100:
        problems.append("battery harus 0-100")
    return problems
