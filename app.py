import streamlit as st
import requests
from datetime import datetime, timedelta, date
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. KONFIGURACJA APLIKACJI ---
st.set_page_config(page_title="Mundial Typer 2026", page_icon="🏆", layout="centered")

# SŁOWNIK FLAG (Dodawaj tu kolejne kraje!)
# KODY FLAG ISO (Do pobierania obrazków)
KODY_FLAG = {
    "Czechia": "cz",
    "Mexico": "mx",
    "South Africa": "za",
    "South Korea": "kr",
    "Switzerland": "ch",
    "Bosnia-Herzegovina": "ba",
    "Canada": "ca",
    "Qatar": "qa",
    "Scotland": "gb-sct",
    "Brazil": "br",
    "Haiti": "ht",
    "Morocco": "ma",
    "Turkey": "tr",
    "Paraguay": "py",
    "United States": "us",
    "Australia": "au",
    "Germany": "de",
    "Ecuador": "ec",
    "Ivory Coast": "ci",
    "Curaçao": "cw",
    "Sweden": "se",
    "Netherlands": "nl",
    "Tunisia": "tn",
    "Japan": "jp",
    "Belgium": "be",
    "Egypt": "eg",
    "Iran": "ir",
    "New Zealand": "nz",
    "Spain": "es",
    "Uruguay": "uy",
    "Cape Verde Islands": "cv",
    "Saudi Arabia": "sa",
    "France": "fr",
    "Norway": "no",
    "Iraq": "iq",
    "Senegal": "sn",
    "Austria": "at",
    "Argentina": "ar",
    "Algeria": "dz",
    "Jordan": "jo",
    "Portugal": "pt",
    "Colombia": "co",
    "Congo DR": "cd",
    "Uzbekistan": "uz",
    "Croatia": "hr",
    "England": "gb-eng",
    "Ghana": "gh",
    "Panama": "pa"
}

def pobierz_html_flagi(nazwa_kraju):
    """Zwraca gotowy kod HTML z obrazkiem flagi z serwera FlagCDN"""
    kod = KODY_FLAG.get(nazwa_kraju)
    if kod:
        return f'<img src="https://flagcdn.com/24x18/{kod}.png" width="30" style="vertical-align: middle; margin: 0 8px;">'
    return "" # Jeśli nie znamy kraju, nie pokazujemy obrazka

# --- 2. POBIERANIE KLUCZA Z SEJFU ---
API_KEY = st.secrets["football_data"]["key"]

# Łączymy się z Google Sheets używając kluczy z secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. FUNKCJA POBIERAJĄCA MECZE ---
@st.cache_data(ttl=3600)
def pobierz_mecze(data_od, data_do):
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    headers = {"X-Auth-Token": API_KEY}
    # Wysyłamy do API zakres dat zamiast jednego dnia
    querystring = {"dateFrom": data_od, "dateTo": data_do}

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Błąd serwera API. Kod: {response.status_code}")
        return None


# --- 4. FUNKCJE POMOCNICZE (CZAS I FLAGI) ---
def konwertuj_na_czas_polski(data_utc_string):
    """Zmienia np. '2026-06-11T19:00:00Z' na polską godzinę np. '21:00'"""
    # 1. Tłumaczymy tekst z API na obiekt daty w Pythonie
    czas_utc = datetime.strptime(data_utc_string, "%Y-%m-%dT%H:%M:%SZ")
    # 2. Dodajemy 2 godziny (Czas letni w Polsce)
    czas_polski = czas_utc + timedelta(hours=2)
    # 3. Zwracamy samą godzinę w formacie HH:MM
    return czas_polski.strftime("%d.%m, %H:%M")

# --- 5. INTERFEJS UŻYTKOWNIKA ---
st.title("🏆 Mundial Typer 2026")

dzisiejsza_data = date.today()
jutrzejsza_data = dzisiejsza_data + timedelta(days=1)

str_dzisiaj = str(dzisiejsza_data)
str_jutro = str(jutrzejsza_data)

st.subheader(f"📅 Mecze (Dziś i Jutro): {dzisiejsza_data.strftime('%d.%m')} - {jutrzejsza_data.strftime('%d.%m')}")

dane_api = pobierz_mecze(str_dzisiaj, str_jutro)

