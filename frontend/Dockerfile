# frontend/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .

# ★ 每次构建都传入唯一 BUILD_ID，强制以下步骤重跑
ARG BUILD_ID=local
RUN echo "Building with BUILD_ID=$BUILD_ID" && npm run build

FROM nginx:1.27-alpine
ARG BUILD_ID=local
# ★ 用 BUILD_ID 让 COPY --from 不被缓存
RUN echo "Deploy BUILD_ID=$BUILD_ID"
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf