

# Move the cache paths from /var/nginx/cache to /tmp
client_body_temp_path /tmp/client_temp;
proxy_temp_path /tmp/proxy_temp 1 2;
fastcgi_temp_path /tmp/fastcgi_temp 1 2;
uwsgi_temp_path /tmp//uwsgi_temp 1 2;
scgi_temp_path /tmp/scgi_temp 1 2;


upstream portal {
  ip_hash;
  server app:8080;
}

# portal
server {
    # The max file size is 2GB + a little extra for overhead
    # The django ap will return an error on 2048
    client_max_body_size 2050M;

    location / {
        proxy_pass http://portal/;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;


        # Add and root location declarations
        {{- range .Values.web.locations.root }}
        # {{ .comment }}
        {{ .name }} {{ .value }};
        {{- end -}}

    }

    error_page 501 502 503 404 302 /error503.html;
    location = /error503.html {
        root   /usr/local/nginx/html;
    }

    # Protected path for data downloads
    #   This requires the data to be mounted
    #   read-only at /data
    location /data {
       internal;
       alias /data;
    }

    {{- if .Values.web.realIp.enabled }}
    # obtain client IP from proxy headers
    real_ip_header    X-Forwarded-For;

    {{- range .Values.web.realIp.fromIps }}
    set_real_ip_from {{ . }};
    {{- end }}
    {{- end -}}{{- /* end web.realIp.enabled  */}}

    listen 8000;
    server_name {{ tpl .Values.web.serverName . }};

}