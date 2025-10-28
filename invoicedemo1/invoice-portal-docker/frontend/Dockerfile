FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY login.html /usr/share/nginx/html/login.html
COPY upload.html /usr/share/nginx/html/upload.html
COPY common.js /usr/share/nginx/html/common.js
RUN ln -sf /usr/share/nginx/html/login.html /usr/share/nginx/html/index.html