# Build the admin web portal, then serve it with nginx (which also proxies the API).
FROM node:20-alpine AS build
WORKDIR /web
COPY web_portal/package.json web_portal/package-lock.json ./
RUN npm ci
COPY web_portal/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 80
