import pandas as pd
import math

data = pd.read_csv("season-2425.csv")

data["Date"] = pd.to_datetime(
    data["Date"], errors="coerce"
)

data = data.dropna(
    subset=["Date", "HomeTeam", "AwayTeam",
            "FTHG", "FTAG", "FTR"]
)

data = data.sort_values("Date").reset_index(drop=True)

print("=" * 55)
print(" PROGRAM PREDIKSI HASIL PERTANDINGAN EPL ")
print("             MUSIM 2024/2025")
print("=" * 55)

print("\nJumlah pertandingan:", len(data))


teams = sorted(set(data["HomeTeam"]) |
               set(data["AwayTeam"]))

print("\nDAFTAR TIM EPL:")

for i, team in enumerate(teams, start=1):
    print(i, ".", team)


def statistik_tim(team, venue, history):

    home = history[history["HomeTeam"] == team]
    away = history[history["AwayTeam"] == team]

    gol_masuk = pd.concat([
        home["FTHG"],
        away["FTAG"]
    ])

    gol_kebobolan = pd.concat([
        home["FTAG"],
        away["FTHG"]
    ])

    if venue == "home":
        gol_for = home["FTHG"]
        gol_against = home["FTAG"]
    else:
        gol_for = away["FTAG"]
        gol_against = away["FTHG"]


    if len(gol_for) == 0:
        gol_for = gol_masuk

    if len(gol_against) == 0:
        gol_against = gol_kebobolan

    if len(gol_masuk) == 0:
        return None

    return {
        "gol_masuk": gol_for.mean(),
        "gol_kebobolan": gol_against.mean()
    }


def prediksi(home_team, away_team, history):

    if home_team == away_team:
        return None

    home_stats = statistik_tim(
        home_team, "home", history
    )

    away_stats = statistik_tim(
        away_team, "away", history
    )

    if home_stats is None or away_stats is None:
        return None


    prediksi_gol_home = (
        home_stats["gol_masuk"] +
        away_stats["gol_kebobolan"]
    ) / 2

    prediksi_gol_away = (
        away_stats["gol_masuk"] +
        home_stats["gol_kebobolan"]
    ) / 2


    gol_home = math.floor(prediksi_gol_home + 0.5)
    gol_away = math.floor(prediksi_gol_away + 0.5)

    if gol_home > gol_away:
        hasil = "Home Win (Menang Kandang)"
    elif gol_home < gol_away:
        hasil = "Away Win (Menang Tandang)"
    else:
        hasil = "Draw (Seri)"
    return {
        "home_goals": gol_home,
        "away_goals": gol_away,
        "result": hasil
    }


print("\n" + "=" * 55)
print("PENGUJIAN PREDIKSI")
print("=" * 55)

total_prediksi = 0
prediksi_benar = 0

for tanggal, pertandingan in data.groupby("Date"):

    history = data[data["Date"] < tanggal]

    for _, row in pertandingan.iterrows():

        hasil_prediksi = prediksi(
            row["HomeTeam"],
            row["AwayTeam"],
            history
        )

        if hasil_prediksi is None:
            continue

        total_prediksi += 1

        hasil_asli = row["FTR"]

        if hasil_prediksi["result"].startswith("Home"):
            kode_prediksi = "H"
        elif hasil_prediksi["result"].startswith("Away"):
            kode_prediksi = "A"
        else:
            kode_prediksi = "D"
        if kode_prediksi == hasil_asli:
            prediksi_benar += 1


if total_prediksi > 0:

    akurasi = (
        prediksi_benar / total_prediksi
    ) * 100

    print("Total prediksi:", total_prediksi)
    print("Prediksi benar:", prediksi_benar)
    print("Prediksi salah:",
          total_prediksi - prediksi_benar)

    print("Akurasi: {:.2f}%".format(akurasi))

print("\n" + "=" * 55)
print("PREDIKSI PERTANDINGAN BARU")
print("=" * 55)

print("\nMasukkan nama tim sesuai daftar dataset.")

home_team = input("Tim tuan rumah: ").strip()
away_team = input("Tim tim tamu: ").strip()

tanggal_input = input(
    "Tanggal prediksi (YYYY-MM-DD): "
).strip()

tanggal_prediksi = pd.to_datetime(
    tanggal_input, errors="coerce"
)

if pd.isna(tanggal_prediksi):
    print("Format tanggal tidak valid.")
elif home_team not in teams or away_team not in teams:
    print("Nama tim tidak ditemukan.")
elif home_team == away_team:
    print("Tim tuan rumah dan tamu tidak boleh sama.")

else:
    history = data[
        data["Date"] < tanggal_prediksi
    ]

    hasil = prediksi(
        home_team,
        away_team,
        history
    )

    if hasil is None:
        print("\nData historis belum mencukupi.")
    else:
        print("\n" + "=" * 55)
        print("HASIL PREDIKSI PERTANDINGAN")
        print("=" * 55)
        print("Tanggal:", tanggal_prediksi.date())
        print("Tuan Rumah:", home_team)
        print("Tim Tamu:", away_team)
        print("\nPrediksi Skor:")
        print(
            home_team, hasil["home_goals"],
            "-", hasil["away_goals"], away_team
        )
        print("\nPrediksi Hasil:")
        print(hasil["result"])
        print("\nCatatan: Hasil merupakan estimasi")
        print("berdasarkan data historis, bukan")
        print("kepastian hasil pertandingan.")

print("\nProgram selesai.")