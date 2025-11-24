# Define args to use throughout the file
ARG NODE_VERSION=20.18-alpine
ARG PORT=3000

# Define the base image to use for the build
FROM node:${NODE_VERSION} AS base
WORKDIR /src

# Build stage
FROM base AS build

# Set build-time environment variables
ENV NODE_ENV=production

# First, copy over the package.json files and run npm install
COPY --link package.json package-lock.json .
RUN npm ci

# Then we copy the rest of the application and run the build command
COPY --link . .
RUN npm run build

# Delete unused packages to reduce image size
RUN npm prune --omit=dev

# Finally, using the base image, copy the build output
FROM base

# Set runtime environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0

COPY --from=build /src/.output /src/.output

# And expose the port
EXPOSE 3000

# And run the server!
CMD ["node", ".output/server/index.mjs"]