# --- 6. PANEL TYPERA I WYŚWIETLANIE WYNIKÓW ---
if dane_api and "matches" in dane_api:
    mecze = dane_api["matches"]

    if len(mecze) == 0:
        st.info("Brak zaplanowanych meczów Mistrzostw Świata na ten dzień.")
    else:
        st.markdown("### ✍️ Panel Typera")

        # 1. WYCIĄGAMY WYBÓR GRACZA NAD FORMULARZ
        uzytkownik = st.selectbox("Kto typuje?", ["Wybierz gracza...", "Konrad", "Marcel", "Natalka"])

        # 2. POBIERAMY DOTYCHCZASOWE TYPY GRACZA Z BAZY
        moje_typy = {}
        moj_typ_zwyciezca = ""
        moj_typ_strzelec = ""

        if uzytkownik != "Wybierz gracza...":
            with st.spinner("Sprawdzam Twoje zapisane typy..."):
                try:
                    # fillna("") zapobiega błędom "NaN" jeśli pole jest puste
                    baza_obecna = conn.read(ttl=0).fillna("")
                    if not baza_obecna.empty:
                        typy_gracza = baza_obecna[baza_obecna["Uzytkownik"] == uzytkownik]
                        for _, wiersz in typy_gracza.iterrows():
                            mecz_nazwa = wiersz["Mecz"]
                            if mecz_nazwa == "🏆 ZWYCIĘZCA MUNDIALU":
                                moj_typ_zwyciezca = str(wiersz["Typ_Opisowy"])
                            elif mecz_nazwa == "⚽ KRÓL STRZELCÓW":
                                moj_typ_strzelec = str(wiersz["Typ_Opisowy"])
                            else:
                                moje_typy[mecz_nazwa] = {
                                    "gosp": int(wiersz["Typ_Gospodarz"]),
                                    "gosc": int(wiersz["Typ_Gosc"])
                                }
                except Exception:
                    pass  # W razie chwilowego błędu bazy, po prostu załadujemy 0:0

        # 3. OTWIERAMY FORMULARZ
        with st.form("formularz_typowania"):
            # Słownik, w którym będziemy trzymać zebrane z formularza wyniki
            zebrane_typy = {}

            for mecz in mecze:
                gospodarz = mecz["homeTeam"]["name"] if mecz["homeTeam"]["name"] else "Nieznany"
                gosc = mecz["awayTeam"]["name"] if mecz["awayTeam"]["name"] else "Nieznany"
                flaga_gosp = pobierz_html_flagi(gospodarz)
                flaga_gosc = pobierz_html_flagi(gosc)
                status = mecz["status"]
                godzina_pl = konwertuj_na_czas_polski(mecz["utcDate"])
                nazwa_meczu = f"{gospodarz} vs {gosc}"

                st.markdown("---")

                # Jeśli mecz się jeszcze nie zaczął
                if status in ["SCHEDULED", "TIMED"]:
                    st.markdown(f"### 🕒 {godzina_pl} | {flaga_gosp} **{gospodarz}** vs **{gosc}** {flaga_gosc}",
                                unsafe_allow_html=True)

                    # Ustawiamy stare typy jako domyślne w polach (jeśli ich nie ma, zostaje 0)
                    stary_gosp = moje_typy.get(nazwa_meczu, {}).get("gosp", 0)
                    stary_gosc = moje_typy.get(nazwa_meczu, {}).get("gosc", 0)

                    if nazwa_meczu in moje_typy:
                        st.success(
                            f"🛡️ Masz już zapisany typ na ten mecz: **{stary_gosp} : {stary_gosc}**. Zmień liczby poniżej tylko, jeśli chcesz go nadpisać.")

                    # Dwie kolumny obok siebie na pola z wpisywaniem goli
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        typ_gosp = st.number_input(f"Gole: {gospodarz}", min_value=0, max_value=20, step=1,
                                                   value=stary_gosp, key=f"gosp_{mecz['id']}")
                    with col2:
                        typ_gosc = st.number_input(f"Gole: {gosc}", min_value=0, max_value=20, step=1, value=stary_gosc,
                                                   key=f"gosc_{mecz['id']}")

                    # Zapisujemy typy do naszego słownika w pamięci
                    zebrane_typy[mecz['id']] = {
                        "mecz_nazwa": nazwa_meczu,
                        "gosp": typ_gosp,
                        "gosc": typ_gosc
                    }

                # Jeśli mecz trwa lub się skończył
                else:
                    wynik_gosp = mecz["score"]["fullTime"]["home"]
                    wynik_gosc = mecz["score"]["fullTime"]["away"]
                    st.markdown(
                        f"### 🕒 {godzina_pl} | {flaga_gosp} **{gospodarz}** {wynik_gosp} : {wynik_gosc} **{gosc}** {flaga_gosc}",
                        unsafe_allow_html=True)
                    st.info(f"Mecz niedostępny do typowania. Status: {status}")

            # --- TYPY DŁUGOTERMINOWE ---
            st.markdown("---")
            st.markdown("### 🔮 Typy Długoterminowe")

            # Formularz sam zaczyta i wklei tu Twoje poprzednie słowa!
            typ_zwyciezca = st.text_input("Kto wygra cały Mundial?", value=moj_typ_zwyciezca)
            typ_strzelec = st.text_input("Kto zostanie królem strzelców?", value=moj_typ_strzelec)

            # Przycisk wysyłający cały formularz
            wyslano = st.form_submit_button("💾 Zapisz moje typy w bazie!")

