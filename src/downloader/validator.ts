const YOUTUBE_URL_PATTERNS = [
  // youtube.com/shorts/VIDEO_ID
  /(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})/,
  // youtube.com/watch?v=VIDEO_ID
  /(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})/,
  // youtu.be/VIDEO_ID
  /(?:https?:\/\/)?youtu\.be\/([a-zA-Z0-9_-]{11})/,
  // youtube.com/embed/VIDEO_ID
  /(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,
  // youtube.com/v/VIDEO_ID
  /(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([a-zA-Z0-9_-]{11})/,
];

export interface ValidationResult {
  valid: boolean;
  videoId?: string;
  url?: string;
  error?: string;
}

export function validateYouTubeUrl(text: string): ValidationResult {
  const trimmed = text.trim();

  for (const pattern of YOUTUBE_URL_PATTERNS) {
    const match = trimmed.match(pattern);
    if (match) {
      const videoId = match[1];
      const normalizedUrl = `https://www.youtube.com/watch?v=${videoId}`;
      return { valid: true, videoId, url: normalizedUrl };
    }
  }

  return {
    valid: false,
    error:
      "Invalid URL. Please send a valid YouTube or YouTube Shorts link.\n\nExamples:\n- https://youtube.com/shorts/ABC123\n- https://youtube.com/watch?v=ABC123\n- https://youtu.be/ABC123",
  };
}

export function extractYouTubeUrls(text: string): string[] {
  const urls: string[] = [];
  const urlRegex = /https?:\/\/[^\s]+/g;
  let match;

  while ((match = urlRegex.exec(text)) !== null) {
    const result = validateYouTubeUrl(match[0]);
    if (result.valid && result.url) {
      urls.push(result.url);
    }
  }

  return urls;
}
