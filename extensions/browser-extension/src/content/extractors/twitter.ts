/**
 * Twitter/X Content Extractor
 */

export class TwitterExtractor {
  extract(): { content: string; metadata: Record<string, any> } {
    const tweet = document.querySelector('[data-testid="tweetText"]');
    const author = document.querySelector('[data-testid="User-Name"]');
    const timestamp = document.querySelector('time');

    return {
      content: tweet?.textContent || '',
      metadata: {
        author: author?.textContent || null,
        timestamp: timestamp?.getAttribute('datetime') || null,
      },
    };
  }
}