# --- 7. LOGIKA ZAPISU DO ARKUSZA GOOGLE ---
if wyslano:
    if uzytkownik == "Wybierz gracza...":
        st.error("⚠️ Wybierz swoje imię z listy na samej górze zanim zapiszesz!")
    elif len(zebrane_typy) == 0:
        st.warning("Brak meczów do wytypowania.")
    else:
        with st.spinner("Łączenie z bazą Google... 🚀"):
            try:
                # 1. Odczytujemy bazę omijając cache
                stare_dane = conn.read(ttl=0)

                nowe_wiersze = []
                nazwy_meczow = []

                # 1. Zgrywamy typy standardowych meczów
                for mecz_id, dane in zebrane_typy.items():
                    nowe_wiersze.append({
                        "Data": str_dzisiaj,
                        "Uzytkownik": uzytkownik,
                        "Mecz": dane["mecz_nazwa"],
                        "Typ_Gospodarz": dane["gosp"],
                        "Typ_Gosc": dane["gosc"],
                        "Typ_Opisowy": ""  # Kolumna na tekst, pusta dla meczów
                    })
                    nazwy_meczow.append(dane["mecz_nazwa"])

                # 2. Zgrywamy typy długoterminowe (jeśli ktoś coś wpisał)
                if typ_zwyciezca.strip() != "":
                    nowe_wiersze.append({
                        "Data": str_dzisiaj, "Uzytkownik": uzytkownik,
                        "Mecz": "🏆 ZWYCIĘZCA MUNDIALU", "Typ_Gospodarz": -1, "Typ_Gosc": -1,
                        "Typ_Opisowy": typ_zwyciezca.strip()
                    })
                    nazwy_meczow.append("🏆 ZWYCIĘZCA MUNDIALU")

                if typ_strzelec.strip() != "":
                    nowe_wiersze.append({
                        "Data": str_dzisiaj, "Uzytkownik": uzytkownik,
                        "Mecz": "⚽ KRÓL STRZELCÓW", "Typ_Gospodarz": -1, "Typ_Gosc": -1,
                        "Typ_Opisowy": typ_strzelec.strip()
                    })
                    nazwy_meczow.append("⚽ KRÓL STRZELCÓW")

                # 3. Aktualizacja bazy
                nowy_df = pd.DataFrame(nowe_wiersze)

                if not stare_dane.empty:
                    maska = ~((stare_dane["Uzytkownik"] == uzytkownik) & (stare_dane["Mecz"].isin(nazwy_meczow)))
                    stare_dane = stare_dane[maska]

                zaktualizowana_baza = pd.concat([stare_dane, nowy_df], ignore_index=True)
                conn.update(data=zaktualizowana_baza)

                st.success("✅ Typy zapisane! (Zwykłe i długoterminowe zaktualizowane).")
            except Exception as e:
                st.error(f"Wystąpił błąd podczas zapisu: {e}")

# --- 8. RANKING GRACZY (TABELA WYNIKÓW) ---
st.markdown("---")
st.markdown("## 🏆 Tabela Wyników (Na żywo)")

