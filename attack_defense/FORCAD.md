# ForcAD in Girello

ForcAD è il motore utilizzato per la modalità Attack & Defense di Girello.

La directory `forcad/` contiene i sorgenti importati dalla repository
https://github.com/pomo-mondreganto/ForcAD al commit:

`6ce3407be569b7f69f879501c5e2ca79231c1ff9`

Questa è la versione utilizzata nella valutazione iniziale del motore.
La licenza originale è conservata in `forcad/LICENSE`.

I sorgenti sono versionati direttamente nella repository Girello.
Gli adattamenti locali vengono quindi conservati nella stessa cronologia
del progetto.

I checker specifici dei servizi Girello si trovano nella directory
`checkers/`.

## Adattamenti per il laboratorio offline

Il frontend utilizza le risorse di Font Awesome distribuite localmente.
Sono stati rimossi i riferimenti a Google Fonts e al foglio di stile
remoto di Font Awesome, permettendo l'utilizzo dell'interfaccia senza
accesso a Internet.

È inoltre applicata una correzione alla gestione della cache delle flag.

L'adattamento del frontend riguarda la versione compilata in
`forcad/front/dist/`, utilizzata dal container Nginx.
