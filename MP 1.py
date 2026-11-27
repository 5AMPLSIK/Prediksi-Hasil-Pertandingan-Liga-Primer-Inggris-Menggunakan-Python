import os
import csv
import math

folder_script = os.path.dirname(os.path.abspath(__file__))
path_csv = os.path.join(folder_script, "season-2425.csv")

data = []
with open(path_csv, mode="r", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        tanggal = row.get("Date", "").strip()
        home = row.get("HomeTeam", "").strip()
        away = row.get("AwayTeam", "").strip()
        ftr = row.get("FTR", "").strip()
        fthg_str = row.get("FTHG", "").strip()
        ftag_str = row.get("FTAG", "").strip()

        if len(tanggal) == 10 and tanggal[4] == "-" and tanggal[7] == "-":
            if home and away and ftr and fthg_str.isdigit() and ftag_str.isdigit():
                data.append({
                    "Date": tanggal,
                    "HomeTeam": home,
                    "AwayTeam": away,
                    "FTHG": int(fthg_str),
                    "FTAG": int(ftag_str),
                    "FTR": ftr,
                    "HST": int(row["HST"]) if row.get("HST", "").strip().isdigit() else 4,
                    "AST": int(row["AST"]) if row.get("AST", "").strip().isdigit() else 4
                })

data.sort(key=lambda x: x["Date"])
teams = sorted({m["HomeTeam"] for m in data} | {m["AwayTeam"] for m in data})
teams_map = {team.lower(): team for team in teams}

print("=" * 62)
print("   SISTEM ANALISIS & PREDIKSI PERTANDINGAN EPL 2024/2025")
print("        Metode: Weighted Form & Distribusi Poisson")
print("=" * 62)
print(f"Total Dataset: {len(data)} Pertandingan")

def statistik_tim(team, venue, history):
    all_matches = [m for m in history if m["HomeTeam"] == team or m["AwayTeam"] == team]
    if not all_matches:
        return None

    home = [m for m in history if m["HomeTeam"] == team]
    away = [m for m in history if m["AwayTeam"] == team]

    semua_gol_masuk = [m["FTHG"] for m in home] + [m["FTAG"] for m in away]
    semua_gol_kebobolan = [m["FTAG"] for m in home] + [m["FTHG"] for m in away]
    gol_masuk_all = sum(semua_gol_masuk) / len(semua_gol_masuk)
    gol_kebobolan_all = sum(semua_gol_kebobolan) / len(semua_gol_kebobolan)

    if venue == "home" and home:
        gol_for = sum(m["FTHG"] for m in home) / len(home)
        gol_against = sum(m["FTAG"] for m in home) / len(home)
        sot_for = sum(m["HST"] for m in home) / len(home)
    elif venue == "away" and away:
        gol_for = sum(m["FTAG"] for m in away) / len(away)
        gol_against = sum(m["FTHG"] for m in away) / len(away)
        sot_for = sum(m["AST"] for m in away) / len(away)
    else:
        gol_for, gol_against, sot_for = gol_masuk_all, gol_kebobolan_all, 4.0

    recent = all_matches[-5:]
    rec_gf = [r["FTHG"] if r["HomeTeam"] == team else r["FTAG"] for r in recent]
    rec_ga = [r["FTAG"] if r["HomeTeam"] == team else r["FTHG"] for r in recent]
    form_gf = sum(rec_gf) / len(rec_gf)
    form_ga = sum(rec_ga) / len(rec_ga)

    return {
        "attack": (0.65 * gol_for) + (0.35 * form_gf),
        "defense": (0.65 * gol_against) + (0.35 * form_ga),
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

    league_avg_home = (sum(m["FTHG"] for m in history) / len(history)) if history else 1.5
    league_avg_away = (sum(m["FTAG"] for m in history) / len(history)) if history else 1.2

    xg_home = min(max((home_stats["attack"] * away_stats["defense"]) / max(league_avg_home, 0.5), 0.2), 4.5)
    xg_away = min(max((away_stats["attack"] * home_stats["defense"]) / max(league_avg_away, 0.5), 0.2), 4.5)

    prob_home_win = prob_draw = prob_away_win = 0.0
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
        hasil, kode = f"Home Win ({home_team} Menang)", "H"
    elif prob_away_win > prob_home_win and prob_away_win >= prob_draw:
        hasil, kode = f"Away Win ({away_team} Menang)", "A"
    else:
        hasil, kode = "Draw (Seri)", "D"

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

total_prediksi = prediksi_benar = 0
for tanggal in sorted({m["Date"] for m in data}):
    history = [m for m in data if m["Date"] < tanggal]
    if len(history) < 30:
        continue
    for row in [m for m in data if m["Date"] == tanggal]:
        hasil_prediksi = prediksi(row["HomeTeam"], row["AwayTeam"], history)
        if hasil_prediksi is not None:
            total_prediksi += 1
            if hasil_prediksi["kode"] == row["FTR"]:
                prediksi_benar += 1

if total_prediksi > 0:
    print(f"Pertandingan Diuji : {total_prediksi} laga")
    print(f"Prediksi Tepat     : {prediksi_benar} laga")
    print(f"Akurasi Model      : {(prediksi_benar / total_prediksi) * 100:.2f}%")

print("\nDAFTAR TIM EPL:")
for i in range(0, len(teams), 2):
    kiri = f"{i+1:2d}. {teams[i]:<18}"
    kanan = f"{i+2:2d}. {teams[i+1]}" if i + 1 < len(teams) else ""
    print("  ", kiri, kanan)

while True:
    print("\n" + "=" * 62)
    print("MENU UTAMA")
    print("=" * 62)
    print("1. Mulai Prediksi Pertandingan")
    print("0. Keluar")
    pilihan = input("Pilih menu (0-1): ").strip()

    if pilihan == "1":
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
                hs, aws = hasil["home_stats"], hasil["away_stats"]
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
                print(f"{'Lambda / Expected Goals':<26} | {hasil['xg_home']:<14} | {hasil['xg_away']:<14}")
                print("=" * 62)
                print("PROBABILITAS HASIL PERTANDINGAN:")
                print(f"  * {home_team} Menang : {hasil['prob_h']}%")
                print(f"  * Hasil Seri (Draw)  : {hasil['prob_d']}%")
                print(f"  * {away_team} Menang : {hasil['prob_a']}%")
                print("-" * 62)
                print(f"KESIMPULAN PREDIKSI : {hasil['result']}")
                print(f"SKOR PALING MUNGKIN : {home_team} {hasil['home_goals']} - {hasil['away_goals']} {away_team} (Peluang skor: {hasil['score_prob']}%)")
                print("=" * 62)

                while True:
                    print("\nMENU DISTRIBUSI POISSON:")
                    print("1. Cek nilai Lambda")
                    print("2. Hitung peluang jumlah gol (k) tertentu (misal k=0)")
                    print("3. Tabel distribusi peluang (k=0 s.d. 5)")
                    print("0. Kembali ke Menu Utama")
                    menu = input("Pilih (0-3): ").strip()

                    if menu == "1":
                        print(f"\nLambda {home_team}: {hasil['xg_home']} | Lambda {away_team}: {hasil['xg_away']}")
                    elif menu == "2":
                        k_in = input("Masukkan nilai k (misal 0): ").strip()
                        if k_in.isdigit():
                            k = int(k_in)
                            ph = poisson_prob(hasil["xg_home"], k) * 100
                            pa = poisson_prob(hasil["xg_away"], k) * 100
                            print(f"\nPeluang k={k} gol -> {home_team}: {ph:.2f}% | {away_team}: {pa:.2f}%")
                        else:
                            print("[Error] Masukkan angka bulat.")
                    elif menu == "3":
                        print(f"\n{'k':<5} | {home_team:<15} | {away_team:<15}")
                        print("-" * 40)
                        for k in range(6):
                            ph = poisson_prob(hasil["xg_home"], k) * 100
                            pa = poisson_prob(hasil["xg_away"], k) * 100
                            print(f"{k:<5} | {ph:<14.2f}% | {pa:<14.2f}%")
                    elif menu == "0":
                        break
                    else:
                        print("[Error] Pilihan tidak valid.")

    elif pilihan == "0":
        print("Program selesai.")
        break
    else:
        print("[Error] Pilihan tidak valid.")