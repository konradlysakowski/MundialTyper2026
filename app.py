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
        # Otwieramy formularz
        with st.form("formularz_typowania"):
            st.markdown("### ✍️ Wprowadź swoje typy")

            # Pole do wyboru gracza (Zmień imiona na swoich znajomych!)
            uzytkownik = st.selectbox("Kto typuje?", ["Wybierz gracza...", "Konrad", "Marcel"])

            # Słownik, w którym będziemy trzymać zebrane z formularza wyniki
            zebrane_typy = {}

            for mecz in mecze:
                gospodarz = mecz["homeTeam"]["name"] if mecz["homeTeam"]["name"] else "Nieznany"
                gosc = mecz["awayTeam"]["name"] if mecz["awayTeam"]["name"] else "Nieznany"
                flaga_gosp = pobierz_html_flagi(gospodarz)
                flaga_gosc = pobierz_html_flagi(gosc)
                status = mecz["status"]
                godzina_pl = konwertuj_na_czas_polski(mecz["utcDate"])

                st.markdown("---")

                # Jeśli mecz się jeszcze nie zaczął (status SCHEDULED lub TIMED) -> Dajemy pola do wpisywania
                if status in ["SCHEDULED", "TIMED"]:
                    st.markdown(f"### 🕒 {godzina_pl} | {flaga_gosp} **{gospodarz}** vs **{gosc}** {flaga_gosc}",
                                unsafe_allow_html=True)

                    # Dwie kolumny obok siebie na pola z wpisywaniem goli
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        typ_gosp = st.number_input(f"Gole: {gospodarz}", min_value=0, max_value=20, step=1,
                                                   key=f"gosp_{mecz['id']}")
                    with col2:
                        typ_gosc = st.number_input(f"Gole: {gosc}", min_value=0, max_value=20, step=1,
                                                   key=f"gosc_{mecz['id']}")

                    # Zapisujemy typy do naszego słownika w pamięci
                    zebrane_typy[mecz['id']] = {
                        "mecz_nazwa": f"{gospodarz} vs {gosc}",
                        "gosp": typ_gosp,
                        "gosc": typ_gosc
                    }

                # Jeśli mecz trwa (IN_PLAY, PAUSED) lub się skończył (FINISHED) -> Pokazujemy wynik i blokujemy typowanie
                else:
                    wynik_gosp = mecz["score"]["fullTime"]["home"]
                    wynik_gosc = mecz["score"]["fullTime"]["away"]
                    st.markdown(
                        f"### 🕒 {godzina_pl} | {flaga_gosp} **{gospodarz}** {wynik_gosp} : {wynik_gosc} **{gosc}** {flaga_gosc}",
                        unsafe_allow_html=True)
                    st.info(f"Mecz niedostępny do typowania. Status: {status}")

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

                # 2. Przygotowujemy nowe wiersze do dopisania i listę meczów, które właśnie typujemy
                nowe_wiersze = []
                nazwy_meczow = []
                for mecz_id, dane in zebrane_typy.items():
                    nowe_wiersze.append({
                        "Data": dzisiejsza_data,
                        "Uzytkownik": uzytkownik,
                        "Mecz": dane["mecz_nazwa"],
                        "Typ_Gospodarz": dane["gosp"],
                        "Typ_Gosc": dane["gosc"]
                    })
                    nazwy_meczow.append(dane["mecz_nazwa"])

                nowy_df = pd.DataFrame(nowe_wiersze)

                # 3. LOGIKA USUWANIA / NADPISYWANIA
                if not stare_dane.empty:
                    # Magia biblioteki Pandas: Zostawiamy w tabeli wszystkie wiersze OPRÓCZ tych,
                    # gdzie zgadza się obecny "Uzytkownik" i "Mecz" jest na liście nowo wytypowanych.
                    maska = ~((stare_dane["Uzytkownik"] == uzytkownik) & (stare_dane["Mecz"].isin(nazwy_meczow)))
                    stare_dane = stare_dane[maska]

                # 4. Łączymy "oczyszczone" stare dane z nowymi
                zaktualizowana_baza = pd.concat([stare_dane, nowy_df], ignore_index=True)

                # 5. Wysyłamy do Google
                conn.update(data=zaktualizowana_baza)
                st.success("✅ Typy zapisane! (Jeśli miałeś już tu typ, został pomyślnie zaktualizowany).")
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