with st.spinner("Przeliczam punkty..."):
    try:
        # Odczytujemy aktualną bazę typów
        baza_typow = conn.read(ttl=0)

        if not baza_typow.empty:
            punkty_graczy = {}

            # Przechodzimy przez każdy typ w Arkuszu Google
            for index, wiersz in baza_typow.iterrows():
                gracz = wiersz["Uzytkownik"]
                mecz_nazwa = wiersz["Mecz"]

                # Zabezpieczenie, by traktować wpisane typy jako liczby całkowite
                typ_gosp = int(wiersz["Typ_Gospodarz"])
                typ_gosc = int(wiersz["Typ_Gosc"])

                # Jeśli gracza nie ma jeszcze w słowniku, dodajemy go z 0 pkt
                if gracz not in punkty_graczy:
                    punkty_graczy[gracz] = 0

                # Szukamy tego konkretnego meczu w pobranych dzisiaj danych z API
                if dane_api and "matches" in dane_api:
                    for mecz in dane_api["matches"]:
                        gospodarz = mecz["homeTeam"]["name"] if mecz["homeTeam"]["name"] else "Nieznany"
                        gosc = mecz["awayTeam"]["name"] if mecz["awayTeam"]["name"] else "Nieznany"
                        mecz_api_nazwa = f"{gospodarz} vs {gosc}"

                        if mecz_nazwa == mecz_api_nazwa:
                            # Pobieramy prawdziwy wynik
                            wynik_gosp = mecz["score"]["fullTime"]["home"]
                            wynik_gosc = mecz["score"]["fullTime"]["away"]

                            # Jeśli mecz ma już wynik (czyli trwa lub się skończył)
                            if wynik_gosp is not None and wynik_gosc is not None:
                                # LOGIKA PUNKTACJI

                                # 1. Dokładny wynik (3 punkty)
                                if typ_gosp == wynik_gosp and typ_gosc == wynik_gosc:
                                    punkty_graczy[gracz] += 3

                                # 2. Poprawne rozstrzygnięcie (1 punkt)
                                else:
                                    roznica_typ = typ_gosp - typ_gosc
                                    roznica_wynik = wynik_gosp - wynik_gosc

                                    # Gospodarz wygrał w obu przypadkach (różnica na plus)
                                    if (roznica_typ > 0 and roznica_wynik > 0):
                                        punkty_graczy[gracz] += 1
                                    # Gość wygrał w obu przypadkach (różnica na minus)
                                    elif (roznica_typ < 0 and roznica_wynik < 0):
                                        punkty_graczy[gracz] += 1
                                    # Remis w obu przypadkach (różnica równa 0)
                                    elif (roznica_typ == 0 and roznica_wynik == 0):
                                        punkty_graczy[gracz] += 1

            # --- Tworzenie ładnej tabeli wyświetlającej ranking ---
            # Zmieniamy nasz słownik na tabelę Pandas
            ranking_df = pd.DataFrame(list(punkty_graczy.items()), columns=["Gracz", "Punkty"])

            # Sortujemy malejąco od najlepszego gracza
            ranking_df = ranking_df.sort_values(by="Punkty", ascending=False).reset_index(drop=True)

            # Ustawiamy numery miejsc od 1, 2, 3...
            ranking_df.index = ranking_df.index + 1

            # Wyświetlamy jako ładną, rozciągniętą tabelę
            st.table(ranking_df)

        else:
            st.info("Brak typów w bazie. Bądź pierwszym, który obstawi mecz!")

    except Exception as e:
        st.warning(f"Nie udało się załadować rankingu. Błąd: {e}")

# --- 9. TYPY DŁUGOTERMINOWE (PODGLĄD) ---
st.markdown("---")
st.markdown("## 🔮 Kto w kogo wierzy? (Typy Długoterminowe)")

with st.spinner("Ładuję długoterminowe typy..."):
    try:
        # Odczytujemy najnowszą bazę
        baza_dlugo = conn.read(ttl=0)

        # Sprawdzamy czy nowa kolumna z tekstem już istnieje w Google Sheets
        if "Typ_Opisowy" in baza_dlugo.columns:
            # Filtrujemy tylko nasze "specjalne" wiersze
            maska = baza_dlugo["Mecz"].isin(["🏆 ZWYCIĘZCA MUNDIALU", "⚽ KRÓL STRZELCÓW"])
            typy_dlugo = baza_dlugo[maska]

            if not typy_dlugo.empty:
                # Oczyszczamy stare, zdublowane typy
                typy_dlugo = typy_dlugo.drop_duplicates(subset=['Uzytkownik', 'Mecz'], keep='last')

                # Budujemy piękną, zgrabną tabelkę
                tabela_dlugo = typy_dlugo.pivot(index="Uzytkownik", columns="Mecz", values="Typ_Opisowy").reset_index()
                tabela_dlugo = tabela_dlugo.rename(columns={"Uzytkownik": "Gracz"}).fillna("-")

                st.table(tabela_dlugo)
            else:
                st.info("Nikt jeszcze nie podał typów długoterminowych. Bądź pierwszy!")
        else:
            st.info("Nikt jeszcze nie podał typów długoterminowych. Bądź pierwszy!")
    except Exception as e:
        st.warning(f"Nie można wyświetlić typów długoterminowych: {e}")