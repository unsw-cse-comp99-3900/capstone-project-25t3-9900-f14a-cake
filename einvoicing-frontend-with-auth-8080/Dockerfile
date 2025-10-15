FROM node:20-alpine AS build
WORKDIR /app
COPY package.json pnpm-lock.yaml* package-lock.json* yarn.lock* ./
RUN set -eux;   if [ -f pnpm-lock.yaml ]; then corepack enable && pnpm i --frozen-lockfile;   elif [ -f yarn.lock ]; then yarn install --frozen-lockfile;   else npm ci || npm i; fi
COPY . .
RUN set -eux;   if [ -f pnpm-lock.yaml ]; then pnpm build;   elif [ -f yarn.lock ]; then yarn build;   else npm run build; fi

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
