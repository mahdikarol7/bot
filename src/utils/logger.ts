import pino from "pino";
import { config } from "../config.js";

const redactPaths = ["BOT_TOKEN"];

export const logger = pino({
  level: config.logLevel,
  redact: {
    paths: redactPaths,
    censor: "***REDACTED***",
  },
  transport:
    process.env.NODE_ENV !== "production"
      ? { target: "pino-pretty", options: { colorize: true } }
      : undefined,
});
