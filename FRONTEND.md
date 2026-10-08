# Frontend della biblioteca: le opzioni (da decidere insieme)

> Questo file non è una guida da seguire: è il materiale per **scegliere**. Quando hai finito la Fase 13
> del [README](README.md) (o anche prima, se sei curioso), leggilo e scrivimi cosa ti attira:
> scriviamo insieme le fasi del frontend scelto, con lo stesso metodo (checkpoint, domande, verifica nei container).

Versioni attuali (npm, ottobre 2026): htmx 2.0.11 (la 4.0 è sul tag `next`), Alpine.js 3.17,
React 19.3, Vue 3.5 (3.6 in beta), Vite 8.3.

---

## Chi usa il frontend di una grande biblioteca

| Utente | Cosa fa | Cosa conta |
|---|---|---|
| **Lettore** (pubblico) | cerca nel catalogo, vede disponibilità, prenota, rinnova | velocità, **SEO** (le schede libro devono essere trovate da Google), accessibilità, mobile |
| **Bibliotecario** (banco) | presta e restituisce con il lettore di codici a barre, cerca lettori | rapidità di inserimento, tastiera, nessun ricaricamento di pagina |
| **Staff** (backoffice) | catalogazione, sedi, statistiche | c'è già l'**admin di Django** (Fase 5) |

Sono esigenze diverse: non è detto che la risposta sia una sola tecnologia.

---

## Opzione A: template Django + HTMX (+ Alpine.js)

L'HTML resta generato da Django (quello che hai già fatto nelle Fasi 7-9); **HTMX** aggiunge interattività
con attributi: `hx-get="/?q=..." hx-target="#risultati"` fa una richiesta AJAX e sostituisce solo un pezzo
di pagina con l'HTML restituito dal server. Alpine.js per i piccoli comportamenti lato client (menu,
dialog). Django 6.0 ha introdotto i **template partials** (`{% partialdef %}`), pensati proprio per
restituire un frammento dello stesso template.

- ✅ Un solo linguaggio e un solo progetto; niente API da mantenere in parallelo né stato duplicato nel client.
- ✅ SEO e accessibilità gratis (è HTML vero); ottimo per il catalogo pubblico.
- ✅ Approfondisci Django (template, form, partials) invece di imparare un secondo ecosistema.
- ⚠️ Interfacce molto ricche (drag & drop, editor complessi, offline) diventano scomode.
- 💼 Molto diffuso nei team Django per gestionali e siti di contenuto; meno richiesto nelle offerte "frontend".

Esempio di cosa costruiremmo: ricerca *mentre scrivi* nel catalogo, paginazione senza ricaricare, banco
prestiti in cui il codice a barre letto aggiorna subito la scheda del lettore e la lista dei suoi prestiti.

## Opzione B: SPA React (Vite) sull'API DRF

Il frontend è un'applicazione separata in `frontend/` che parla solo con `/api/` (Fase 11), come la Fase 8
di `symfony_learn`.

- ✅ Riusi quello che hai già visto con Symfony; React è la competenza frontend più richiesta.
- ✅ Ideale per il **banco prestiti**: interfaccia reattiva, stato locale, scorciatoie da tastiera.
- ⚠️ Due progetti, due build, CORS o proxy, autenticazione via token o sessione + CSRF.
- ⚠️ SEO del catalogo pubblico debole senza server-side rendering (servirebbe Next.js o React Router con SSR:
  un altro livello di complessità).

## Opzione C: SPA Vue 3 (Vite) sull'API DRF

Come la B, con Vue (in `COURSES/vue.js` hai già del materiale).

- ✅ Curva più dolce di React, single file component, ottimo per gestionali.
- ✅ Molto usato in Italia ed Europa nei gestionali; Nuxt per l'eventuale SSR.
- ⚠️ Stessi costi architetturali della B.

## Opzione D: ibrida (la scelta "da progetto reale")

- **Catalogo pubblico** con template Django + HTMX (SEO, velocità, poco JavaScript).
- **Banco prestiti** come piccola SPA (React o Vue) montata in una pagina Django, che usa l'API.
- **Backoffice** con l'admin di Django.

- ✅ Ogni parte usa lo strumento adatto; è come sono fatti molti sistemi reali.
- ⚠️ Più tecnologie da imparare insieme: la più lunga delle quattro.

---

## Il mio consiglio

Partire dall'**Opzione A (HTMX)**: è il naturale proseguimento del backend che hai costruito, ti fa
imparare la parte di Django che un colloquio Django chiede (template, form, partials, CSRF con AJAX), e in
pochi giorni dà un catalogo pubblico veloce e indicizzabile. Se poi vuoi la parte React/Vue, il banco
prestiti è il candidato perfetto per evolvere verso l'**Opzione D** senza buttare nulla.

Se invece il tuo obiettivo è un ruolo **full-stack con React** (o Vue), conviene la B (o la C) da subito.

## Domande per decidere

1. Il tuo obiettivo è un ruolo **backend Python/Django** o **full-stack**?
2. Vuoi approfondire **React** (già visto con Symfony) o provare **Vue**?
3. Quanto tempo vuoi dedicare al frontend: pochi giorni o un percorso completo?
4. Ti interessa lo stile: CSS semplice, **Bootstrap** o **Tailwind**?
