import { Context } from "grammy";
import { queueDownload } from "../downloader/index.js";
import { extractYouTubeUrls } from "../downloader/validator.js";

export async function messageHandler(ctx: Context): Promise<void> {
  const text = ctx.message?.text;
  if (!text) return;

  if (text.startsWith("/")) return;

  const urls = extractYouTubeUrls(text);

  if (urls.length === 0) return;

  await queueDownload(ctx, urls[0]);

  if (urls.length > 1) {
    await ctx.reply(
      "Note: Only one video will be processed at a time. Send additional links after the current download completes."
    );
  }
}
