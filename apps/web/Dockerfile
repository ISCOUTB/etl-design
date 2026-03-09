FROM node:lts AS workspace

WORKDIR /workspace

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml /workspace/

COPY /apps/web /workspace/apps/web

# DEPENDANDS (direct & indirect)
COPY /tools/eslint /workspace/tools/eslint
COPY /tools/tsconfig /workspace/tools/tsconfig

COPY .moon /workspace/.moon

FROM node:lts AS builder

ENV NODE_ENV="production"
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

RUN pnpm install -g @moonrepo/cli

WORKDIR /app

COPY --from=workspace /workspace /app/

RUN --mount=type=cache,target=/pnpm/store \
    pnpm fetch

RUN --mount=type=cache,target=/app/.pnpm \
    pnpm i --offline --frozen-lockfile


# BUILD TASK
RUN moon run web:nuxt -- build 

FROM gcr.io/distroless/nodejs22-debian13 AS runner

ENV NODE_ENV="production"

WORKDIR /app

COPY --from=builder /app/apps/web/.output /app/.output

EXPOSE 3000

CMD [ ".output/server/index.mjs" ]