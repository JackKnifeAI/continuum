/**
 * YouTube Content Extractor
 */

export class YouTubeExtractor {
  extract(): { content: string; metadata: Record<string, any> } {
    const title = document.querySelector('h1.ytd-watch-metadata')?.textContent || '';
    const description = document.querySelector('#description')?.textContent || '';
    const videoId = new URLSearchParams(window.location.search).get('v');

    return {
      content: `${title}\n\n${description}`,
      metadata: {
        videoId,
        type: 'video',
      },
    };
  }
}
