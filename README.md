# Octavam — octavam.com

Strona darmowej aplikacji do nauki gry na pianinie. Wersje polska (`/`) i angielska (`/en/`), napisane w HTML, CSS i JavaScript, bez zależności npm. Kod aplikacji i paczki macOS są w [lepoco/octavam](https://github.com/lepoco/octavam).

## Budowanie i podgląd

Wymagany Python 3.9 lub nowszy:

```sh
python3 scripts/build-site.py
python3 -m http.server 8080 --directory .build/site
```

Otwórz http://localhost:8080. Strona wymaga serwera w swoim korzeniu, ponieważ używa ścieżek `/assets/...`. Skrypt sprawdza wszystkie strony HTML, odnośniki wewnętrzne, zasoby, sitemap i dane JSON-LD. Wynik trafia do `.build/site`; dokumentacja i pliki repozytorium nie są publikowane.

## Publikacja w GitHub Pages

1. W repozytorium **lepoco/octavam-page**, w **Settings → Pages → Build and deployment → Source**, wybierz **GitHub Actions**.
2. Workflow `Website` sprawdza pull requesty, a po pushu na `main` buduje i publikuje stronę. Możesz go też uruchomić ręcznie.
3. Ustaw domenę **octavam.com** w ustawieniach Pages i włącz **Enforce HTTPS**, gdy certyfikat będzie dostępny. Plik `CNAME` znajduje się w katalogu głównym.
4. Jeżeli domena jest przypięta do Pages repozytorium aplikacji, odłącz ją tam przed przypisaniem do tego repozytorium. Wyłącz publikację Pages w `lepoco/octavam`, aby oba repozytoria nie próbowały obsługiwać tej samej domeny.

DNS dla GitHub Pages pozostaje taki sam: rekord `CNAME` dla `www` wskazuje na `lepoco.github.io`; domena główna używa rekordów A GitHub Pages. Migracja publikacji nie wymaga zmiany adresów GitHub Pages w DNS.

## Edycja

- `index.html`, `en/index.html` — treść PL i EN.
- `assets/style.css` — wspólne style responsywne.
- `assets/site.js` — demonstracje trzech widoków i trybu follow; strona nie łączy się z MIDI.
- `assets/score.svg`, `blocks.svg`, `keyboard.svg` — ilustracje sposobu nauki, nie zrzuty aplikacji.
- `assets/lang.js` — preferencja języka w localStorage; zachowuje kotwicę i parametry URL.
- `privacy.html`, `en/privacy.html` — polityka prywatności.

Strona zachowuje oznaczenie nadchodzącej wersji App Store. Przycisk macOS prowadzi do wydań w repozytorium aplikacji, a kompilacje testowe do jego GitHub Actions.
