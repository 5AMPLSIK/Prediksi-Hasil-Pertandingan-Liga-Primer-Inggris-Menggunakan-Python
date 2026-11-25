import os
import csv
import math

folder_script = os.path.dirname(os.path.abspath(__file__))
path_csv = os.path.join(folder_script, "season-2425.csv")

data = []
with open(path_csv, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    for row in reader:
        tanggal = row.get("Date", "").strip()
        home = row.get("HomeTeam", "").strip()
        away = row.get("AwayTeam", "").strip()
        ftr = row.get("FTR", "").strip()
        fthg_str = row.get("FTHG", "").strip()
        ftag_str = row.get("FTAG", "").strip()

        if len(tanggal) == 10 and tanggal[4] == "-" and tanggal[7] == "-":
            if home and away and ftr and fthg_str.isdigit() and ftag_str.isdigit():
                hst = int(row["HST"]) if row.get("HST", "").strip().isdigit() else 4
                ast = int(row["AST"]) if row.get("AST", "").strip().isdigit() else 4

                data.append({
                    "Date": tanggal,
                    "HomeTeam": home,
                    "AwayTeam": away,
                    "FTHG": int(fthg_str),
                    "FTAG": int(ftag_str),
                    "FTR": ftr,
                    "HST": hst,
                    "AST": ast
                })

data.sort(key=lambda x: x["Date"])

print("=" * 62)
print("   SISTEM ANALISIS & PREDIKSI PERTANDINGAN EPL 2024/2025")
print("        Metode: Weighted Form & Distribusi Poisson")
print("=" * 62)
print(f"Total Dataset: {len(data)} Pertandingan")

teams = sorted({m["HomeTeam"] for m in data} | {m["AwayTeam"] for m in data})
teams_map = {team.lower(): team for team in teams}

print("\nDAFTAR TIM EPL:")
for i in range(0, len(teams), 2):
    kiri = f"{i+1:2d}. {teams[i]:<18}"
    kanan = f"{i+2:2d}. {teams[i+1]}" if i + 1 < len(teams) else ""
    print("  ", kiri, kanan)


def statistik_tim(team, venue, history):
    all_matches = [m for m in history if m["HomeTeam"] == team or m["AwayTeam"] == team]
    if len(all_matches) == 0:
        return None

    home = [m for m in history if m["HomeTeam"] == team]
    away = [m for m in history if m["AwayTeam"] == team]

    semua_gol_masuk = [m["FTHG"] for m in home] + [m["FTAG"] for m in away]
    semua_gol_kebobolan = [m["FTAG"] for m in home] + [m["FTHG"] for m in away]

    gol_masuk_all = sum(semua_gol_masuk) / len(semua_gol_masuk)
    gol_kebobolan_all = sum(semua_gol_kebobolan) / len(semua_gol_kebobolan)

    if venue == "home" and len(home) > 0:
        gol_for = sum(m["FTHG"] for m in home) / len(home)
        gol_against = sum(m["FTAG"] for m in home) / len(home)
        sot_for = sum(m["HST"] for m in home) / len(home)
    elif venue == "away" and len(away) > 0:
        gol_for = sum(m["FTAG"] for m in away) / len(away)
        gol_against = sum(m["FTHG"] for m in away) / len(away)
        sot_for = sum(m["AST"] for m in away) / len(away)
    else:
        gol_for = gol_masuk_all
        gol_against = gol_kebobolan_all
        sot_for = 4.0

    recent = all_matches[-5:]
    rec_gf = []
    rec_ga = []
    for r in recent:
        if r["HomeTeam"] == team:
            rec_gf.append(r["FTHG"])
            rec_ga.append(r["FTAG"])
        else:
            rec_gf.append(r["FTAG"])
            rec_ga.append(r["FTHG"])

    form_gf = sum(rec_gf) / len(rec_gf)
    form_ga = sum(rec_ga) / len(rec_ga)

    attack_power = (0.65 * gol_for) + (0.35 * form_gf)
    defense_weakness = (0.65 * gol_against) + (0.35 * form_ga)

    return {
        "attack": attack_power,
        "defense": defense_weakness,
        "avg_gf": round(gol_masuk_all, 2),
        "avg_ga": round(gol_kebobolan_all, 2),
        "form_gf": round(form_gf, 2),
        "sot": round(sot_for, 1)
    }


def poisson_prob(lmbda, k):
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)


