# Usiamo NGINX come server web super leggero
FROM nginx:alpine

# Rimuoviamo la pagina di benvenuto di default di NGINX
RUN rm -rf /usr/share/nginx/html/*

# Copiamo i file web generati da Kotlin dentro la cartella pubblica di NGINX.
# ATTENZIONE: Controlla che questo percorso corrisponda esattamente a dove Gradle 
# ha generato i tuoi file nel Passaggio 1!
COPY build/dist/wasmJs/productionExecutable /usr/share/nginx/html

# (Opzionale ma consigliato) Copiamo un file di configurazione NGINX se usi il routing
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Esponiamo la porta 80 (quella standard per il web HTTP)
EXPOSE 80

# Avviamo NGINX
CMD ["nginx", "-g", "daemon off;"]