def prediksi(home_team, away_team, history):
    if home_team == away_team:
        return None

    home_stats = statistik_tim(home_team, "home", history)
    away_stats = statistik_tim(away_team, "away", history)

    if home_stats is None or away_stats is None:
        return None

    if len(history) > 0:
        league_avg_home = sum(m["FTHG"] for m in history) / len(history)
        league_avg_away = sum(m["FTAG"] for m in history) / len(history)
    else:
        league_avg_home = 1.5
        league_avg_away = 1.2

    xg_home = (home_stats["attack"] * away_stats["defense"]) / max(league_avg_home, 0.5)
    xg_away = (away_stats["attack"] * home_stats["defense"]) / max(league_avg_away, 0.5)

    xg_home = min(max(xg_home, 0.2), 4.5)
    xg_away = min(max(xg_away, 0.2), 4.5)

    prob_home_win = 0.0
    prob_draw = 0.0
    prob_away_win = 0.0
    best_score = (0, 0)
    max_score_prob = -1.0

    for h in range(7):
        for a in range(7):
            p = poisson_prob(xg_home, h) * poisson_prob(xg_away, a)
            if p > max_score_prob:
                max_score_prob = p
                best_score = (h, a)
            if h > a:
                prob_home_win += p
            elif h < a:
                prob_away_win += p
            else:
                prob_draw += p

    total_p = prob_home_win + prob_draw + prob_away_win
    prob_home_win = (prob_home_win / total_p) * 100
    prob_draw = (prob_draw / total_p) * 100
    prob_away_win = (prob_away_win / total_p) * 100

    if prob_home_win >= prob_away_win and prob_home_win >= prob_draw:
        hasil = f"Home Win ({home_team} Menang)"
        kode = "H"
    elif prob_away_win > prob_home_win and prob_away_win >= prob_draw:
        hasil = f"Away Win ({away_team} Menang)"
        kode = "A"
    else:
        hasil = "Draw (Seri)"
        kode = "D"

    return {
        "home_goals": best_score[0],
        "away_goals": best_score[1],
        "xg_home": round(xg_home, 2),
        "xg_away": round(xg_away, 2),
        "prob_h": round(prob_home_win, 1),
        "prob_d": round(prob_draw, 1),
        "prob_a": round(prob_away_win, 1),
        "score_prob": round(max_score_prob * 100, 1),
        "result": hasil,
        "kode": kode,
        "home_stats": home_stats,
        "away_stats": away_stats
    }


print("\n" + "=" * 62)
print("EVALUASI AKURASI MODEL (BACKTESTING)")
print("=" * 62)

total_prediksi = 0
prediksi_benar = 0

daftar_tanggal = sorted({m["Date"] for m in data})

for tanggal in daftar_tanggal:
    history = [m for m in data if m["Date"] < tanggal]
    if len(history) < 30:
        continue

    pertandingan_hari_ini = [m for m in data if m["Date"] == tanggal]
    for row in pertandingan_hari_ini:
        hasil_prediksi = prediksi(row["HomeTeam"], row["AwayTeam"], history)
        if hasil_prediksi is None:
            continue

        total_prediksi += 1
        if hasil_prediksi["kode"] == row["FTR"]:
            prediksi_benar += 1

if total_prediksi > 0:
    akurasi = (prediksi_benar / total_prediksi) * 100
    print(f"Pertandingan Diuji : {total_prediksi} laga")
    print(f"Prediksi Tepat     : {prediksi_benar} laga")
    print(f"Akurasi Model      : {akurasi:.2f}%")

print("\n" + "=" * 62)
print("SIMULASI PREDIKSI PERTANDINGAN")
print("=" * 62)

home_in = input("Masukkan Tim Tuan Rumah : ").strip().lower()
away_in = input("Masukkan Tim Tamu       : ").strip().lower()
tanggal_input = input("Tanggal (YYYY-MM-DD, misal 2025-05-26): ").strip()

bagian_tgl = tanggal_input.split("-")
tanggal_valid = (
    len(bagian_tgl) == 3
    and len(bagian_tgl[0]) == 4 and bagian_tgl[0].isdigit()
    and len(bagian_tgl[1]) == 2 and bagian_tgl[1].isdigit()
    and len(bagian_tgl[2]) == 2 and bagian_tgl[2].isdigit()
)

if not tanggal_valid:
    print("\n[Error] Format tanggal tidak valid (gunakan YYYY-MM-DD).")
elif home_in not in teams_map or away_in not in teams_map:
    print("\n[Error] Nama tim tidak ditemukan di daftar EPL.")
elif home_in == away_in:
    print("\n[Error] Tim tuan rumah dan tamu tidak boleh sama.")
else:
    home_team = teams_map[home_in]
    away_team = teams_map[away_in]
    history = [m for m in data if m["Date"] < tanggal_input]
    hasil = prediksi(home_team, away_team, history)

    if hasil is None:
        print("\n[Info] Data historis belum mencukupi.")
    else:
        hs = hasil["home_stats"]
        aws = hasil["away_stats"]
        print("\n" + "=" * 62)
        print(f"LAPORAN PREDIKSI: {home_team.upper()} vs {away_team.upper()}")
        print(f"Tanggal Analisis: {tanggal_input} (Basis: {len(history)} laga)")
        print("=" * 62)
        print(f"{'Statistik':<26} | {home_team:<14} | {away_team:<14}")
        print("-" * 62)
        print(f"{'Rata-rata Gol/Laga':<26} | {hs['avg_gf']:<14} | {aws['avg_gf']:<14}")
        print(f"{'Rata-rata Kebobolan':<26} | {hs['avg_ga']:<14} | {aws['avg_ga']:<14}")
        print(f"{'Gol 5 Laga Terakhir':<26} | {hs['form_gf']:<14} | {aws['form_gf']:<14}")
        print(f"{'Tembakan On-Target/Laga':<26} | {hs['sot']:<14} | {aws['sot']:<14}")
        print(f"{'Expected Goals (xG)':<26} | {hasil['xg_home']:<14} | {hasil['xg_away']:<14}")
        print("=" * 62)
        print("PROBABILITAS HASIL PERTANDINGAN:")
        print(f"  * {home_team} Menang : {hasil['prob_h']}%")
        print(f"  * Hasil Seri (Draw)  : {hasil['prob_d']}%")
        print(f"  * {away_team} Menang : {hasil['prob_a']}%")
        print("-" * 62)
        print(f"KESIMPULAN PREDIKSI : {hasil['result']}")
        print(f"SKOR PALING MUNGKIN : {home_team} {hasil['home_goals']} - {hasil['away_goals']} {away_team} (Peluang skor: {hasil['score_prob']}%)")
        print("=" * 62)
